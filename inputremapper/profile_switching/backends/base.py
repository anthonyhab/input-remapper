# -*- coding: utf-8 -*-
# input-remapper - GUI for device specific keyboard mappings
# Copyright (C) 2025 sezanzeb <b8x45ygc9@mozmail.com>
#
# This file is part of input-remapper.
#
# input-remapper is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# input-remapper is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with input-remapper.  If not, see <https://www.gnu.org/licenses/>.
"""Abstract base class for application monitoring backends."""

from abc import ABC, abstractmethod
from typing import Optional, Callable


class AppMonitorBackend(ABC):
    """Abstract base class for window focus monitoring backends.

    Implementations should monitor window manager events and report
    the currently focused application's class/window class.
    """

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the backend's event source.

        Returns
        -------
        bool
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    async def watch(self, callback: Callable[[Optional[str]], None]) -> None:
        """Watch for window focus changes and call callback with app class.

        This method should run indefinitely, calling the callback whenever
        the focused window changes. The callback receives the window class
        (or None if no window is focused).

        Parameters
        ----------
        callback : Callable[[Optional[str]], None]
            Function to call with the new window class
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available on the current system.

        Returns
        -------
        bool
            True if the backend can be used (e.g., socket exists)
        """
        pass
