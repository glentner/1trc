# SPDX-FileCopyrightText: 2025 Geoffrey Lentner
# SPDX-License-Identifier: MIT

"""One Trillion Row Challenge."""


# Type annotations
from __future__ import annotations
from typing import List, Final

# Standard libs
import sys
from platform import python_implementation, python_version
from importlib.metadata import version as get_version

# External libs
from cmdkit.logging import Logger, level_by_name, logging_styles
from cmdkit.app import Application, ApplicationGroup
from cmdkit.cli import Interface
from cmdkit.config import Configuration

# Internal libs
from onetrc.build import BuildMeasurements

# Public interface
__all__ = ['main', ]

# Metadata
PKGNAME: Final[str] = 'onetrc'
APPNAME: Final[str] = '1trc'
VERSION: Final[str] = get_version(APPNAME)
VERSION_INFO: Final[str] = f'{APPNAME} v{VERSION} ({python_implementation()} {python_version()})'


# Global runtime configuration from environment variables
cfg = Configuration.from_local(env=True, prefix=PKGNAME.upper(), default={
    'log': {
        'level': 'info',
        'style': 'default',
    },
})


log = Logger.default(name=APPNAME,
                     level=level_by_name[cfg.log.level.upper()],
                     **logging_styles.get(cfg.log.style.lower(), {}))


def print_exception(exc: Exception, status: int) -> int:
    """Log `exc` and return `status`."""
    log.critical(str(exc))
    return status


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