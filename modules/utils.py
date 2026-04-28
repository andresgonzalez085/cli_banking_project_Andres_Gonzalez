"""
utils.py — Shared utility helpers used across all modules.
Implemented in Sprint 1; print_table completed in Sprint 6.
"""

import os
import uuid


def format_currency(amount):
    """Format a numeric amount as a USD currency string.

    Args:
        amount (float): Dollar amount to format (may be negative for overdraft).

    Returns:
        str: Formatted string with commas and two decimal places,
            e.g. '$1,234.56' or '-$50.00'.
    """
    return f"${amount:,.2f}"


def validate_amount(input_str):
    """Parse and validate that input_str represents a positive dollar amount.

    Args:
        input_str (str): Raw text entered by the user.

    Returns:
        float: The validated positive amount.

    Raises:
        ValueError: If input_str cannot be converted to float, or the
            resulting value is not strictly positive.
    """
    value = float(input_str)
    if value <= 0:
        raise ValueError("Amount must be greater than zero.")
    return value


def clear_screen():
    """Clear the terminal screen using the OS-appropriate command.

    Uses 'cls' on Windows (os.name == 'nt') and 'clear' on Unix/macOS.
    """
    os.system('cls' if os.name == 'nt' else 'clear')


def print_table(headers, rows):
    """Render a formatted ASCII table to the terminal.

    Column widths are calculated automatically as the maximum of each
    header's length and the longest value in the same column. An empty
    rows list still prints the header and borders.

    Args:
        headers (list[str]): Column header labels.
        rows (list[list]): Data rows; each inner list must have the same
            number of elements as headers. Non-string values are
            converted with str() before rendering.

    Example::

        print_table(
            ['Name', 'Balance'],
            [['Alice', '$500.00'], ['Bob', '$1,200.00']],
        )

        +---------+------------+
        | Name    | Balance    |
        +---------+------------+
        | Alice   | $500.00    |
        | Bob     | $1,200.00  |
        +---------+------------+
    """
    if not headers:
        return

    str_rows = [[str(cell) for cell in row] for row in rows]
    widths = [
        max(len(h), max((len(r[i]) for r in str_rows), default=0))
        for i, h in enumerate(headers)
    ]

    sep = '+' + '+'.join('-' * (w + 2) for w in widths) + '+'

    def fmt_row(vals):
        cells = [f' {str(v):<{w}} ' for v, w in zip(vals, widths)]
        return '|' + '|'.join(cells) + '|'

    print(sep)
    print(fmt_row(headers))
    print(sep)
    for row in str_rows:
        print(fmt_row(row))
    print(sep)


def generate_id():
    """Generate a short unique alphanumeric identifier using UUID4.

    Takes the first 8 hex characters of a random UUID and uppercases them,
    producing an ID with 16^8 ≈ 4.3 billion possible values.

    Returns:
        str: 8-character uppercase alphanumeric ID, e.g. 'A1B2C3D4'.
    """
    return uuid.uuid4().hex[:8].upper()
