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

"""User session profile switching service entry point."""

import asyncio
import signal
import sys
from argparse import ArgumentParser

from inputremapper.configs.profile_switching_config import ProfileSwitchingConfig
from inputremapper.daemon import Daemon
from inputremapper.logging.logger import logger
from inputremapper.profile_switching.backends.registry import get_available_backend
from inputremapper.profile_switching.service import ProfileService


class InputRemapperProfileServiceBin:
    """Entry point for the user session profile switching service."""

    @staticmethod
    def main() -> None:
        parser = ArgumentParser(
            description="User session profile switching service for input-remapper"
        )
        parser.add_argument(
            "-d",
            "--debug",
            action="store_true",
            dest="debug",
            help="Displays additional debug information",
            default=False,
        )
        parser.add_argument(
            "--hide-info",
            action="store_true",
            dest="hide_info",
            help="Don't display version information",
            default=False,
        )

        options = parser.parse_args(sys.argv[1:])
        logger.update_verbosity(options.debug)

        if not options.hide_info:
            logger.log_info("input-remapper-profile-service")

        # Load config
        config = ProfileSwitchingConfig()
        config.load()

        # Check if profile switching is enabled
        if not config.is_enabled():
            logger.info("Profile switching is disabled, exiting")
            sys.exit(0)

        # Get available backend
        backend = get_available_backend()
        if backend is None:
            logger.error("No window monitoring backend available")
            sys.exit(1)

        # Connect to daemon
        daemon = Daemon.connect(fallback=True)
        if daemon is None:
            logger.error("Failed to connect to input-remapper daemon")
            sys.exit(1)

        # Create and run service
        service = ProfileService(config, backend, daemon)

        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info("Received signal %s, shutting down", signum)
            sys.exit(0)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        try:
            asyncio.run(service.run())
        except KeyboardInterrupt:
            logger.info("Interrupted, shutting down")
            sys.exit(0)
        except Exception as e:
            logger.error("Service error: %s", str(e))
            sys.exit(1)


if __name__ == "__main__":
    InputRemapperProfileServiceBin.main()
