# SPDX-FileCopyrightText: 2025 Geoffrey Lentner
# SPDX-License-Identifier: MIT

"""Build measurement data for 1TRC."""


# Type annotations
from __future__ import annotations
from typing import List, Final, Tuple

# Standard libs
import os

# External libs
from cmdkit.logging import Logger, level_by_name, logging_styles
from cmdkit.app import Application, ApplicationGroup
from cmdkit.cli import Interface
from polars import DataFrame
from numpy.random import default_rng

# Internal libs
from onetrc.data import CITY_AVERAGES

# Public interface
__all__ = ['BuildMeasurements', ]

# Logging
log = Logger.with_name(__name__)


USAGE: Final[str] = f"""\
Usage:
  1trc build [-h] [-o DIR] [-f FORMAT] [-n NUM] [-N NUM]
  {__doc__}\
"""

HELP: Final[str] = f"""\
{USAGE}

Options:
  -o, --output        DIR     Output directory (default: '.').
  -f, --format        FORMAT  Either CSV or PARQUET (default: CSV).
  -n, --num-samples   NUM     Rows per output file (default: 10M).
  -N, --num-files     NUM     Number of output files (default: 1).
  -h, --help                  Show this message and exit.
"""


# Configurable global parameters
DEFAULT_SAMPLES: Final[int] = int(os.getenv('ONETRC_SAMPLES', 10_000_000))
DEFAULT_FILES: Final[int] = int(os.getenv('ONETRC_FILES', 1))
DEFAULT_STDEV: Final[float] = float(os.getenv('ONETRC_STDEV', 10))


class BuildMeasurements(Application):
    """Application interface for `1trc build` subcommand."""

    interface = Interface('1trc build', USAGE, HELP)

    output_dir: str = '.'
    interface.add_argument('-o', '--output', default=output_dir, dest='output_dir')

    output_format: str = 'csv'
    interface.add_argument('-f', '--format', default=output_format, dest='output_format',
                           type=str.lower, choices=['csv', 'parquet', 'CSV', 'PARQUET'])

    num_samples: int = DEFAULT_SAMPLES
    interface.add_argument('-n', '--num-samples', type=int, default=num_samples)

    num_files: int = DEFAULT_FILES
    interface.add_argument('-N', '--num-files', type=int, default=num_files)

    def run(self: BuildMeasurements) -> None:
        """Run program."""
        rng = default_rng()
        data = DataFrame(CITY_AVERAGES, ("name", "temperature"), orient="row")
        for i in range(self.num_files):
            batch = data.sample(n=self.num_samples, with_replacement=True)
            batch = batch.with_columns(temperature=rng.normal(batch["temperature"], 10))
            filepath = self.build_filepath(i)
            log.info(f'Building measurements ({self.num_samples}) for file {filepath}')
            match self.output_format:
                case 'csv':
                    batch.write_csv(filepath, separator=';', float_precision=1, include_header=False)
                case 'parquet':
                    batch.write_parquet(filepath)

    def build_filepath(self: BuildMeasurements, i: int) -> str:
        """Left-pad file number."""
        return os.path.join(
            self.output_dir,
            'measurements-' + str(i).zfill(len(str(self.num_files))) + f'.{self.output_format}'
        )