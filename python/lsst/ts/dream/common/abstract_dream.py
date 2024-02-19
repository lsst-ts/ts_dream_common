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

__all__ = ["AbstractDream"]

import typing
from abc import ABC, abstractmethod


class AbstractDream(ABC):
    """Abstract class that defines the communication interface of a DREAM
    instance."""

    @abstractmethod
    async def resume(self) -> None:
        """Indicate that DREAM is permitted to resume automated operations."""
        raise NotImplementedError

    @abstractmethod
    async def open_roof(self) -> None:
        """Open the roof if DREAM has evaluated that it is safe to do so."""
        raise NotImplementedError

    @abstractmethod
    async def close_roof(self) -> None:
        """Close the roof."""
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        """Immediately stop operations and close the roof."""
        raise NotImplementedError

    @abstractmethod
    async def set_ready_for_data(self, ready: bool) -> None:
        """Inform DREAM that Rubin Observatory is ready to receive data as
        indicated.

        Parameters
        ----------
        ready: `bool`
            Rubin Observatory is ready to receive data (True) or not (False).
        """
        raise NotImplementedError

    @abstractmethod
    async def set_data_archived(self) -> None:
        """Inform DREAM that Rubin Observatory has received and archived a data
        product.

        Notes
        -----
        This method will require one or more parameters. Currently it is
        unknown what the parameters will be so they will be added later.

        """
        raise NotImplementedError

    @abstractmethod
    async def set_weather_info(
        self, weather_info: typing.Dict[str, typing.Union[float, bool]]
    ) -> None:
        """Inform DREAM of the current weather conditions.

        Parameters
        ----------
        weather_info : `dict`
            A dict of weather information to send. It should contain the
            following keys:

                - temperature : `float`
                - humidity : `float`
                - wind_speed : `float`
                - wind_direction : `float`
                - pressure : `float`
                - rain : `float`
                - cloudcover : `float`
                - safe_observing_conditions : `bool`
        """
        raise NotImplementedError

    @abstractmethod
    async def status(self) -> None:
        """Send the current status of DREAM."""
        raise NotImplementedError

    @abstractmethod
    async def new_data_products(self) -> None:
        """Inform the client that new data products are available."""
        raise NotImplementedError
