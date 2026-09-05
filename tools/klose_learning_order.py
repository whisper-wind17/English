#!/usr/bin/env python3
"""Shared serialization contract for Klose curriculum LearningOrder."""
from __future__ import annotations

LEARNING_ORDER_WIDTH = 6
LEARNING_ORDER_MAX = 10**LEARNING_ORDER_WIDTH - 1


def format_learning_order(index: int) -> str:
    if index < 1 or index > LEARNING_ORDER_MAX:
        raise ValueError(
            f"LearningOrder index out of range: {index}; expected 1..{LEARNING_ORDER_MAX}"
        )
    return f"{index:0{LEARNING_ORDER_WIDTH}d}"


def is_valid_learning_order(value: str) -> bool:
    return (
        len(value) == LEARNING_ORDER_WIDTH
        and value.isdigit()
        and 1 <= int(value) <= LEARNING_ORDER_MAX
        and value == format_learning_order(int(value))
    )
