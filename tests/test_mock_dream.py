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
import random
import typing
import unittest

from lsst.ts.dream import common
from lsst.ts import tcpip, utils

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)

# Standard timeout in seconds.
TIMEOUT = 60


class MockDreamTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.log = logging.getLogger(type(self).__name__)
        self.mock_dream = common.mock.MockDream()
        self.index_generator = utils.index_generator()

        await self.mock_dream.start_task
        assert self.mock_dream.server.is_serving()
        self.reader, self.writer = await asyncio.open_connection(
            host=tcpip.LOCAL_HOST, port=self.mock_dream.port
        )
        await asyncio.sleep(0.1)
        assert self.mock_dream.connected

        self.expected_status = common.MasterServerStatus()
        self.expected_status.state = common.ServerState.HIBERNATING
        self.expected_status.roof_status = common.RoofStatus.CLOSED

    async def asyncTearDown(self) -> None:
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

    async def validate_command_response(
        self, command_id: int, command_response: common.CommandResponse
    ) -> None:
        data = await self.read()
        assert data["command_id"] == command_id
        assert data["command_response"] == command_response

    async def validate_server_status(self) -> None:
        data = await self.read()
        assert data["device"] == common.Device.MASTER
        assert data["state"] == self.expected_status.state
        assert data["start_time"] == 0.0
        assert data["stop_time"] == 0.0
        assert data["error_code"] == common.ErrorCode.OK
        assert data["rain_sensor"] is True
        assert data["roof_status"] == self.expected_status.roof_status

    async def test_invalid_json(self) -> None:
        # "parameters" is mandatory
        command_id = next(self.index_generator)
        await self.write(
            command_id=command_id,
            key="resume",
            time_command_sent=utils.current_tai(),
        )
        await self.validate_server_status()
        await self.validate_command_response(
            command_id=command_id, command_response=common.CommandResponse.INVALID_JSON
        )

        # The "openHatch" command doesn't exist.
        command_id = next(self.index_generator)
        await self.write(
            command_id=command_id,
            key="openHatch",
            parameters={},
            time_command_sent=utils.current_tai(),
        )
        await self.validate_command_response(
            command_id=command_id, command_response=common.CommandResponse.INVALID_JSON
        )

    async def test_open_and_close_roof(self) -> None:
        await self.validate_server_status()

        command_id = next(self.index_generator)
        await self.write(
            command_id=command_id,
            key="openRoof",
            parameters={},
            time_command_sent=utils.current_tai(),
        )
        await self.validate_command_response(
            command_id=command_id, command_response=common.CommandResponse.ACK
        )
        self.expected_status.state = common.ServerState.OPEN
        self.expected_status.roof_status = common.RoofStatus.OPEN
        await self.validate_server_status()
        await self.validate_command_response(
            command_id=command_id, command_response=common.CommandResponse.LAST
        )
        self.expected_status.state = common.ServerState.OBSERVING
        await self.validate_server_status()

        command_id = next(self.index_generator)
        await self.write(
            command_id=command_id,
            key="openRoof",
            parameters={},
            time_command_sent=utils.current_tai(),
        )
        await self.validate_command_response(
            command_id=command_id, command_response=common.CommandResponse.ACK
        )
        await self.validate_command_response(
            command_id=command_id,
            command_response=common.CommandResponse.COMMAND_FAILED,
        )
        await self.validate_server_status()

        command_id = next(self.index_generator)
        await self.write(
            command_id=command_id,
            key="closeRoof",
            parameters={},
            time_command_sent=utils.current_tai(),
        )
        await self.validate_command_response(
            command_id=command_id, command_response=common.CommandResponse.ACK
        )
        self.expected_status.state = common.ServerState.CLOSED
        self.expected_status.roof_status = common.RoofStatus.CLOSING
        await self.validate_server_status()
        await self.validate_command_response(
            command_id=command_id, command_response=common.CommandResponse.LAST
        )
        self.expected_status.roof_status = common.RoofStatus.CLOSED
        await self.validate_server_status()

        command_id = next(self.index_generator)
        await self.write(
            command_id=command_id,
            key="closeRoof",
            parameters={},
            time_command_sent=utils.current_tai(),
        )
        await self.validate_command_response(
            command_id=command_id, command_response=common.CommandResponse.ACK
        )
        await self.validate_command_response(
            command_id=command_id,
            command_response=common.CommandResponse.COMMAND_FAILED,
        )
        await self.validate_server_status()

    async def validate_dream_status_task(self, done: bool) -> None:
        assert self.mock_dream.status_task.done() is done

    async def test_resume_and_stop(self) -> None:
        await self.validate_dream_status_task(done=False)

        command_id = next(self.index_generator)
        await self.write(
            command_id=command_id,
            key="resume",
            parameters={},
            time_command_sent=utils.current_tai(),
        )
        self.expected_status.state = common.ServerState.HIBERNATING
        await self.validate_server_status()
        await self.validate_command_response(
            command_id=command_id, command_response=common.CommandResponse.ACK
        )
        await self.validate_command_response(
            command_id=command_id, command_response=common.CommandResponse.LAST
        )
        await self.validate_dream_status_task(done=False)

        self.expected_status.state = common.ServerState.READY
        await self.validate_server_status()

        command_id = next(self.index_generator)
        await self.write(
            command_id=command_id,
            key="stop",
            parameters={},
            time_command_sent=utils.current_tai(),
        )
        await self.validate_command_response(
            command_id=command_id, command_response=common.CommandResponse.ACK
        )
        await self.validate_command_response(
            command_id=command_id, command_response=common.CommandResponse.LAST
        )

    async def validate_ready(self, ready_for_data: bool, done: bool) -> None:
        assert self.mock_dream.client_ready_for_data is ready_for_data
        assert self.mock_dream.new_data_products_task.done() is done

    async def test_ready(self) -> None:
        await self.validate_ready(ready_for_data=False, done=False)

        command_id = next(self.index_generator)
        await self.write(
            command_id=command_id,
            key="readyForData",
            parameters={"ready": True},
            time_command_sent=utils.current_tai(),
        )
        await self.validate_server_status()
        await self.validate_command_response(
            command_id=command_id, command_response=common.CommandResponse.ACK
        )
        await self.validate_command_response(
            command_id=command_id, command_response=common.CommandResponse.LAST
        )
        await self.validate_ready(ready_for_data=True, done=False)

        data = await self.read()
        self.log.debug(data)
        metadata = data["metadata"]
        assert data["amount"] == len(metadata)
        for data in metadata:
            assert data["name"] is not None
            assert data["location"] is not None
            assert data["timestamp"] > 0

        command_id = next(self.index_generator)
        await self.write(
            command_id=command_id,
            key="readyForData",
            parameters={"ready": False},
            time_command_sent=utils.current_tai(),
        )
        await self.validate_command_response(
            command_id=command_id, command_response=common.CommandResponse.ACK
        )
        await self.validate_command_response(
            command_id=command_id, command_response=common.CommandResponse.LAST
        )
        await self.validate_ready(ready_for_data=False, done=True)

    def validate_weather_info(
        self, expected_weather_info: typing.Dict[str, typing.Union[float, bool]]
    ) -> None:
        for key in expected_weather_info:
            assert (
                getattr(self.mock_dream.weather_info, key) == expected_weather_info[key]
            )

    async def test_weather_info(self) -> None:
        # First validate the default values of the weather info data in the
        # mock DREAM server.
        weather_info = {
            "temperature": 0.0,
            "humidity": 0.0,
            "wind_speed": 0.0,
            "wind_direction": 0.0,
            "pressure": 0.0,
            "rain": 0.0,
            "cloudcover": 0.0,
            "safe_observing_conditions": False,
        }
        self.validate_weather_info(expected_weather_info=weather_info)

        # Now set new values and verify that the mock DREAM server has picked
        # them up.
        weather_info = {
            "temperature": random.uniform(-10, 30),
            "humidity": random.uniform(0, 100),
            "wind_speed": random.uniform(0, 100),
            "wind_direction": random.uniform(0, 360),
            "pressure": random.uniform(70000, 100000),
            "rain": random.uniform(0, 100),
            "cloudcover": random.uniform(0, 100),
            "safe_observing_conditions": True,
        }
        command_id = next(self.index_generator)
        await self.write(
            command_id=command_id,
            key="setWeatherInfo",
            parameters={"weather_info": weather_info},
            time_command_sent=utils.current_tai(),
        )
        await self.validate_server_status()
        await self.validate_command_response(
            command_id=command_id, command_response=common.CommandResponse.ACK
        )
        await self.validate_command_response(
            command_id=command_id, command_response=common.CommandResponse.LAST
        )
        self.validate_weather_info(expected_weather_info=weather_info)

        # Now set new, invalid, values and verify that the mock DREAM server
        # has rejected them.
        weather_info = {
            "temp": random.uniform(-10, 30),
            "hum": random.uniform(0, 100),
            "wind_speed": random.uniform(0, 100),
            "wind_dir": random.uniform(0, 360),
            "pressure": random.uniform(70000, 100000),
            "rain": random.uniform(0, 100),
            "cloudcover": random.uniform(0, 100),
            "safe_to_observe": True,
        }
        command_id = next(self.index_generator)
        await self.write(
            command_id=command_id,
            key="setWeatherInfo",
            parameters={"weather_info": weather_info},
            time_command_sent=utils.current_tai(),
        )
        await self.validate_command_response(
            command_id=command_id, command_response=common.CommandResponse.ACK
        )
        await self.validate_command_response(
            command_id=command_id,
            command_response=common.CommandResponse.COMMAND_FAILED,
        )
