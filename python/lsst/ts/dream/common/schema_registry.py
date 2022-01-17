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

__all__ = ["registry"]

import json
import typing

registry: typing.Dict[str, typing.Any] = {
    "command": json.loads(
        """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "description": "Schema for Sensor Telemetry",
  "type": "object",
  "properties": {
    "command_id": {
      "type": "integer"
    },
    "key": {
      "enum": [
        "resume",
        "openRoof",
        "closeRoof",
        "stop",
        "readyForData",
        "dataArchived",
        "setWeatherInfo"
      ]
    },
    "parameters": {
      "type": "object"
    },
    "time_command_sent": {
      "type": "number"
    }
  },
  "required": ["command_id", "key", "parameters", "time_command_sent"],
  "additionalProperties": false
}
        """
    )
}
