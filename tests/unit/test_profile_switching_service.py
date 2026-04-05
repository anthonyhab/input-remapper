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

"""Tests for the profile switching service."""

import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

from tests.lib.test_setup import test_setup


@test_setup
class TestProfileSwitchingService(unittest.IsolatedAsyncioTestCase):
    """Test suite for ProfileService."""

    async def test_service_skips_if_not_enabled(self):
        """Service exits immediately if profile switching is disabled."""
        # Arrange
        from inputremapper.profile_switching.service import ProfileService

        config = MagicMock()
        config.is_enabled.return_value = False
        backend = AsyncMock()
        daemon = MagicMock()

        service = ProfileService(config, backend, daemon)

        # Act
        await service.run()

        # Assert
        backend.connect.assert_not_called()
        backend.watch.assert_not_called()

    async def test_service_calls_daemon_on_app_change(self):
        """Service calls daemon.switch_preset when app changes."""
        # Arrange
        from inputremapper.profile_switching.service import ProfileService

        config = MagicMock()
        config.is_enabled.return_value = True
        config.get_active_profile.return_value = "my_profile"
        config.get_profile.return_value = {
            "defaults": {"group1": "preset1"},
            "rules": [],
        }

        backend = AsyncMock()
        daemon = MagicMock()
        daemon.switch_preset = MagicMock()

        service = ProfileService(config, backend, daemon)

        # Act - simulate the backend calling the callback
        await service.run()

        # Get the callback that was passed to backend.watch
        self.assertTrue(backend.watch.called)
        callback = backend.watch.call_args[0][0]

        # Simulate app change
        callback("firefox")

        # Assert
        daemon.switch_preset.assert_called_once_with("group1", "preset1")

    async def test_service_uses_rule_engine(self):
        """Verify resolve() is called with correct arguments."""
        # Arrange
        from inputremapper.profile_switching.service import ProfileService

        config = MagicMock()
        config.is_enabled.return_value = True
        config.get_active_profile.return_value = "my_profile"
        profile_data = {
            "defaults": {"group1": "default_preset"},
            "rules": [
                {"app_class": "firefox", "overrides": {"group1": "firefox_preset"}}
            ],
        }
        config.get_profile.return_value = profile_data

        backend = AsyncMock()
        daemon = MagicMock()

        service = ProfileService(config, backend, daemon)

        with patch("inputremapper.profile_switching.service.resolve") as mock_resolve:
            mock_resolve.return_value = {"group1": "firefox_preset"}

            # Act
            await service.run()
            callback = backend.watch.call_args[0][0]
            callback("firefox")

            # Assert
            mock_resolve.assert_called_once_with(profile_data, "firefox")
            daemon.switch_preset.assert_called_once_with("group1", "firefox_preset")

    async def test_service_dedupes_same_app(self):
        """Same app class twice = only one daemon call."""
        # Arrange
        from inputremapper.profile_switching.service import ProfileService

        config = MagicMock()
        config.is_enabled.return_value = True
        config.get_active_profile.return_value = "my_profile"
        config.get_profile.return_value = {
            "defaults": {"group1": "preset1"},
            "rules": [],
        }

        backend = AsyncMock()
        daemon = MagicMock()
        daemon.switch_preset = MagicMock()

        service = ProfileService(config, backend, daemon)

        # Act
        await service.run()
        callback = backend.watch.call_args[0][0]

        # First app change
        callback("firefox")
        # Same app again - should be deduped
        callback("firefox")

        # Assert - only called once
        self.assertEqual(daemon.switch_preset.call_count, 1)

    async def test_service_handles_no_active_profile(self):
        """No active profile = no daemon calls."""
        # Arrange
        from inputremapper.profile_switching.service import ProfileService

        config = MagicMock()
        config.is_enabled.return_value = True
        config.get_active_profile.return_value = None  # No active profile

        backend = AsyncMock()
        daemon = MagicMock()
        daemon.switch_preset = MagicMock()

        service = ProfileService(config, backend, daemon)

        # Act
        await service.run()
        callback = backend.watch.call_args[0][0]
        callback("firefox")

        # Assert - no daemon calls
        daemon.switch_preset.assert_not_called()

    async def test_service_diffs_against_last_applied(self):
        """Only changed presets trigger daemon calls."""
        # Arrange
        from inputremapper.profile_switching.service import ProfileService

        config = MagicMock()
        config.is_enabled.return_value = True
        config.get_active_profile.return_value = "my_profile"

        # First app config
        config.get_profile.return_value = {
            "defaults": {
                "group1": "preset1",
                "group2": "preset2",
            },
            "rules": [],
        }

        backend = AsyncMock()
        daemon = MagicMock()
        daemon.switch_preset = MagicMock()

        service = ProfileService(config, backend, daemon)

        # Act - first app
        await service.run()
        callback = backend.watch.call_args[0][0]
        callback("firefox")

        # Both presets should be applied
        self.assertEqual(daemon.switch_preset.call_count, 2)
        daemon.switch_preset.assert_any_call("group1", "preset1")
        daemon.switch_preset.assert_any_call("group2", "preset2")

        # Reset mock
        daemon.switch_preset.reset_mock()

        # Same app again - no changes
        callback("firefox")
        daemon.switch_preset.assert_not_called()

        # Reset mock
        daemon.switch_preset.reset_mock()

        # Different app with overlapping presets
        config.get_profile.return_value = {
            "defaults": {
                "group1": "preset1",  # Same
                "group2": "new_preset",  # Changed
            },
            "rules": [],
        }
        callback("chrome")

        # Only changed preset should be applied
        self.assertEqual(daemon.switch_preset.call_count, 1)
        daemon.switch_preset.assert_called_once_with("group2", "new_preset")

    async def test_service_handles_daemon_disconnect(self):
        """Graceful handling when daemon is not available."""
        # Arrange
        from inputremapper.profile_switching.service import ProfileService

        config = MagicMock()
        config.is_enabled.return_value = True
        config.get_active_profile.return_value = "my_profile"
        config.get_profile.return_value = {
            "defaults": {"group1": "preset1"},
            "rules": [],
        }

        backend = AsyncMock()
        daemon = MagicMock()
        daemon.switch_preset = MagicMock()

        service = ProfileService(config, backend, daemon)

        # Act
        await service.run()
        callback = backend.watch.call_args[0][0]

        # Simulate daemon raising exception
        daemon.switch_preset.side_effect = Exception("Daemon disconnected")

        # Should not raise - handled gracefully
        try:
            callback("firefox")
        except Exception:
            self.fail("Service should handle daemon disconnect gracefully")

    async def test_service_loads_config_on_startup(self):
        """Config loaded before run."""
        # Arrange
        from inputremapper.profile_switching.service import ProfileService

        config = MagicMock()
        config.is_enabled.return_value = True
        config.get_active_profile.return_value = "my_profile"
        config.get_profile.return_value = {
            "defaults": {"group1": "preset1"},
            "rules": [],
        }

        backend = AsyncMock()
        daemon = MagicMock()

        # Act - create service (config should already be passed in)
        service = ProfileService(config, backend, daemon)

        # Run and trigger app change
        await service.run()
        callback = backend.watch.call_args[0][0]
        callback("firefox")

        # Assert - config methods were called
        config.is_enabled.assert_called()
        config.get_active_profile.assert_called()
        config.get_profile.assert_called_with("my_profile")
        daemon.switch_preset.assert_called_once_with("group1", "preset1")


if __name__ == "__main__":
    unittest.main()
