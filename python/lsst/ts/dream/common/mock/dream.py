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

__all__ = ["MockDream", "ServerState", "ErrorCode", "RoofStatus", "Device"]

import asyncio
import enum
import logging
import json
import typing

import jsonschema

from ..abstract_dream import AbstractDream
from ..schema_registry import registry
from lsst.ts import tcpip

# Interval between sending the mock DREAM server status [s].
STATUS_INTERVAL = 5


class ServerState(enum.IntEnum):
    """The state the mock DREAM server can be in."""

    INITIALIZING = enum.auto()
    HIBERNATING = enum.auto()
    COOLING_DOWN = enum.auto()
    CALIBRATING = enum.auto()
    READY = enum.auto()
    OPEN = enum.auto()
    OBSERVING = enum.auto()
    MAINTENANCE = enum.auto()
    SHUTTING_DOWN = enum.auto()


class ErrorCode(enum.IntEnum):
    """Error Code enum."""

    # TODO DM-33287: Add more ErrorCode values.
    OK = enum.auto()


class RoofStatus(enum.IntEnum):
    """Roof status enum."""

    CLOSED = enum.auto()
    OPEN = enum.auto()
    OPENING = enum.auto()
    CLOSING = enum.auto()


class Device(enum.IntEnum):
    """Device enum."""

    MASTER = enum.auto()
    NORTH = enum.auto()
    EAST = enum.auto()
    SOUTH = enum.auto()
    WEST = enum.auto()
    ZENITH = enum.auto()


class WeatherInfo:
    """Class that holds the weather info.

    Attributes
    ----------
        temperature : `float`
            The temperature [ºC].
        humidty : `float`
            The humidty [%].
        wind_speed : `float`
            The wind speed [m/s].
        wind_direction : `float`
            The wind direction [º azimuth].
        pressure : `float`
            The pressure [Pa].
        rain : `float`
            The rain [mm].
        cloudcover : `float`
            The cloudcover [%].
        safe_observing_conditions : `float`
            Safe to observe (True) or not (False).

    """

    def __init__(self) -> None:
        self.temperature = 0.0
        self.humidity = 0.0
        self.wind_speed = 0.0
        self.wind_direction = 0.0
        self.pressure = 0.0
        self.rain = 0.0
        self.cloudcover = 0.0
        self.safe_observing_conditions = False


class MasterServerStatus:
    """Class that holds the status of the master server.

    Attributes
    ----------
        device : `Device`
            The device.
        state : `ServerState`
            The state of the server.
        start_time : `float`
            The last start time UNIX time stamp [s].
        stop_time : `float`
            The last stop time UNIX time stamp [s].
        error_code : `ErrorCode`
            The error code.
        rain_sensor : `bool`
            A rain sensor is present (True) or not (False).
        roof_status : `RoofStatus`
            The status of the roof.

    """

    def __init__(self) -> None:
        self.device = Device.MASTER
        self.state = ServerState.INITIALIZING
        self.start_time = 0.0
        self.stop_time = 0.0
        self.error_code = ErrorCode.OK
        self.rain_sensor = True
        self.roof_status = RoofStatus.CLOSED

    def asdict(self) -> typing.Dict[str, typing.Any]:
        return {
            "device": self.device,
            "state": self.state,
            "start_time": self.start_time,
            "stop_time": self.stop_time,
            "error_code": self.error_code,
            "rain_sensor": self.rain_sensor,
            "roof_status": self.roof_status,
        }


class CameraServerStatus:
    """Class that holds the status of a camera server.

    Parameters
    ----------
    device : `Device`
        The device.

    Attributes
    ----------
        device : `Device`
            The device.
        state : `ServerState`
            The state of the server.
        error_code : `ErrorCode`
            The error code.
        altitude : `float`
            The altitude [º].
        azimuth : `float`
            The azimuth [º].
        last_exposure_time_stamp : `float`
            The last exposure time stamp [s].
        exposure_time : `float`
            The exposure time [s].

    """

    def __init__(self, device: Device) -> None:
        self.device = device
        self.state = ServerState.INITIALIZING
        self.error_code = ErrorCode.OK
        self.altitude = 0.0
        self.azimuth = 0.0
        self.last_exposure_time_stamp = 0.0
        self.exposure_time = 0.0

    def asdict(self) -> typing.Dict[str, typing.Any]:
        return {
            "device": self.device,
            "state": self.state,
            "error_code": self.error_code,
            "altitude": self.altitude,
            "azimuth": self.azimuth,
            "last_exposure_time_stamp": self.last_exposure_time_stamp,
            "exposure_time": self.exposure_time,
        }


class MockDream(AbstractDream, tcpip.OneClientServer):
    """Class that implements the communication interface of a DREAM server."""

    def __init__(self) -> None:
        self.log = logging.getLogger(type(self).__name__)

        # Read loop for receiving commands.
        self.read_loop_task: asyncio.Future = asyncio.Future()

        # Status loop for sending the status of the mock DREAM server to the
        # client.
        self.status_task: asyncio.Future = asyncio.Future()
        self.master_server_status = MasterServerStatus()

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

        self.client_ready_for_data = False

        # Hold the weather info.
        self.weather_info = WeatherInfo()

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
                    # TODO DM-33287: Needs better error handling.
                    validator.validate(items)
                    key = items["key"]
                    kwargs = items["parameters"]
                    func = self.dispatch_dict[key]
                    # TODO DM-33287: Needs sending acknowledgements.
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
        self.status_task = asyncio.create_task(self.status())

    async def open_roof(self) -> None:
        self.log.debug("open_roof")
        # This can be improved by implementing a delay during which the roof is
        # opening.
        if self.master_server_status.roof_status == RoofStatus.CLOSED:
            self.master_server_status.roof_status = RoofStatus.OPEN
        else:
            # TODO DM-33287: Needs better error handling.
            pass

    async def close_roof(self) -> None:
        self.log.debug("close_roof")
        # This can be improved by implementing a delay during which the roof is
        # closing.
        if self.master_server_status.roof_status == RoofStatus.OPEN:
            self.master_server_status.roof_status = RoofStatus.CLOSED
        else:
            # TODO DM-33287: Needs better error handling.
            pass

    async def stop(self) -> None:
        self.log.debug("stop")
        self.status_task.cancel()

    async def set_ready_for_data(self, ready: bool) -> None:
        self.log.debug(f"set_ready_for_data with ready={ready!r}")
        self.client_ready_for_data = ready

    async def set_data_archived(self) -> None:
        self.log.debug("set_data_archived")

    async def set_weather_info(
        self, weather_info: typing.Dict[str, typing.Union[float, bool]]
    ) -> None:
        self.log.debug(f"set_weather_info with weather_info={weather_info!r}")
        validator = jsonschema.Draft7Validator(schema=registry["weather_info"])
        # TODO DM-33287: Needs better error handling.
        validator.validate(weather_info)
        for key in weather_info:
            setattr(self.weather_info, key, weather_info[key])

    async def status(self) -> None:
        self.log.debug("status")
        try:
            while True:
                # TODO DM-33287: Make sure that the status gets updated when
                #  commands are sent and that it includes the camera server
                #  statuses.
                self.log.debug("Sending status.")
                await self.write(self.master_server_status.asdict())
                await asyncio.sleep(STATUS_INTERVAL)

        except Exception:
            self.log.exception("status loop failed.")

    async def new_data_products(self) -> None:
        self.log.debug("new_data_products")
