"""
reports.py — matplotlib balance chart, pandas summary stats, and CSV export.
Implemented in Sprint 5.
"""

import csv
import os
from datetime import date

from modules.utils import format_currency

_BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REPORTS_DIR = os.path.join(_BASE_DIR, 'reports')


def _ensure_reports_dir():
    os.makedirs(_REPORTS_DIR, exist_ok=True)


def _today():
    return date.today().strftime('%Y-%m-%d')


# ---------------------------------------------------------------------------
# Balance chart
# ---------------------------------------------------------------------------

def generate_balance_chart(account):
    """Generate a matplotlib line chart of balance over time.

    Plots balance_after for each transaction against transaction index.
    Saves the figure as reports/balance_chart_<account_id>_<date>.png via
    plt.savefig() — no display window is opened.

    Args:
        account (Account): Account to chart.

    Returns:
        str: Absolute path to the saved PNG, or None on error.
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
    except ImportError:
        print("  [Error] matplotlib is not installed. Run: pip install matplotlib")
        return None

    _ensure_reports_dir()

    txns = account.transactions
    if txns:
        x_indices = list(range(len(txns)))
        y_balances = [t['balance_after'] for t in txns]
        x_labels   = [
            f"{i + 1}. {t['type'][:4]}\n{t['timestamp'][:10]}"
            for i, t in enumerate(txns)
        ]
    else:
        x_indices  = [0]
        y_balances = [account.balance]
        x_labels   = ['Current Balance']

    fig, ax = plt.subplots(figsize=(max(8, len(x_indices) * 1.2), 5))
    ax.plot(x_indices, y_balances, marker='o', linewidth=2,
            color='steelblue', markersize=6)
    ax.fill_between(x_indices, y_balances, alpha=0.12, color='steelblue')

    ax.set_xticks(x_indices)
    ax.set_xticklabels(x_labels, rotation=30, ha='right', fontsize=8)
    ax.set_title(
        f"Balance Over Time\n"
        f"{account.account_type} Account [{account.account_id}]  |  "
        f"Owner: {account.owner}",
        fontsize=12, pad=10
    )
    ax.set_xlabel("Transaction", fontsize=10)
    ax.set_ylabel("Balance ($)", fontsize=10)
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"${v:,.2f}")
    )
    ax.grid(True, linestyle='--', alpha=0.4)
    fig.tight_layout()

    path = os.path.join(
        _REPORTS_DIR,
        f"balance_chart_{account.account_id}_{_today()}.png"
    )
    try:
        plt.savefig(path, dpi=150)
        plt.close(fig)
        return path
    except (OSError, PermissionError) as e:
        print(f"  [Error] Could not save chart: {e}")
        plt.close(fig)
        return None


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

def export_transactions_csv(account):
    """Export the account's full transaction history to a CSV file.

    Saves to reports/transactions_<account_id>_<date>.csv.

    Args:
        account (Account): Account whose history to export.

    Returns:
        str: Absolute path to the saved CSV, or None on error.
    """
    _ensure_reports_dir()
    path = os.path.join(
        _REPORTS_DIR,
        f"transactions_{account.account_id}_{_today()}.csv"
    )
    headers = ['txn_id', 'type', 'amount', 'timestamp', 'balance_after']
    try:
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(account.transactions)
        return path
    except PermissionError as e:
        print(f"  [Error] Could not write CSV: {e}")
        return None


# ---------------------------------------------------------------------------
# Pandas summary
# ---------------------------------------------------------------------------

def generate_summary(account):
    """Build a pandas DataFrame from transactions and display describe() stats.

    Args:
        account (Account): Account to summarize.

    Returns:
        pandas.DataFrame: The transaction DataFrame, or None on error.
    """
    try:
        import pandas as pd
    except ImportError:
        print("  [Error] pandas is not installed. Run: pip install pandas")
        return None

    if not account.transactions:
        print("  No transactions to summarize.")
        return None

    df = pd.DataFrame(account.transactions)
    df['amount']       = pd.to_numeric(df['amount'])
    df['balance_after'] = pd.to_numeric(df['balance_after'])

    W = 40
    sep = "  +" + "-" * W + "+"

    print()
    print(sep)
    print(f"  |{'TRANSACTION SUMMARY':^{W}}|")
    print(sep)
    print(f"  |  {'Account ID':<18}: {account.account_id:<{W - 22}}|")
    print(f"  |  {'Total Transactions':<18}: {len(df):<{W - 22}}|")
    type_counts = df['type'].value_counts()
    for txn_type, count in type_counts.items():
        label = f"  {txn_type}"
        print(f"  |  {label:<18}: {count:<{W - 22}}|")
    print(sep)

    print(f"  |{'NUMERIC STATISTICS':^{W}}|")
    print(sep)

    stats = df[['amount', 'balance_after']].describe()
    stat_labels = {
        'count': 'Count', 'mean': 'Mean', 'std': 'Std Dev',
        'min': 'Min', '25%': '25th pct', '50%': 'Median',
        '75%': '75th pct', 'max': 'Max',
    }
    for col in ['amount', 'balance_after']:
        col_label = 'AMOUNT' if col == 'amount' else 'BALANCE AFTER'
        print(f"  |  {col_label:<{W - 4}}|")
        for stat, label in stat_labels.items():
            val = stats.loc[stat, col]
            if stat == 'count':
                print(f"  |    {label:<14}: {int(val):<{W - 22}}|")
            else:
                print(f"  |    {label:<14}: {format_currency(val):<{W - 22}}|")
        print(sep)

    return df


# ---------------------------------------------------------------------------
# Account statement
# ---------------------------------------------------------------------------

def print_account_statement(account):
    """Print a formatted account statement to the terminal.

    Shows account header details followed by full transaction history
    in an ASCII table.

    Args:
        account (Account): Account to print.
    """
    # Header box
    HW = 50
    hsep = "  +" + "-" * HW + "+"

    def hrow(label, value=''):
        if value:
            return f"  |  {label:<20}{str(value):<{HW - 22}}|"
        return f"  |  {label:<{HW - 2}}|"

    print()
    print(hsep)
    print(f"  |{'ACCOUNT  STATEMENT':^{HW}}|")
    print(hsep)
    print(hrow("Account ID:", account.account_id))
    print(hrow("Type:", account.account_type))
    print(hrow("Owner:", account.owner))
    print(hrow("Current Balance:", format_currency(account.balance)))
    print(hrow("Transactions:", str(len(account.transactions))))
    print(hsep)

    if not account.transactions:
        print(hrow("No transaction history on record."))
        print(hsep)
        return

    # Transaction table — widths: 8 | 10 | 10 | 16 | 10
    C = [8, 10, 10, 16, 10]
    tsep = "  +" + "+".join("-" * (w + 2) for w in C) + "+"

    def trow(vals):
        cells = [f" {str(v):<{w}} " for v, w in zip(vals, C)]
        return "  |" + "|".join(cells) + "|"

    print(trow(["Txn ID", "Type", "Amount", "Date/Time", "Balance"]))
    print(tsep)
    for t in account.transactions:
        amt = f"${t['amount']:,.2f}"
        bal = f"${t['balance_after']:,.2f}"
        ts  = t['timestamp'][:16]
        print(trow([t['txn_id'], t['type'], amt, ts, bal]))
    print(tsep)
