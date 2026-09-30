"""Concrete processors. To add one: write a subclass of ``Processor`` (or
``WindowedProcessor``) in this package and list it in :func:`default_processors`.
"""

from app.processing.base import Processor
from app.processing.processors.heart_rate import HeartRateStatsProcessor
from app.processing.processors.spo2 import SpO2StatsProcessor


def default_processors() -> list[Processor]:
    return [HeartRateStatsProcessor(), SpO2StatsProcessor()]


__all__ = ["HeartRateStatsProcessor", "SpO2StatsProcessor", "default_processors"]
