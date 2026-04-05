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
"""Manages per-application profile switching configuration."""

from __future__ import annotations

import copy
import json
import os
from typing import Optional

from inputremapper.configs.paths import PathUtils
from inputremapper.logging.logger import logger
from inputremapper.user import UserUtils

INITIAL_CONFIG = {
    "version": "2.2.0",
    "enabled": False,
    "active_profile": None,
    "profiles": {},
}


class ProfileSwitchingConfig:
    """Manages profile definitions in ~/.config/input-remapper-2/profiles.json."""

    def __init__(self):
        self.path = PathUtils.profiles_path()
        self._config = copy.deepcopy(INITIAL_CONFIG)

    def load(self, path: Optional[str] = None):
        """Load the config from disk, creating defaults if missing."""
        if path is not None:
            self.path = path

        if not os.path.exists(self.path):
            self._config = copy.deepcopy(INITIAL_CONFIG)
            self._save_config()
            return

        with open(self.path, "r") as file:
            try:
                self._config = json.load(file)
                logger.info('Loaded profile config from "%s"', self.path)
            except json.decoder.JSONDecodeError as error:
                logger.error(
                    'Failed to parse profile config "%s": %s. Using defaults',
                    self.path,
                    str(error),
                )
                self._config = copy.deepcopy(INITIAL_CONFIG)

    def save(self, path: Optional[str] = None):
        """Save the config to disk. Skipped for root user."""
        if path is not None:
            self.path = path

        self._save_config()

    def get_profiles(self) -> dict:
        """Returns a deep copy of the profiles dict."""
        return copy.deepcopy(self._config.get("profiles", {}))

    def get_profile(self, name: str) -> Optional[dict]:
        """Returns a deep copy of a single profile or None."""
        profile = self._config.get("profiles", {}).get(name)
        if profile is None:
            return None
        return copy.deepcopy(profile)

    def create_profile(
        self, name: str, defaults: Optional[dict] = None, rules: Optional[list] = None
    ):
        """Creates a new profile. Raises ValueError if it already exists."""
        if name in self._config.get("profiles", {}):
            raise ValueError(f"Profile '{name}' already exists")

        if "profiles" not in self._config:
            self._config["profiles"] = {}

        self._config["profiles"][name] = {
            "defaults": defaults if defaults is not None else {},
            "rules": rules if rules is not None else [],
        }

    def delete_profile(self, name: str):
        """Deletes a profile. Clears active_profile if it was the active one."""
        profiles = self._config.get("profiles", {})
        if name in profiles:
            del profiles[name]

        if self._config.get("active_profile") == name:
            self._config["active_profile"] = None

    def rename_profile(self, old: str, new: str):
        """Renames a profile and updates active_profile reference if needed."""
        profiles = self._config.get("profiles", {})
        if old in profiles:
            profiles[new] = profiles.pop(old)

        if self._config.get("active_profile") == old:
            self._config["active_profile"] = new

    def set_active_profile(self, name: Optional[str]):
        """Sets the active profile. Pass None to deactivate."""
        self._config["active_profile"] = name

    def get_active_profile(self) -> Optional[str]:
        """Returns the active profile name or None."""
        return self._config.get("active_profile")

    def is_enabled(self) -> bool:
        """Returns the enabled boolean."""
        return self._config.get("enabled", False)

    def set_enabled(self, value: bool):
        """Sets the enabled boolean."""
        self._config["enabled"] = value

    def _save_config(self):
        """Save the config to the file system."""
        if UserUtils.user == "root":
            logger.debug("Skipping config file creation for the root user")
            return

        PathUtils.touch(self.path)

        with open(self.path, "w") as file:
            json.dump(self._config, file, indent=4)
            logger.info("Saved profile config to %s", self.path)
            file.write("\n")
