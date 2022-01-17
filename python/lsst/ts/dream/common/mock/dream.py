from __future__ import annotations

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

__all__ = ["MockDream"]

import asyncio
import logging
import json
import typing

import jsonschema

from ..abstract_dream import AbstractDream
from ..schema_registry import registry
from lsst.ts import tcpip


class MockDream(AbstractDream, tcpip.OneClientServer):
    """Class that implements the communication interface of a DREAM server."""

    def __init__(self) -> None:
        self.log = logging.getLogger(type(self).__name__)
        self.read_loop_task: asyncio.Future = asyncio.Future()
        super().__init__(
            name="MockDream",
            host="0.0.0.0",
            port=5000,
            log=self.log,
            connect_callback=self.connect_callback,
        )

        # The keys in this dict are the same as in the command schema and the
        # presence thereof is validated with every incoming command message.
        self.dispatch_dict: typing.Dict[str, typing.Callable] = {
            "resume": self.resume,
            "openRoof": self.open_roof,
            "closeRoof": self.close_roof,
            "stop": self.stop,
            "readyForData": self.set_ready_for_data,
            "dataArchived": self.set_data_archived,
            "setWeatherInfo": self.set_weather_info,
        }

    def connect_callback(self, server: MockDream) -> None:
        """A client has connected or disconnected."""
        if self.connected:
            self.log.info("Client connected.")
            self.read_loop_task = asyncio.create_task(self.read_loop())
        else:
            self.log.info("Client disconnected.")

    async def write(self, data: dict) -> None:
        """Write the data appended with a newline character.

        The data are encoded via JSON and then passed on to the StreamWriter
        associated with the socket.

        Parameters
        ----------
        data : `dict`
            The data to write.
        """
        self.log.debug(f"Writing data {data}")
        st = json.dumps({**data})
        self.log.debug(st)
        if self.connected:
            self.writer.write(st.encode() + tcpip.TERMINATOR)
            await self.writer.drain()
        self.log.debug("Done")

    async def read_loop(self) -> None:
        """Read commands and output replies."""
        try:
            self.log.info(f"The read_loop begins connected? {self.connected}")
            validator = jsonschema.Draft7Validator(schema=registry["command"])
            while self.connected:
                self.log.debug("Waiting for next incoming message.")
                line = await self.reader.readuntil(tcpip.TERMINATOR)
                if line:
                    line = line.decode().strip()
                    self.log.debug(f"Read command line: {line!r}")
                    items = json.loads(line)
                    # validate the incoming message
                    validator.validate(items)
                    key = items["key"]
                    kwargs = items["parameters"]
                    func = self.dispatch_dict[key]
                    await func(**kwargs)

        except Exception:
            self.log.exception("read_loop failed. Disconnecting.")
            await self.disconnect()

    async def disconnect(self) -> None:
        """Stop sending telemetry and close the client."""
        self.log.debug("Cancelling read_loop_task.")
        self.read_loop_task.cancel()
        self.log.debug("Closing client.")
        await self.close_client()

    async def resume(self) -> None:
        self.log.debug("resume")

    async def open_roof(self) -> None:
        self.log.debug("open_roof")

    async def close_roof(self) -> None:
        self.log.debug("close_roof")

    async def stop(self) -> None:
        self.log.debug("stop")

    async def set_ready_for_data(self, ready: bool) -> None:
        self.log.debug(f"set_ready_for_data with ready={ready!r}")

    async def set_data_archived(self) -> None:
        self.log.debug("set_data_archived")

    async def set_weather_info(
        self, weather_info: typing.Dict[str, typing.Union[float, bool]]
    ) -> None:
        self.log.debug(f"set_weather_info with weather_info={weather_info!r}")

    async def status(self) -> None:
        self.log.debug("status")

    async def new_data_products(self) -> None:
        self.log.debug("new_data_products")
