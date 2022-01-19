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
import logging
import random
import typing
import unittest

from lsst.ts.dream import common

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)

# Standard timeout in seconds.
TIMEOUT = 5

# Wait time for a write to get processed
WRITE_WAIT_TIME = 0.01


class MockDreamClientTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.log = logging.getLogger(type(self).__name__)
        self.mock_dream = common.mock.MockDream()
        self.mock_dream_client = common.mock.MockDreamClient()

        await self.mock_dream.start_task
        assert self.mock_dream.server.is_serving()

    async def asyncTearDown(self) -> None:
        if self.mock_dream_client.connected:
            await self.mock_dream_client.disconnect()
        await self.mock_dream.close()

    async def validate_connect(self) -> None:
        assert self.mock_dream_client.connected is False
        await self.mock_dream_client.connect()
        assert self.mock_dream_client.connected is True

    async def test_connect_client(self) -> None:
        await self.validate_connect()

    async def test_disconnect_client(self) -> None:
        await self.validate_connect()

        await self.mock_dream_client.disconnect()
        assert self.mock_dream_client.connected is False

    async def validate_roof_status(self, roof_status: common.mock.RoofStatus) -> None:
        # Give time to the mock DREAM server to process the command.
        await asyncio.sleep(WRITE_WAIT_TIME)
        assert self.mock_dream.master_server_status.roof_status == roof_status

    async def test_open_and_close_roof(self) -> None:
        await self.validate_roof_status(common.mock.RoofStatus.CLOSED)

        await self.validate_connect()

        await self.mock_dream_client.run_command(command="openRoof")
        await self.validate_roof_status(common.mock.RoofStatus.OPEN)

        await self.mock_dream_client.run_command(command="closeRoof")
        await self.validate_roof_status(common.mock.RoofStatus.CLOSED)

    async def validate_dream_status_task(self, done: bool) -> None:
        # Give time to the mock DREAM server to process the command.
        await asyncio.sleep(WRITE_WAIT_TIME)
        assert self.mock_dream.status_task.done() is done

    async def test_resume_and_stop(self) -> None:
        await self.validate_dream_status_task(done=False)

        await self.validate_connect()

        await self.mock_dream_client.run_command(command="resume")
        await self.validate_dream_status_task(done=False)

        data = await self.mock_dream_client.read()
        # TODO DM-33287: Validate that the status gets updated when commands
        #  are sent.
        assert data["device"] == common.mock.Device.MASTER
        assert data["state"] == common.mock.ServerState.INITIALIZING
        assert data["start_time"] == 0.0
        assert data["stop_time"] == 0.0
        assert data["error_code"] == common.mock.ErrorCode.OK
        assert data["rain_sensor"] is True
        assert data["roof_status"] == common.mock.RoofStatus.CLOSED

        await self.mock_dream_client.run_command(command="stop")
        await self.validate_dream_status_task(done=True)

    async def validate_ready(self, ready_for_data: bool, done: bool) -> None:
        # Give time to the mock DREAM server to process the command.
        await asyncio.sleep(WRITE_WAIT_TIME)
        assert self.mock_dream.client_ready_for_data is ready_for_data
        assert self.mock_dream.new_data_products_task.done() is done

    async def test_ready(self) -> None:
        await self.validate_ready(ready_for_data=False, done=False)

        await self.validate_connect()

        await self.mock_dream_client.run_command(command="readyForData", ready=True)
        await self.validate_ready(ready_for_data=True, done=False)

        data = await self.mock_dream_client.read()
        self.log.debug(data)
        metadata = data["metadata"]
        assert data["amount"] == len(metadata)
        for data in metadata:
            assert data["name"] is not None
            assert data["location"] is not None
            assert data["timestamp"] > 0

        await self.mock_dream_client.run_command(command="readyForData", ready=False)
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

        await self.validate_connect()

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
        await self.mock_dream_client.run_command(
            command="setWeatherInfo", weather_info=weather_info
        )
        # Give time to the mock DREAM server to process the command.
        await asyncio.sleep(WRITE_WAIT_TIME)
        self.validate_weather_info(expected_weather_info=weather_info)