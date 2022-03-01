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

__all__ = ["MasterServerStatus", "CameraServerStatus"]

import typing

from .enums import Device, ErrorCode, RoofStatus, ServerState


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

    def as_dict(self) -> typing.Dict[str, typing.Any]:
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
        state : `ServerState`
            The state of the server.
        error_code : `ErrorCode`
            The error code.
        altitude : `float`
            The altitude [deg].
        azimuth : `float`
            The azimuth [deg].
        last_exposure_time_stamp : `float`
            The last exposure timestamp [s].
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

    def as_dict(self) -> typing.Dict[str, typing.Any]:
        return {
            "device": self.device,
            "state": self.state,
            "error_code": self.error_code,
            "altitude": self.altitude,
            "azimuth": self.azimuth,
            "last_exposure_time_stamp": self.last_exposure_time_stamp,
            "exposure_time": self.exposure_time,
        }
