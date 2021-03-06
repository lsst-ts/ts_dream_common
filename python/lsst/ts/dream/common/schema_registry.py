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
    ),
    "master_server_status": json.loads(
        """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "description": "Schema for Sensor Telemetry",
  "type": "object",
  "properties": {
    "device": {
      "type": "integer"
    },
    "state": {
      "type": "integer"
    },
    "start_time": {
      "type": "number"
    },
    "stop_time": {
      "type": "number"
    },
    "error_code": {
      "type": "integer"
    },
    "rain_sensor": {
      "type": "boolean"
    },
    "roof_status": {
      "type": "integer"
    }
  },
  "required": [
    "device",
    "state",
    "start_time",
    "stop_time",
    "error_code",
    "rain_sensor",
    "roof_status"
  ],
  "additionalProperties": false
}
        """
    ),
    "new_data_products": json.loads(
        """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "description": "Schema for Sensor Telemetry",
  "type": "object",
  "properties": {
    "amount": {
      "type": "integer"
    },
    "metadata": {
      "type": "array",
      "minItems": 1,
      "items": [
        {
          "type": "object",
          "properties": {
            "name": {
              "type": "string"
            },
            "location": {
              "type": "string"
            },
            "timestamp": {
              "type": "number"
            }
          }
        }
      ],
      "required": [
        "name",
        "location",
        "timestamp"
      ],
      "additionalProperties": false
    }
  },
  "required": [
    "amount",
    "metadata"
  ],
  "additionalProperties": false
}
        """
    ),
    "weather_info": json.loads(
        """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "description": "Schema for Sensor Telemetry",
  "type": "object",
  "properties": {
    "temperature": {
      "type": "number"
    },
    "humidity": {
      "type": "number"
    },
    "wind_speed": {
      "type": "number"
    },
    "wind_direction": {
      "type": "number"
    },
    "pressure": {
      "type": "number"
    },
    "rain": {
      "type": "number"
    },
    "cloudcover": {
      "type": "number"
    },
    "safe_observing_conditions": {
      "type": "boolean"
    }
  },
  "required": [
    "temperature",
    "humidity",
    "wind_speed",
    "wind_direction",
    "pressure",
    "rain",
    "cloudcover",
    "safe_observing_conditions"
  ],
  "additionalProperties": false
}
        """
    ),
}
