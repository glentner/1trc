# SPDX-FileCopyrightText: 2025 Geoffrey Lentner
# SPDX-License-Identifier: MIT

"""Naive SQL implementation."""


# Type annotations
from __future__ import annotations
from typing import List, Final, Type

# Standard libs
import os
import sys

# External libs
from cmdkit.cli import Interface
import duckdb

# Internal libs
from onetrc.config import log
from onetrc.solutions.interface import Solution

# Public interface
__all__ = ['DuckdbBasic', ]


NAME: Final[str] = 'duckdb-basic'
USAGE: Final[str] = f"""\
Usage:
  1trc run {NAME} [-h] [-p] <filepattern>
  {__doc__}\
"""

HELP: Final[str] = f"""
{USAGE}

Options:
  -s, --set      ARGS...   Set param=value pairs.
      --pragma   ARGS...   Set pragmas for query.
  -p, --parquet            Switch to parquet format.
      --print              Print query results to <stdout>.
  -h, --help               Show this message and exit.
  
Settings:
  threads=4               Set number of threads to 4.
  memory_limit=8GB        Set memory limit to 8GB.
  enable_profiling=json   Alter format of profiling output.
  profiling_output=PATH   Some PATH to write profiling output.
  
Pragmas:
  enable_profiling        Enable profiling on query.
  enable_progress_bar     Show progress bar when running queries.
  disable_progress_bar    Disable progress bar when running queries.

See https://duckdb.org/docs/stable/configuration/pragmas.html
for more information on duckdb settings and pragmas.
"""


class DuckdbBasic(Solution):
    """Solution interface includes timing and metadata management."""

    name: str = 'duckdb-basic'
    desc: str = __doc__
    mode: str = 'filepattern'

    interface = Interface(f'1trc run {NAME}', USAGE, HELP)

    filepattern: str = 'measurements.txt'
    interface.add_argument('filepattern')

    parquet_mode: bool = False
    interface.add_argument('-p', '--parquet', action='store_true', dest='parquet_mode')

    print_mode: bool = False
    interface.add_argument('--print', action='store_true', dest='print_mode')

    pragmas: List[str] = []
    interface.add_argument('--pragma', nargs='+', dest='pragmas')

    settings: List[str] = []
    interface.add_argument('-s', '--set', nargs='+', dest='settings')

    def run(self: DuckdbBasic) -> None:
        """Query with duckdb."""
        query = run_query(self.filepattern, SQL_CSV if not self.parquet_mode else SQL_PARQUET,
                          pragmas=self.pragmas, settings=self.settings)
        print(repr(query), file=(sys.stdout if self.print_mode else open(os.devnull, 'w')))


SQL_CSV = """
{pragmas}
{settings}

SELECT
    station_name,
    MIN(temperature) as min_temperature,
    MAX(temperature) as max_temperature,
    CAST(AVG(temperature) AS DECIMAL(8,1)) AS mean_temperature
FROM READ_CSV('{filepattern}', header=false, columns={{'station_name':'TEXT','temperature':'double'}}, delim=';')
GROUP BY station_name;
"""


SQL_PARQUET = """
{pragmas}
{settings}

SELECT
    station_name,
    MIN(temperature) as min_temperature,
    MAX(temperature) as max_temperature,
    CAST(AVG(measurement) AS DECIMAL(8,1)) AS mean_temperature
FROM READ_PARQUET('{filepattern}')
GROUP BY station_name;
"""


def run_query(
        filepattern: str,
        query: str = SQL_CSV,
        pragmas: List[str] | None = None,
        settings: List[str] | None = None) -> duckdb.DuckDBPyRelation:
    """Execute SQL query against target filepattern."""
    return duckdb.query(
        query.format(
            filepattern=filepattern,
            pragmas='\n'.join([f'PRAGMA {value};' for value in (pragmas or [])]),
            settings='\n'.join([f'SET {key} = {smart_format_value(value)};'
                                for key, value in parse_settings_args(settings).items()]),
        )
    )


def smart_format_value(value: str) -> str:
    """Apply single-quotes if text value."""
    try:
        return str(int(value))
    except ValueError:
        return f"'{value}'"


def parse_settings_args(settings: List[str] | None) -> Dict[str, str]:
    """Parse command-line arguments for settings."""
    out = {}
    for arg in (settings or []):
        key, value = arg.split('=', 1)
        out[key] = value
    return out
