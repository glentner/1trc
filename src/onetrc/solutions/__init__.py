# SPDX-FileCopyrightText: 2025 Geoffrey Lentner
# SPDX-License-Identifier: MIT

"""Run given solution to the challenge."""


# Type annotations
from __future__ import annotations
from typing import Final

# External libs
from cmdkit.app import Application, ApplicationGroup
from cmdkit.cli import Interface

# Internal libs
from onetrc.config import APPNAME
from onetrc.solutions.duckdb_basic import DuckdbBasic

# Public interface
__all__ = ['SolutionGroup', ]


USAGE: Final[str] = f"""\
Usage:
  1trc run [-h] <solution> <filepattern> [--parquet] [--print] ...
  {__doc__}\
"""

HELP: Final[str] = f"""\
{USAGE}

Solutions:
  duckdb-basic          {DuckdbBasic.desc}

Options:
  -h, --help            Show this message and exit.\
"""


class SolutionGroup(ApplicationGroup):
    """Application interface for `1trc run` program."""

    interface = Interface(APPNAME, USAGE, HELP)
    interface.add_argument('command')

    commands = {
        'duckdb-basic': DuckdbBasic,
    }
