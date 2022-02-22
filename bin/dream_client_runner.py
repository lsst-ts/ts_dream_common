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
import typing

from lsst.ts.dream import common

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.INFO
)

# Time interval for mocking waiting for an operator to the observing run.
OPERATOR_WAIT_INTERVAL = 20

# Time interval to wait until checking the server or roof status.
WAIT_INTERVAL = 1

# The number of new data products to receive before shutting down.
NUM_NEW_DATA_PRODUCTS_TO_RECEIVE = 10


class MockDreamClientRunner:
    """Run a MockDreamClient such that it mocks an observing run.

    Notes
    -----
    It is assumed that a (mock) DREAM server is running.
    """

    def __init__(self) -> None:
        self.log = logging.getLogger(type(self).__name__)
        self.log.setLevel(logging.DEBUG)
        self.mock_dream_client = common.mock.MockDreamClient()

        # Task for receiving data from (the mock) DREAM.
        self.process_dream_messages_task: asyncio.Future = asyncio.Future()

        # Keep track of the master server state.
        self.master_server_state = 0

        # Keep track of the roof status.
        self.roof_status = 0

        # Keep track of the commands sent and their status.
        self.command_status: typing.Dict[int, int] = {}

        # Keep track of data products received.
        self.data_products_received: typing.Dict[int, typing.Dict[str, typing.Any]] = {}

    async def execute_nominal_run(self) -> None:
        """Execute a nominal run.

        Notes
        -----
        The MockDreamClient runner will

            - connect to (the mock) DREAM server
            - indicate that it may resume operations
            - instruct it to open the roof
            - receive several data products
            - instruct it to close the roof
            - indicate that it should stop operations
            - disconnect
        """
        # Connect to (the mock) DREAM server.
        await self.mock_dream_client.connect()

        # Start reading data.
        self.process_dream_messages_task = asyncio.create_task(
            self.process_dream_messages()
        )

        # Wait a bit to mock an operator getting ready for the night. Note that
        # DREAM is expected to send status messages and that the
        # MockDreamClient is receiving them.
        self.log.debug("Waiting for an operator to start sending commands.")
        await asyncio.sleep(OPERATOR_WAIT_INTERVAL)

        # Indicate that DREAM may resume.
        cmd = "resume"
        cmd_id = await self.mock_dream_client.run_command(command=cmd)
        self.command_status[cmd_id] = 0
        self.log.debug("Waiting for DREAM to have resumed.")
        while self.command_status[cmd_id] != common.CommandResponse.LAST:
            await asyncio.sleep(WAIT_INTERVAL)

        # Open the roof.
        cmd = "openRoof"
        cmd_id = await self.mock_dream_client.run_command(command=cmd)
        self.command_status[cmd_id] = 0
        self.log.debug("Waiting for the roof to be open.")
        while self.command_status[cmd_id] != common.CommandResponse.LAST:
            await asyncio.sleep(WAIT_INTERVAL)

        # Start receiving telemetry.
        cmd = "readyForData"
        cmd_id = await self.mock_dream_client.run_command(command=cmd, ready=True)
        self.command_status[cmd_id] = 0
        self.log.debug("Ready to receive data.")
        while self.command_status[cmd_id] != common.CommandResponse.LAST:
            await asyncio.sleep(WAIT_INTERVAL)
        while len(self.data_products_received) < NUM_NEW_DATA_PRODUCTS_TO_RECEIVE:
            self.log.debug(
                f"Received {len(self.data_products_received)} data products so far."
            )
            await asyncio.sleep(WAIT_INTERVAL)

        # Stop receiving telemetry.
        cmd = "readyForData"
        cmd_id = await self.mock_dream_client.run_command(command=cmd, ready=False)
        self.command_status[cmd_id] = 0
        self.log.debug("Stop receiving data.")
        while self.command_status[cmd_id] != common.CommandResponse.LAST:
            await asyncio.sleep(WAIT_INTERVAL)

        # Close the roof.
        cmd = "closeRoof"
        cmd_id = await self.mock_dream_client.run_command(command=cmd)
        self.command_status[cmd_id] = 0
        self.log.debug("Waiting for the roof to be closed.")
        while self.command_status[cmd_id] != common.CommandResponse.LAST:
            await asyncio.sleep(WAIT_INTERVAL)

        # Indicate that DREAM should stop.
        cmd = "stop"
        cmd_id = await self.mock_dream_client.run_command(command=cmd)
        self.command_status[cmd_id] = 0
        self.log.debug("Waiting for DREAM to have stopped.")
        while self.command_status[cmd_id] != common.CommandResponse.LAST:
            await asyncio.sleep(WAIT_INTERVAL)

        self.process_dream_messages_task.cancel()

        # Finally, disconnect from (the mock) DREAM server.
        if self.mock_dream_client.connected:
            await self.mock_dream_client.disconnect()

    async def process_dream_messages(self) -> None:
        """Instruct the MockDreamClient to read data and process those.

        Raises
        ------
        RuntimeError
            In case unexpected data are received.
        """
        try:
            while True:
                data = await self.mock_dream_client.read()
                self.log.debug(f"Received data {data!r}")
                if "device" in data:
                    self.master_server_state = data["state"]
                    self.roof_status = data["roof_status"]
                elif "command_id" in data:
                    self.command_status[data["command_id"]] = data["command_response"]
                elif "metadata" in data:
                    amount = data["amount"]
                    self.log.debug(f"Received {amount} data products.")
                    metadata = data["metadata"]
                    for d in metadata:
                        self.data_products_received[
                            len(self.data_products_received)
                        ] = d
                else:
                    raise RuntimeError(f"Invalid data {data!r} received.")

        except Exception:
            self.log.exception("process_dream_messages failed.")


async def main() -> None:
    """Main method that gets executed when running from the command line."""
    logging.info("main method")
    mock_dream = common.mock.MockDream()
    await mock_dream.start_task
    assert mock_dream.server.is_serving()

    mock_dream_client_runner = MockDreamClientRunner()
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
