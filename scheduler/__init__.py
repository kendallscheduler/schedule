"""
AutoScheduler — Residency Master Schedule constraint-based scheduler.
Uses OR-Tools CP-SAT to assign rotations while enforcing coverage and policy constraints.

Single-workbook workflow: the workbook IS the source of truth.
"""

__version__ = "2.0.0"
