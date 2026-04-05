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


import asyncio
import os
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

from tests.lib.test_setup import test_setup


@test_setup
class TestProfileSwitchingBackends(unittest.TestCase):
    """Test suite for profile switching backend abstraction."""

    def run_async(self, coro):
        """Helper to run async coroutines in tests."""
        return asyncio.run(coro)

    def test_base_class_is_abstract(self):
        """Base AppMonitorBackend cannot be instantiated directly."""
        from inputremapper.profile_switching.backends.base import AppMonitorBackend

        with self.assertRaises(TypeError):
            AppMonitorBackend()

    def test_registry_returns_none_when_no_backend(self):
        """Registry returns None when no backend is available."""
        from inputremapper.profile_switching.backends.registry import (
            get_available_backend,
        )

        # Mock os.path.exists to return False (no socket)
        with patch("os.path.exists", return_value=False):
            result = get_available_backend()
            self.assertIsNone(result)

    def test_hyprland_is_available_when_socket_exists(self):
        """Hyprland backend is available when socket2.sock exists."""
        from inputremapper.profile_switching.backends.hyprland import HyprlandBackend

        with patch("os.path.exists") as mock_exists:
            # Mock socket exists
            mock_exists.return_value = True
            backend = HyprlandBackend()
            self.assertTrue(backend.is_available())

    def test_hyprland_parse_activewindow(self):
        """Parse activewindow event with class and title."""
        from inputremapper.profile_switching.backends.hyprland import (
            HyprlandBackend,
        )

        backend = HyprlandBackend()

        # Mock reader with activewindow event
        mock_reader = MagicMock()
        mock_reader.readline = AsyncMock(
            side_effect=[
                b"activewindow>>net-runelite-client-RuneLite,RuneLite\n",
                b"",  # EOF
            ]
        )
        backend._reader = mock_reader

        # Mock callback
        callback = MagicMock()

        # Run watch (should process one event then exit on EOF)
        async def run_watch():
            await backend.watch(callback)

        self.run_async(run_watch())

        # Verify callback was called with correct window class
        callback.assert_called_once_with("net-runelite-client-RuneLite")

    def test_hyprland_parse_other_events(self):
        """Ignore non-activewindow events."""
        from inputremapper.profile_switching.backends.hyprland import (
            HyprlandBackend,
        )

        backend = HyprlandBackend()

        # Mock reader with various events
        mock_reader = MagicMock()
        mock_reader.readline = AsyncMock(
            side_effect=[
                b"workspace>>1\n",
                b"windowtitle>>12345,Some Title\n",
                b"activewindow>>firefox,Firefox\n",
                b"",  # EOF
            ]
        )
        backend._reader = mock_reader

        # Mock callback
        callback = MagicMock()

        # Run watch
        async def run_watch():
            await backend.watch(callback)

        self.run_async(run_watch())

        # Verify callback was only called for activewindow event
        callback.assert_called_once_with("firefox")

    def test_hyprland_find_socket_with_signature(self):
        """Find socket using HYPRLAND_INSTANCE_SIGNATURE env var."""
        from inputremapper.profile_switching.backends.hyprland import (
            HyprlandBackend,
        )

        backend = HyprlandBackend()

        with patch.dict(
            os.environ,
            {
                "HYPRLAND_INSTANCE_SIGNATURE": "abc123_1234567890",
                "XDG_RUNTIME_DIR": "/run/user/1000",
            },
        ):
            with patch("os.path.exists") as mock_exists:
                # First call is for socket path check
                # Second call in is_available also checks
                expected_path = "/run/user/1000/hypr/abc123_1234567890/.socket2.sock"

                def exists_side_effect(path):
                    return path == expected_path

                mock_exists.side_effect = exists_side_effect

                result = backend._find_socket()
                self.assertEqual(result, expected_path)

    def test_hyprland_find_socket_fallback(self):
        """Find socket using fallback /run/user/* iteration."""
        from inputremapper.profile_switching.backends.hyprland import (
            HyprlandBackend,
        )

        backend = HyprlandBackend()

        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.isdir") as mock_isdir:
                with patch("os.listdir") as mock_listdir:
                    with patch("os.path.exists") as mock_exists:
                        # Mock directory structure
                        mock_isdir.side_effect = lambda p: p in [
                            "/run/user",
                            "/run/user/1000",
                            "/run/user/1000/hypr",
                        ]
                        mock_listdir.return_value = ["xyz789_9876543210"]

                        expected_path = (
                            "/run/user/1000/hypr/xyz789_9876543210/.socket2.sock"
                        )

                        def exists_side_effect(path):
                            return path == expected_path

                        mock_exists.side_effect = exists_side_effect

                        result = backend._find_socket()
                        self.assertEqual(result, expected_path)

    def test_registry_returns_hyprland_when_socket_exists(self):
        """Registry returns HyprlandBackend when socket exists."""
        from inputremapper.profile_switching.backends.registry import (
            get_available_backend,
        )
        from inputremapper.profile_switching.backends.hyprland import (
            HyprlandBackend,
        )

        with patch("os.path.exists") as mock_exists:
            with patch("os.path.isdir") as mock_isdir:
                with patch("os.listdir") as mock_listdir:
                    # Mock socket exists
                    mock_isdir.side_effect = lambda p: p in [
                        "/run/user",
                        "/run/user/1000",
                        "/run/user/1000/hypr",
                    ]
                    mock_listdir.return_value = ["test123"]
                    mock_exists.return_value = True

                    result = get_available_backend()
                    self.assertIsNotNone(result)
                    self.assertIsInstance(result, HyprlandBackend)

    def test_hyprland_watch_calls_callback(self):
        """Watch method calls callback when activewindow events arrive."""
        from inputremapper.profile_switching.backends.hyprland import (
            HyprlandBackend,
        )

        backend = HyprlandBackend()

        # Create mock reader that simulates multiple events
        mock_reader = MagicMock()
        events = [
            b"activewindow>>firefox,Firefox Browser\n",
            b"activewindow>>code,VS Code\n",
            b"activewindow>>terminal,Terminal\n",
            b"",  # EOF to stop
        ]
        mock_reader.readline = AsyncMock(side_effect=events)
        backend._reader = mock_reader

        # Mock callback
        callback = MagicMock()

        # Run watch
        async def run_watch():
            await backend.watch(callback)

        self.run_async(run_watch())

        # Verify callback was called for each activewindow event
        self.assertEqual(callback.call_count, 3)
        callback.assert_any_call("firefox")
        callback.assert_any_call("code")
        callback.assert_any_call("terminal")


if __name__ == "__main__":
    unittest.main()
