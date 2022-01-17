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

import asyncio
import json
import logging
import unittest

import typing

from lsst.ts.dream import common
from lsst.ts import tcpip, utils

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)

# Standard timeout in seconds.
TIMEOUT = 5


class MockDreamTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.log = logging.getLogger(type(self).__name__)
        self.log.debug("WOUTERRRR creating mock dream")
        self.mock_dream = common.mock.MockDream()

        await self.mock_dream.start_task
        assert self.mock_dream.server.is_serving()
        self.reader, self.writer = await asyncio.open_connection(
            host=tcpip.LOCAL_HOST, port=self.mock_dream.port
        )
        assert self.mock_dream.connected

    async def asyncTearDown(self) -> None:
        self.log.info("===== Start of asyncTearDown =====")
        if self.mock_dream.connected:
            await self.mock_dream.disconnect()
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        await self.mock_dream.close()

    async def read(self) -> typing.Dict[str, typing.Any]:
        """Read a string from the reader and unmarshal it

        Returns
        -------
        data : `dict`
            A dictionary with objects representing the string read.
        """
        read_bytes = await asyncio.wait_for(
            self.reader.readuntil(tcpip.TERMINATOR), timeout=TIMEOUT
        )
        data = json.loads(read_bytes.decode())
        return data

    async def write(self, **data: typing.Any) -> None:
        """Write the data appended with a tcpip.TERMINATOR string.

        Parameters
        ----------
        data:
            The data to write.
        """
        st = json.dumps({**data})
        assert self.writer is not None
        self.writer.write(st.encode() + tcpip.TERMINATOR)
        await self.writer.drain()

    async def test_commands(self) -> None:
        for key in self.mock_dream.dispatch_dict:
            parameters: typing.Dict[str, typing.Any] = {}
            if key == "readyForData":
                parameters = {"ready": True}
            if key == "setWeatherInfo":
                parameters = {"weather_info": {}}
            await self.write(
                command_id=1,
                key=key,
                parameters=parameters,
                time_command_sent=utils.current_tai(),
            )
