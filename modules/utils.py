"""
utils.py — Utility helper functions.
Stubs created in Sprint 1; full implementation in Sprint 6.
"""

import uuid
import os


def format_currency(amount):
    """Return amount formatted as a USD currency string, e.g. '$1,234.56'."""
    return f"${amount:,.2f}"


def validate_amount(input_str):
    """Validate that input_str is a positive number. Raises ValueError if not."""
    value = float(input_str)
    if value <= 0:
        raise ValueError("Amount must be greater than zero.")
    return value


def clear_screen():
    """Clear the terminal screen (cross-platform)."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_table(headers, rows):
    """Render a formatted ASCII table to the terminal."""
    pass  # TODO: implement in Sprint 6


def generate_id():
    """Return a short unique alphanumeric ID using uuid."""
    return uuid.uuid4().hex[:8].upper()
