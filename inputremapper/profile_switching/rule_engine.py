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
"""Pure rule engine for per-application profile switching."""

from __future__ import annotations


def resolve(profile: dict, app_class: str) -> dict[str, str]:
    """Resolve effective presets for given app_class based on profile rules.

    1. Start with profile["defaults"] as base (group_key -> preset)
    2. Find first rule where rule["app_class"] == app_class
    3. If found, apply rule["overrides"] on top of defaults
    4. Return the resulting map

    Parameters
    ----------
    profile: dict
        Profile dict with "defaults" (dict) and "rules" (list)
    app_class: str
        The current application class/window class

    Returns
    -------
    dict[str, str]
        Mapping of group_key -> preset_name
    """
    result = dict(profile.get("defaults", {}))

    rules = profile.get("rules", [])
    for rule in rules:
        if rule.get("app_class") == app_class:
            overrides = rule.get("overrides", {})
            result.update(overrides)
            break

    return result


def get_effective_presets(profile: dict, app_class: str) -> dict[str, str]:
    """Alias/wrapper for resolve (same implementation).

    Parameters
    ----------
    profile: dict
        Profile dict with "defaults" (dict) and "rules" (list)
    app_class: str
        The current application class/window class

    Returns
    -------
    dict[str, str]
        Mapping of group_key -> preset_name
    """
    return resolve(profile, app_class)
