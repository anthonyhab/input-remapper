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
"""Hyprland window focus monitoring backend."""

import asyncio
import os
from typing import Optional, Callable

from inputremapper.profile_switching.backends.base import AppMonitorBackend


class HyprlandBackend(AppMonitorBackend):
    """Hyprland window focus monitoring using IPC socket."""

    def __init__(self):
        self._socket_path: Optional[str] = None
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None

    def _find_socket(self) -> Optional[str]:
        """Find the Hyprland socket2.sock path.

        Checks in order:
        1. $XDG_RUNTIME_DIR/hypr/$HYPRLAND_INSTANCE_SIGNATURE/.socket2.sock
        2. /run/user/$UID/hypr/$HYPRLAND_INSTANCE_SIGNATURE/.socket2.sock
        3. Iterate /run/user/* to find hypr directories

        Returns
        -------
        Optional[str]
            Path to socket2.sock if found, None otherwise
        """
        # Check HYPRLAND_INSTANCE_SIGNATURE env var first
        instance_sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
        runtime_dir = os.environ.get("XDG_RUNTIME_DIR")

        if instance_sig:
            # Try XDG_RUNTIME_DIR first
            if runtime_dir:
                path = os.path.join(runtime_dir, "hypr", instance_sig, ".socket2.sock")
                if os.path.exists(path):
                    return path

            # Try /run/user/$UID
            uid = os.getuid()
            path = os.path.join(
                "/run/user", str(uid), "hypr", instance_sig, ".socket2.sock"
            )
            if os.path.exists(path):
                return path

        # Try to find any hypr socket in /run/user/*
        run_user = "/run/user"
        if os.path.isdir(run_user):
            uid = os.getuid()
            user_dir = os.path.join(run_user, str(uid))
            if os.path.isdir(user_dir):
                hypr_dir = os.path.join(user_dir, "hypr")
                if os.path.isdir(hypr_dir):
                    # Find any instance directory
                    for entry in os.listdir(hypr_dir):
                        socket_path = os.path.join(hypr_dir, entry, ".socket2.sock")
                        if os.path.exists(socket_path):
                            return socket_path

        return None

    def is_available(self) -> bool:
        """Check if Hyprland backend is available.

        Returns
        -------
        bool
            True if socket2.sock exists
        """
        self._socket_path = self._find_socket()
        return self._socket_path is not None

    async def connect(self) -> bool:
        """Connect to Hyprland's socket2.sock.

        Returns
        -------
        bool
            True if connection successful
        """
        if not self._socket_path:
            self._socket_path = self._find_socket()
            if not self._socket_path:
                return False

        try:
            self._reader, self._writer = await asyncio.open_unix_connection(
                self._socket_path
            )
            return True
        except (OSError, ConnectionRefusedError):
            return False

    async def watch(self, callback: Callable[[Optional[str]], None]) -> None:
        """Watch for activewindow events from Hyprland.

        Parses lines like: activewindow>>class,title
        Calls callback with the window class.

        Parameters
        ----------
        callback : Callable[[Optional[str]], None]
            Function to call when window focus changes
        """
        if not self._reader:
            raise RuntimeError("Not connected. Call connect() first.")

        while True:
            try:
                line = await self._reader.readline()
                if not line:
                    # Connection closed
                    break

                line = line.decode("utf-8").strip()
                if line.startswith("activewindow>>"):
                    # Parse: activewindow>>class,title
                    content = line[len("activewindow>>") :]
                    parts = content.split(",", 1)
                    if parts:
                        window_class = parts[0].strip()
                        callback(window_class)
            except (OSError, ConnectionResetError):
                # Connection lost, break out
                break
