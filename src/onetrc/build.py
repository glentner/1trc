# SPDX-FileCopyrightText: 2025 Geoffrey Lentner
# SPDX-License-Identifier: MIT

"""Build measurement data for 1TRC."""


# Type annotations
from __future__ import annotations
from typing import Final

# Standard libs
import os
import sys

# External libs
from cmdkit.app import Application
from cmdkit.cli import Interface
from polars import DataFrame
from tqdm import tqdm
from numpy.random import default_rng

# Internal libs
from onetrc.data import STATION_DATA
from onetrc.config import cfg, log, set_verbose

# Public interface
__all__ = ['BuildMeasurements', ]


USAGE: Final[str] = f"""\
Usage:
  1trc build [-h] [-v | -p] [-o DIR] [-f FORMAT] [-n NUM] [-N NUM]
  {__doc__}\
"""

HELP: Final[str] = f"""\
{USAGE}

Options:
  -o, --output        DIR     Output directory (default: '.').
  -f, --format        FORMAT  Either CSV or PARQUET (default: CSV).
  -s, --stream-output         Write all data to <stdout> instead.
  -n, --num-samples   NUM     Rows per output file (default: 10M).
  -N, --num-files     NUM     Number of output files (default: 1).
  -v, --verbose               Show info level messages.
  -p, --progress              Show progress bar.
  -h, --help                  Show this message and exit.\
"""


# Configurable global parameters
DEFAULT_SAMPLES: Final[int] = int(cfg.build.samples)
DEFAULT_FILES: Final[int] = int(cfg.build.files)
DEFAULT_STDEV: Final[float] = float(cfg.build.stdev)


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

    stream_output: bool = False
    interface.add_argument('-s', '--stream-output', action='store_true')

    verbose_mode: bool = False
    progress_mode: bool = False
    notify_interface = interface.add_mutually_exclusive_group()
    notify_interface.add_argument('-v', '--verbose', action='store_true', dest='verbose_mode')
    notify_interface.add_argument('-p', '--progress', action='store_true', dest='progress_mode')

    def run(self: BuildMeasurements) -> None:
        """Run program."""
        if self.verbose_mode:
            set_verbose()
        rng = default_rng()
        data = DataFrame(STATION_DATA, ("station_name", "temperature"), orient="row")
        stream = sys.stdout if self.stream_output else None
        with self.progress_bar() as progress:
            for i in range(self.num_files):
                batch = data.sample(n=self.num_samples, with_replacement=True)
                batch = batch.with_columns(temperature=rng.normal(batch["temperature"], DEFAULT_STDEV))
                filepath = '<stdout>' if self.stream_output else self.build_filepath(i)
                log.info(f'Writing data ({self.num_samples}) to file ({filepath})')
                progress.set_description(os.path.basename(filepath))
                match self.output_format:
                    case 'csv':
                        batch.write_csv(stream or filepath, separator=';', float_precision=1, include_header=False)
                    case 'parquet':
                        batch.write_parquet(stream or filepath)
                progress.update(self.num_samples)

    def build_filepath(self: BuildMeasurements, i: int) -> str:
        """Left-pad file number."""
        return os.path.join(
            self.output_dir,
            'measurements-' + str(i).zfill(len(str(self.num_files))) + f'.{self.output_format}'
        )

    def progress_bar(self: BuildMeasurements) -> tqdm:
        """Build progress bar interface."""
        return tqdm(
            total=self.num_files * self.num_samples,
            unit='row',
            unit_scale=True,
            ascii=True,
            file=(sys.stderr if self.progress_mode else open(os.devnull, 'w')),
        )