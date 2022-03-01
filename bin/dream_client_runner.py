#!/usr/bin/env python

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

from lsst.ts.dream import common

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.INFO
)


async def main() -> None:
    """Main method that gets executed when running from the command line."""
    logging.info("main method")
    mock_dream = common.mock.MockDream()
    await mock_dream.start_task
    assert mock_dream.server.is_serving()

    mock_dream_client_runner = common.mock.MockDreamClientRunner()
    await mock_dream_client_runner.execute_nominal_run()

    await mock_dream.close()
    await mock_dream.server.wait_closed()


if __name__ == "__main__":
    logging.info("main")
    try:
        logging.info("Calling main method")
        asyncio.run(main())
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
