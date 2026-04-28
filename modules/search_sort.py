"""
search_sort.py — Linear/binary search and bubble sort on transaction lists.
Implemented in Sprint 5.
"""

# ---------------------------------------------------------------------------
# ASCII table display
# ---------------------------------------------------------------------------

# Fixed column widths (inner content, excluding padding and pipes)
_COLS = [
    ('txn_id',       'Txn ID',     8),
    ('type',         'Type',      10),
    ('amount',       'Amount',    10),
    ('timestamp',    'Date/Time', 16),
    ('balance_after','Balance',   10),
]


def _sep():
    return '  +' + '+'.join('-' * (w + 2) for _, _, w in _COLS) + '+'


def _row(values):
    cells = [f" {str(v):<{w}} " for v, (_, _, w) in zip(values, _COLS)]
    return '  |' + '|'.join(cells) + '|'


def print_results(transactions):
    """Print a list of transaction dicts as a formatted ASCII table.

    Args:
        transactions (list[dict]): Records to display.
    """
    if not transactions:
        print("  (no results)")
        return

    print()
    print(_sep())
    print(_row([label for _, label, _ in _COLS]))
    print(_sep())
    for t in transactions:
        amt = f"${t['amount']:,.2f}"
        bal = f"${t['balance_after']:,.2f}"
        ts  = t['timestamp'][:16]          # trim seconds for width
        print(_row([t['txn_id'], t['type'], amt, ts, bal]))
    print(_sep())
    print(f"  {len(transactions)} result(s)")
    print()


# ---------------------------------------------------------------------------
# Search functions
# ---------------------------------------------------------------------------

def linear_search(transactions, query):
    """Search transactions by txn_id (exact) or type keyword (case-insensitive).

    Iterates every element — O(n). Works on unsorted lists.

    Args:
        transactions (list[dict]): Transaction records to search.
        query (str): Matched against txn_id exactly (upper-cased) or as a
                     case-insensitive substring of the type field.

    Returns:
        list[dict]: All matching transaction records.
    """
    q_upper = query.upper()
    q_lower = query.lower()
    results = []
    for t in transactions:
        if t['txn_id'] == q_upper or q_lower in t['type'].lower():
            results.append(t)
    return results


def binary_search(transactions, amount):
    """Binary search for all transactions whose amount equals the target.

    The caller MUST pass a list already sorted by amount ascending; this
    function asserts that precondition before searching.

    Args:
        transactions (list[dict]): Records sorted by amount ascending.
        amount (float): Target dollar amount.

    Returns:
        list[dict]: All records whose amount matches (may be multiple).

    Raises:
        AssertionError: If transactions is not sorted by amount ascending.
    """
    for i in range(len(transactions) - 1):
        assert transactions[i]['amount'] <= transactions[i + 1]['amount'], (
            "binary_search requires a list sorted by amount ascending. "
            "Call sorted_by_amount() first."
        )

    lo, hi = 0, len(transactions) - 1
    hit = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        mid_amt = transactions[mid]['amount']
        if mid_amt == amount:
            hit = mid
            break
        elif mid_amt < amount:
            lo = mid + 1
        else:
            hi = mid - 1

    if hit == -1:
        return []

    # Expand left and right to collect all records with the same amount.
    results = [transactions[hit]]
    i = hit - 1
    while i >= 0 and transactions[i]['amount'] == amount:
        results.append(transactions[i])
        i -= 1
    i = hit + 1
    while i < len(transactions) and transactions[i]['amount'] == amount:
        results.append(transactions[i])
        i += 1
    return results


# ---------------------------------------------------------------------------
# Sort functions
# ---------------------------------------------------------------------------

def bubble_sort(transactions, key='date', reverse=False):
    """Sort transactions using bubble sort; returns a new list.

    key='date' compares the ISO-8601 timestamp strings directly —
    lexicographic order equals chronological order for that format.

    Args:
        transactions (list[dict]): Records to sort.
        key (str): Sort key — only 'date' (timestamp) is supported.
        reverse (bool): False (default) → ascending; True → descending.

    Returns:
        list[dict]: New sorted list; original is unchanged.
    """
    result = list(transactions)
    n = len(result)
    for i in range(n):
        swapped = False
        for j in range(n - 1 - i):
            a = result[j]['timestamp']
            b = result[j + 1]['timestamp']
            should_swap = (a > b) if not reverse else (a < b)
            if should_swap:
                result[j], result[j + 1] = result[j + 1], result[j]
                swapped = True
        if not swapped:
            break
    return result


def sorted_by_amount(transactions, reverse=False):
    """Return a new list of transactions sorted by amount using sorted().

    Args:
        transactions (list[dict]): Records to sort.
        reverse (bool): False (default) → ascending; True → descending.

    Returns:
        list[dict]: New sorted list; original is unchanged.
    """
    return sorted(transactions, key=lambda t: t['amount'], reverse=reverse)
