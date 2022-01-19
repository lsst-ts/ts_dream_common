# This file is part of ts_dream_common.
#
# Developed for the Vera C. Rubin Observatory Telescope and Site Systems.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__all__ = ["MockDreamClient"]

import asyncio
import json
import typing

from ..index_generator import index_generator
from lsst.ts import tcpip, utils

# Time limit for connecting to the RPi (seconds)
CONNECT_TIMEOUT = 5

# Time limit for communicating with the DREAM server (seconds).
# This includes writing a command and reading the response and reading
# telemetry.
COMMUNICATE_TIMEOUT = 5


class MockDreamClient:
    """Class that implements the communication interface of a DREAM client
    instance."""

    def __init__(self) -> None:
        # TCP/IP stream reader and writer
        self.reader: typing.Optional[asyncio.StreamReader] = None
        self.writer: typing.Optional[asyncio.StreamWriter] = None

        # Lock for TCP/IP communication
        self.stream_lock = asyncio.Lock()

        # Index generator for command indices.
        self.index_generator = index_generator()

    @property
    def connected(self) -> bool:
        return not (
            self.reader is None
            or self.writer is None
            or self.reader.at_eof()
            or self.writer.is_closing()
        )

    async def connect(self) -> None:
        """Connect to the DREAM server.

        Raises
        ------
        RuntimeError
            If already connected.
        """
        if self.connected:
            raise RuntimeError("Already connected.")

        self.reader, self.writer = await asyncio.wait_for(
            asyncio.open_connection(host=tcpip.LOCAL_HOST, port=5000),
            timeout=CONNECT_TIMEOUT,
        )

    async def disconnect(self) -> None:
        """Disconnect from the DREAM server.

        Always safe to call, though it may raise asyncio.CancelledError
        if the writer is currently being closed.
        """
        if self.connected:
            await asyncio.wait_for(
                tcpip.close_stream_writer(self.writer), timeout=CONNECT_TIMEOUT
            )

    async def read(self) -> typing.Dict:
        """Read and unmarshal a json-encoded dict.

        This may be a command acknowedgement or telemetry data.

        Time out if reading takes longer than COMMUNICATE_TIMEOUT seconds.

        Returns
        -------
        data : `dict`
            The read data, after json-decoding it.
        """
        if not self.connected:
            raise RuntimeError("Not connected.")
        assert self.reader is not None  # make mypy happy

        read_bytes = await asyncio.wait_for(
            self.reader.readuntil(tcpip.TERMINATOR), timeout=COMMUNICATE_TIMEOUT
        )
        try:
            data = json.loads(read_bytes.decode())
        except json.decoder.JSONDecodeError as e:
            raise RuntimeError(f"Could not parse {read_bytes!r} as json.") from e
        if not isinstance(data, dict):
            raise RuntimeError(
                f"Could not parse {read_bytes!r} as a json-encoded dict."
            )
        return data

    async def run_command(self, command: str, **parameters: typing.Any) -> None:
        """Write a command. Time out if it takes too long.

        Parameters
        ----------
        command : `str`
            The command to write.
        **parameters : `dict`
            Command parameters, as name=dict. For example::

                configuration = {"devices": self.config.devices}

        Raises
        ------
        ConnectionError
            If not connected
        asyncio.TimeoutError
            If it takes more than COMMUNICATE_TIMEOUT seconds
            to acquire the lock or write the data.
        """
        json_str = json.dumps(
            {
                "command_id": next(self.index_generator),
                "key": command,
                "parameters": parameters,
                "time_command_sent": utils.current_tai(),
            }
        )
        await asyncio.wait_for(
            self._basic_run_command(json_str), timeout=COMMUNICATE_TIMEOUT
        )

    async def _basic_run_command(self, json_str: str) -> None:
        """Write a json-encoded command dict. Potentially wait forever.

        Parameters
        ----------
        json_str : `str`
            json-encoded dict to write. The dict should be of the form::

                {
                    "command_id": int,
                    "command": command_str,
                    "parameters": params_dict,
                    "time_command_sent": float
                }

        Raises
        ------
        RuntimeError
            If the command fails.
        ConnectionError
            If disconnected before command is acknowledged.
        """
        async with self.stream_lock:
            if not self.connected:
                raise ConnectionError("Not connected; cannot send the command.")
            assert self.writer is not None  # make mypy happy

            self.writer.write(json_str.encode() + tcpip.TERMINATOR)
            await self.writer.drain()
