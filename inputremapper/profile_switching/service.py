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
"""User session profile switching service."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Callable

from inputremapper.configs.profile_switching_config import ProfileSwitchingConfig
from inputremapper.profile_switching.backends.base import AppMonitorBackend
from inputremapper.logging.logger import logger
from inputremapper.profile_switching.rule_engine import resolve

if TYPE_CHECKING:
    from inputremapper.daemon import DaemonProxy


class ProfileService:
    """Orchestrates per-application profile switching.

    Flow:
    1. Load config
    2. If not enabled → exit
    3. Connect to backend
    4. For each app_class change:
       a. Get active profile from config
       b. resolve(profile, app_class) → desired: dict[group_key, preset]
       c. diff desired vs last_applied
       d. For each changed group_key: daemon.switch_preset(group_key, preset)
       e. Update last_applied
    """

    def __init__(
        self,
        config: ProfileSwitchingConfig,
        backend: AppMonitorBackend,
        daemon: DaemonProxy,
    ) -> None:
        self._config = config
        self._backend = backend
        self._daemon = daemon
        self._last_applied: dict[str, str] = {}  # group_key -> preset
        self._current_app: Optional[str] = None

    async def run(self) -> None:
        """Start the profile switching service."""
        if not self._config.is_enabled():
            logger.info("Profile switching is disabled, exiting")
            return

        # Connect to backend and start watching
        connected = await self._backend.connect()
        if not connected:
            logger.error("Failed to connect to backend")
            return

        await self._backend.watch(self._on_app_change)

    def _on_app_change(self, app_class: Optional[str]) -> None:
        """Handle application focus change.

        Parameters
        ----------
        app_class : Optional[str]
            The window class of the focused application, or None
        """
        # Skip if same app (dedupe)
        if app_class == self._current_app:
            return

        self._current_app = app_class

        # Get active profile from config
        active_profile = self._config.get_active_profile()
        if active_profile is None:
            logger.debug("No active profile configured")
            return

        # Get profile dict
        profile = self._config.get_profile(active_profile)
        if profile is None:
            logger.error("Active profile '%s' not found", active_profile)
            return

        # Resolve desired presets using rule engine
        desired = resolve(profile, app_class or "")

        # Diff against last applied - only switch changed presets
        diff = {k: v for k, v in desired.items() if self._last_applied.get(k) != v}

        # Apply changes via daemon
        for group_key, preset in diff.items():
            try:
                self._daemon.switch_preset(group_key, preset)
            except Exception as e:
                logger.error(
                    "Failed to switch preset for %s to %s: %s",
                    group_key,
                    preset,
                    str(e),
                )

        # Update last applied
        self._last_applied = desired
