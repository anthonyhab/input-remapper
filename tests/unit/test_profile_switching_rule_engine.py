#!/usr/bin/env python3
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


import unittest

from tests.lib.test_setup import test_setup


@test_setup
class TestProfileSwitchingRuleEngine(unittest.TestCase):
    def test_resolve_empty_profile(self):
        """Empty profile returns empty dict."""
        from inputremapper.profile_switching.rule_engine import resolve

        profile = {}
        result = resolve(profile, "any_app")
        self.assertEqual(result, {})

    def test_resolve_defaults_only(self):
        """Profile with defaults, no matching rule returns defaults."""
        from inputremapper.profile_switching.rule_engine import resolve

        profile = {
            "defaults": {"mouse": "default_mouse", "kbd": "default_kbd"},
            "rules": [],
        }
        result = resolve(profile, "unknown_app")
        self.assertEqual(result, {"mouse": "default_mouse", "kbd": "default_kbd"})

    def test_resolve_first_rule_wins(self):
        """Two rules, first matching one applies."""
        from inputremapper.profile_switching.rule_engine import resolve

        profile = {
            "defaults": {"mouse": "default_mouse", "kbd": "default_kbd"},
            "rules": [
                {"app_class": "firefox", "overrides": {"mouse": "browser_mouse"}},
                {
                    "app_class": "firefox",
                    "overrides": {"mouse": "second_browser_mouse"},
                },
            ],
        }
        # First rule should win
        result = resolve(profile, "firefox")
        self.assertEqual(result, {"mouse": "browser_mouse", "kbd": "default_kbd"})

    def test_resolve_overrides_merge(self):
        """Overrides on top of defaults (different groups)."""
        from inputremapper.profile_switching.rule_engine import resolve

        profile = {
            "defaults": {"mouse": "default_mouse", "kbd": "default_kbd"},
            "rules": [
                {"app_class": "game", "overrides": {"gamepad": "gamepad_preset"}},
            ],
        }
        result = resolve(profile, "game")
        self.assertEqual(
            result,
            {
                "mouse": "default_mouse",
                "kbd": "default_kbd",
                "gamepad": "gamepad_preset",
            },
        )

    def test_resolve_overrides_replace(self):
        """Override replaces default for same group."""
        from inputremapper.profile_switching.rule_engine import resolve

        profile = {
            "defaults": {"mouse": "default_mouse", "kbd": "default_kbd"},
            "rules": [
                {"app_class": "firefox", "overrides": {"mouse": "browser_mouse"}},
            ],
        }
        result = resolve(profile, "firefox")
        self.assertEqual(result, {"mouse": "browser_mouse", "kbd": "default_kbd"})

    def test_resolve_no_defaults(self):
        """Only overrides, no defaults."""
        from inputremapper.profile_switching.rule_engine import resolve

        profile = {
            "defaults": {},
            "rules": [
                {"app_class": "app1", "overrides": {"mouse": "app1_mouse"}},
            ],
        }
        result = resolve(profile, "app1")
        self.assertEqual(result, {"mouse": "app1_mouse"})

    def test_resolve_unknown_app(self):
        """No rule matches, returns defaults."""
        from inputremapper.profile_switching.rule_engine import resolve

        profile = {
            "defaults": {"mouse": "default_mouse", "kbd": "default_kbd"},
            "rules": [
                {"app_class": "firefox", "overrides": {"mouse": "browser_mouse"}},
                {"app_class": "runelite", "overrides": {"mouse": "game_mouse"}},
            ],
        }
        result = resolve(profile, "unknown_app")
        self.assertEqual(result, {"mouse": "default_mouse", "kbd": "default_kbd"})

    def test_resolve_rules_empty(self):
        """Empty rules list."""
        from inputremapper.profile_switching.rule_engine import resolve

        profile = {
            "defaults": {"mouse": "default_mouse"},
            "rules": [],
        }
        result = resolve(profile, "any_app")
        self.assertEqual(result, {"mouse": "default_mouse"})

    def test_resolve_idempotent(self):
        """Same inputs always produce same outputs."""
        from inputremapper.profile_switching.rule_engine import resolve

        profile = {
            "defaults": {"mouse": "default_mouse", "kbd": "default_kbd"},
            "rules": [
                {"app_class": "firefox", "overrides": {"mouse": "browser_mouse"}},
            ],
        }
        result1 = resolve(profile, "firefox")
        result2 = resolve(profile, "firefox")
        self.assertEqual(result1, result2)
        # Ensure profile is not mutated
        self.assertEqual(
            profile["defaults"], {"mouse": "default_mouse", "kbd": "default_kbd"}
        )
        self.assertEqual(len(profile["rules"]), 1)

    def test_get_effective_presets_alias(self):
        """get_effective_presets is an alias for resolve."""
        from inputremapper.profile_switching.rule_engine import (
            resolve,
            get_effective_presets,
        )

        profile = {
            "defaults": {"mouse": "default_mouse"},
            "rules": [
                {"app_class": "firefox", "overrides": {"mouse": "browser_mouse"}},
            ],
        }
        result_resolve = resolve(profile, "firefox")
        result_alias = get_effective_presets(profile, "firefox")
        self.assertEqual(result_resolve, result_alias)


if __name__ == "__main__":
    unittest.main()
