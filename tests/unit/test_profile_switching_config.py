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


import os
import unittest

from tests.lib.test_setup import test_setup


@test_setup
class TestProfileSwitchingConfig(unittest.TestCase):
    def test_defaults(self):
        from inputremapper.configs.profile_switching_config import (
            ProfileSwitchingConfig,
        )

        config = ProfileSwitchingConfig()
        self.assertEqual(config.get_profiles(), {})
        self.assertFalse(config.is_enabled())
        self.assertIsNone(config.get_active_profile())

    def test_create_profile(self):
        from inputremapper.configs.profile_switching_config import (
            ProfileSwitchingConfig,
        )

        config = ProfileSwitchingConfig()
        config.create_profile("gaming")
        profiles = config.get_profiles()
        self.assertIn("gaming", profiles)
        self.assertEqual(profiles["gaming"]["defaults"], {})
        self.assertEqual(profiles["gaming"]["rules"], [])

    def test_create_profile_duplicate(self):
        from inputremapper.configs.profile_switching_config import (
            ProfileSwitchingConfig,
        )

        config = ProfileSwitchingConfig()
        config.create_profile("gaming")
        self.assertRaises(ValueError, config.create_profile, "gaming")

    def test_delete_profile(self):
        from inputremapper.configs.profile_switching_config import (
            ProfileSwitchingConfig,
        )

        config = ProfileSwitchingConfig()
        config.create_profile("gaming")
        config.set_active_profile("gaming")
        config.delete_profile("gaming")
        self.assertNotIn("gaming", config.get_profiles())
        self.assertIsNone(config.get_active_profile())

    def test_rename_profile(self):
        from inputremapper.configs.profile_switching_config import (
            ProfileSwitchingConfig,
        )

        config = ProfileSwitchingConfig()
        config.create_profile("gaming")
        config.set_active_profile("gaming")
        config.rename_profile("gaming", "work")
        profiles = config.get_profiles()
        self.assertNotIn("gaming", profiles)
        self.assertIn("work", profiles)
        self.assertEqual(config.get_active_profile(), "work")

    def test_set_get_active_profile(self):
        from inputremapper.configs.profile_switching_config import (
            ProfileSwitchingConfig,
        )

        config = ProfileSwitchingConfig()
        config.set_active_profile("myprofile")
        self.assertEqual(config.get_active_profile(), "myprofile")
        config.set_active_profile(None)
        self.assertIsNone(config.get_active_profile())

    def test_set_get_enabled(self):
        from inputremapper.configs.profile_switching_config import (
            ProfileSwitchingConfig,
        )

        config = ProfileSwitchingConfig()
        config.set_enabled(True)
        self.assertTrue(config.is_enabled())
        config.set_enabled(False)
        self.assertFalse(config.is_enabled())

    def test_save_and_load(self):
        from inputremapper.configs.profile_switching_config import (
            ProfileSwitchingConfig,
        )

        config = ProfileSwitchingConfig()
        config.create_profile(
            "test_profile",
            {"mouse": "clicks"},
            [{"app_class": "foo", "overrides": {"wheel": "scroll"}}],
        )
        config.set_active_profile("test_profile")
        config.set_enabled(True)

        path = os.path.join("/tmp/test_input_remapper_profiles", "profiles.json")
        config.save(path)

        config2 = ProfileSwitchingConfig()
        config2.load(path)

        self.assertEqual(config2.get_active_profile(), "test_profile")
        self.assertTrue(config2.is_enabled())
        profiles = config2.get_profiles()
        self.assertIn("test_profile", profiles)
        self.assertEqual(profiles["test_profile"]["defaults"], {"mouse": "clicks"})
        self.assertEqual(len(profiles["test_profile"]["rules"]), 1)
        self.assertEqual(profiles["test_profile"]["rules"][0]["app_class"], "foo")

    def test_get_profile_deep_copy(self):
        from inputremapper.configs.profile_switching_config import (
            ProfileSwitchingConfig,
        )

        config = ProfileSwitchingConfig()
        config.create_profile("test", {"mouse": "clicks"}, [])

        profile = config.get_profile("test")
        profile["defaults"]["mouse"] = "modified"

        profile2 = config.get_profile("test")
        self.assertEqual(profile2["defaults"]["mouse"], "clicks")


if __name__ == "__main__":
    unittest.main()
