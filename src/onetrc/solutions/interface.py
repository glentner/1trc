# SPDX-FileCopyrightText: 2025 Geoffrey Lentner
# SPDX-License-Identifier: MIT

"""Solution implementation interface."""


# Type annotations
from __future__ import annotations
from types import TracebackType

# Standard libs
from abc import ABC, abstractmethod, abstractproperty
from time import perf_counter
from datetime import timedelta

# External libs
from cmdkit.app import Application

# Internal libs
from onetrc.config import log, set_verbose

# Public interface
__all__ = ['Solution', ]


class Solution(Application, ABC):
    """Solution interface includes timing and metadata management."""

    t_start: perf_counter
    t_stop: perf_counter

    name: str = '?'
    desc: str = '?'
    mode: str = '?'

    def __enter__(self: Solution) -> Solution:
        """Initialize timer."""
        set_verbose()
        self.mode = getattr(self, self.mode, '?')
        log.info(f'Starting {self.name} on \'{self.mode}\'')
        self.t_start = perf_counter()
        return self

    def __exit__(self: Solution, exc_type: Exception, exc_value: Exception, traceback: TracebackType) -> None:
        """Report on performance."""
        self.t_stop = perf_counter()
        elapsed = timedelta(seconds=(self.t_stop - self.t_start))
        log.info(f'Completed {self.name} in {elapsed}')
