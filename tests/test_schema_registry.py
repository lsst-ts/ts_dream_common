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

import logging
import unittest

import jsonschema
import pytest

from lsst.ts.dream import common

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)


class SchemaRegistryTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_command_schema(self) -> None:
        schema = common.registry["command"]
        # A command with an empty 'parameters' keyword, which should pass.
        command = {
            "command_id": 1,
            "key": "resume",
            "parameters": {},
            "time_command_sent": 1.12345,
        }
        jsonschema.validate(command, schema)

        # A command with a non-empty 'parameters' keyword, which should pass.
        command = {
            "command_id": 1,
            "key": "readyForData",
            "parameters": {"ready": True},
            "time_command_sent": 1.12345,
        }
        jsonschema.validate(command, schema)

        # A command without a 'parameters' keyword, which should fail.
        with pytest.raises(jsonschema.exceptions.ValidationError):
            command_without_parameters = {
                "command_id": 1,
                "key": "readyForData",
                "time_command_sent": 1.12345,
            }
            jsonschema.validate(command_without_parameters, schema)
