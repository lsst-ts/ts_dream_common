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

__all__ = ["ServerState", "ErrorCode", "CommandResponse", "RoofStatus", "Device"]

import enum


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


class CommandResponse(enum.IntEnum):
    """Command Response enum."""

    ACK = enum.auto()
    LAST = enum.auto()
    INVALID_JSON = enum.auto()
    COMMAND_FAILED = enum.auto()


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
