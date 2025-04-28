# SPDX-FileCopyrightText: 2025 Geoffrey Lentner
# SPDX-License-Identifier: MIT

"""Basic implementation with duckdb."""


# Type annotations
from __future__ import annotations
from typing import List, Final, Dict, IO, Callable, Optional

# Standard libs
import sys

# External libs
from cmdkit.cli import Interface
import duckdb

# Internal libs
from onetrc.solutions.interface import Solution

# Public interface
__all__ = ['DuckdbBasic', ]


NAME: Final[str] = 'duckdb-basic'
DESC: Final[str] = str(__doc__)
USAGE: Final[str] = f"""\
Usage:
  1trc run {NAME} [-h] <filepattern> [-p] [--merge] [-f FORMAT] [-o PATH] 
           {' '*len(NAME)} [--set ARGS...] [--pragma ARGS...]

  {__doc__}\
"""

HELP: Final[str] = f"""
{USAGE}

Options:
  -p, --parquet            Switch to parquet format.
  -o, --output   PATH      Write output to PATH (default: <stdout>).
  -f, --format   FORMAT    Format output (default: normal).
      --csv                Format output as CSV.
      --json               Format output as JSON.
      --parquet            Format output as Parquet.
      --merge              Merge partitioned output data.
  -s, --set      ARGS...   Query settings in param=value pairs.
      --pragma   ARGS...   Query pragmas.
  -h, --help               Show this message and exit.
  
Settings:
  threads=4                Set number of threads to 4.
  memory_limit=8GB         Set memory limit to 8GB.
  enable_profiling=json    Alter format of profiling output.
  profiling_output=PATH    Some PATH to write profiling output.
  
Pragmas:
  enable_profiling         Enable profiling on query.
  enable_progress_bar      Show progress bar when running queries.
  disable_progress_bar     Disable progress bar when running queries.

See https://duckdb.org/docs/stable/configuration/pragmas.html
for more information on duckdb settings and pragmas.\
"""


class DuckdbBasic(Solution):
    """Basic duckdb implementation."""

    name: str = NAME
    desc: str = DESC
    mode: str = 'filepattern'

    interface = Interface(f'1trc run {NAME}', USAGE, HELP)

    filepattern: str = 'measurements.txt'
    interface.add_argument('filepattern')

    parquet_mode: bool = False
    interface.add_argument('-p', '--from-parquet', action='store_true', dest='parquet_mode')

    print_format: str = 'normal'
    print_formats: List[str] = ['normal', 'csv', 'json', 'parquet']
    print_interface = interface.add_mutually_exclusive_group()
    print_interface.add_argument('-f', '--format', dest='print_format', default=print_format, choices=print_formats)
    print_interface.add_argument('--csv', action='store_const', dest='print_format', const='csv')
    print_interface.add_argument('--json', action='store_const', dest='print_format', const='json')
    print_interface.add_argument('--parquet', action='store_const', dest='print_format', const='parquet')

    output_filename: str = '-'
    interface.add_argument('-o', '--output', default=output_filename, dest='output_filename')

    pragmas: List[str] = []
    interface.add_argument('--pragma', nargs='+', dest='pragmas')

    settings: List[str] = []
    interface.add_argument('-s', '--set', nargs='+', dest='settings')

    merge_mode = False
    interface.add_argument('--merge', action='store_true', dest='merge_mode')

    def run(self: DuckdbBasic) -> None:
        """Query with duckdb."""
        if not self.merge_mode:
            sql = SQL_PART_CSV if not self.parquet_mode else SQL_PART_PARQUET
        else:
            sql = SQL_MERGE_CSV if not self.parquet_mode else SQL_MERGE_PARQUET
        query = run_query(self.filepattern, sql, pragmas=self.pragmas, settings=self.settings)
        self.print_output(query)

    def print_output(self: DuckdbBasic, query: duckdb.DuckDBPyRelation) -> None:
        """Print query results."""
        formatter = PRINT_MODE[self.print_format]
        if self.output_filename == '-':
            formatter(query)
        else:
            with open(self.output_filename, mode='wb') as stream:
                formatter(query, stream=stream)


SQL_PART_CSV: Final[str] = """
{pragmas}
{settings}

SELECT
    station_name,
    COUNT(temperature) AS station_count,
    MIN(temperature) AS temp_min,
    MAX(temperature) AS temp_max,
    CAST(AVG(temperature) AS DECIMAL(8,1)) AS temp_mean
FROM READ_CSV('{filepattern}', header=false, columns={{'station_name':'TEXT','temperature':'double'}}, delim=';')
GROUP BY station_name
ORDER BY station_name;
"""


SQL_PART_PARQUET: Final[str] = """
{pragmas}
{settings}

SELECT
    station_name,
    COUNT(temperature) AS station_count,
    MIN(temperature) AS temp_min,
    MAX(temperature) AS temp_max,
    CAST(AVG(temperature) AS DECIMAL(8,1)) AS temp_mean
FROM READ_PARQUET('{filepattern}')
GROUP BY station_name
ORDER BY station_name;
"""


SQL_MERGE_CSV: Final[str] = """
{pragmas}
{settings}

SELECT
    station_name,
    CAST(SUM(station_count) AS INTEGER) AS station_count,
    MIN(temp_min) AS temp_min,
    MAX(temp_max) AS temp_max,
    CAST(SUM(temp_mean * station_count)/SUM(station_count) AS DECIMAL(8,1)) AS temp_mean,
FROM READ_CSV('{filepattern}')
GROUP BY station_name
ORDER BY station_name;
"""


SQL_MERGE_PARQUET: Final[str] = """
{pragmas}
{settings}

SELECT
    station_name,
    CAST(SUM(station_count) AS INTEGER) AS station_count,
    MIN(temp_min) AS temp_min,
    MAX(temp_max) AS temp_max,
    CAST(SUM(temp_mean * station_count)/SUM(station_count) AS DECIMAL(8,1)) AS temp_mean,
FROM READ_PARQUET('{filepattern}')
GROUP BY station_name
ORDER BY station_name;
"""


def run_query(
        filepattern: str,
        query: str = SQL_PART_CSV,
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


def print_normal(query: duckdb.DuckDBPyRelation, stream: IO = sys.stdout) -> None:
    """Print query results in normal format."""
    print(query.df().to_string(index=False, float_format='%.1f'), file=stream)


def print_csv(query: duckdb.DuckDBPyRelation, stream: IO = sys.stdout) -> None:
    """Print query results in CSV format."""
    query.df().to_csv(path_or_buf=stream, index=False, sep=',', float_format='%.1f')


def print_json(query: duckdb.DuckDBPyRelation, stream: IO = sys.stdout) -> None:
    """Print query results in JSON format."""
    query.df().to_json(path_or_buf=stream, orient='records', double_precision=1, force_ascii=False)


def print_parquet(query: duckdb.DuckDBPyRelation, stream: IO = sys.stdout) -> None:
    """Print query results in Parquet format."""
    query.df().to_parquet(stream)


PRINT_MODE: Dict[str, Callable[[duckdb.DuckDBPyRelation, Optional[IO]], None]] = {
    'normal': print_normal,
    'csv': print_csv,
    'json': print_json,
    'parquet': print_parquet,
}
