"""Physical-to-QEC adapter for temporal filtering experiments."""

from .physics import EventTable, PhysicalParameters, event_table
from .qec import LogicalEstimate, simulate_logical_error

__all__ = [
    "EventTable",
    "PhysicalParameters",
    "event_table",
    "LogicalEstimate",
    "simulate_logical_error",
]
