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
from cmdkit.logging import Logger, level_by_name, logging_styles, INFO
from cmdkit.config import Configuration

# Public interface
__all__ = [
    'PKGNAME', 'APPNAME', 'VERSION', 'VERSION_INFO',
    'cfg', 'log', 'set_verbose',
    'print_exception'
]


# Metadata
PKGNAME: Final[str] = 'onetrc'
APPNAME: Final[str] = '1trc'
VERSION: Final[str] = get_version(APPNAME)
VERSION_INFO: Final[str] = f'{APPNAME} v{VERSION} ({python_implementation()} {python_version()})'


# Global runtime configuration from environment variables
cfg = Configuration.from_local(env=True, prefix=PKGNAME.upper(), default={
    'log': {
        'level': 'warning',
        'style': 'default',
    },
    'build': {
        'samples': 10_000_000,
        'files': 1,
        'stdev': 10,
    },
})


log = Logger.default(name=APPNAME,
                     level=level_by_name[cfg.log.level.upper()],
                     **logging_styles.get(cfg.log.style.lower(), {}))


def set_verbose() -> None:
    """Set logging level to INFO."""
    log.setLevel(INFO)


def print_exception(exc: Exception, status: int) -> int:
    """Log `exc` and return `status`."""
    log.critical(str(exc))
    return status

