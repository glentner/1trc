# SPDX-FileCopyrightText: 2025 Geoffrey Lentner
# SPDX-License-Identifier: MIT

"""One Trillion Row Challenge."""


# Type annotations
from __future__ import annotations
from typing import List, Final

# Standard libs
import sys

# External libs
from cmdkit.app import Application, ApplicationGroup
from cmdkit.cli import Interface

# Internal libs
from onetrc.config import APPNAME, VERSION_INFO, cfg, log, set_verbose, print_exception
from onetrc.build import BuildMeasurements

# Public interface
__all__ = ['main', ]


USAGE: Final[str] = f"""\
Usage:
  1trc [-hv]
  {__doc__}\
"""

HELP: Final[str] = f"""\
{USAGE}

Commands:
  build                 Create measurement data.
  run                   Run solution.

Options:
  -v, --version         Show version and exit.
  -h, --help            Show this message and exit.
"""

Application.log_critical = log.critical
Application.log_exception = log.exception


class App(ApplicationGroup):
    """Application interface for `1trc` program."""

    interface = Interface(APPNAME, USAGE, HELP)
    interface.add_argument('-v', '--version', action='version', version=VERSION_INFO)
    interface.add_argument('command')

    commands = {
        'build': BuildMeasurements,
    }


def main(argv: List[str] | None = None) -> int:
    """Entry-point for `1trc` program."""
    return App.main(argv or sys.argv[1:])