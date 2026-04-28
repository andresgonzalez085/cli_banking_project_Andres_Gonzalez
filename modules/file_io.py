"""
file_io.py — JSON persistence, CSV transaction log, and audit logging.
Implemented in Sprint 4.
"""

import csv
import json
import os
from datetime import datetime

from modules.accounts import CheckingAccount, SavingsAccount

_BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR   = os.path.join(_BASE_DIR, 'data')
_JSON_FILE  = os.path.join(_DATA_DIR, 'accounts.json')
_CSV_FILE   = os.path.join(_DATA_DIR, 'transactions.csv')
_AUDIT_FILE = os.path.join(_DATA_DIR, 'audit.log')

_CSV_HEADERS = [
    'timestamp', 'txn_id', 'username', 'account_id',
    'type', 'amount', 'balance_after',
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ensure_data_dir():
    """Create the data/ directory if it does not already exist."""
    os.makedirs(_DATA_DIR, exist_ok=True)


def _account_to_dict(acc):
    """Serialize an Account subclass to a JSON-compatible dict."""
    d = {
        "account_id": acc.account_id,
        "owner": acc.owner,
        "account_type": acc.account_type,
        "balance": acc.balance,
        "transactions": acc.transactions,
    }
    if isinstance(acc, CheckingAccount):
        d["overdraft_limit"] = acc.overdraft_limit
    elif isinstance(acc, SavingsAccount):
        d["monthly_withdrawal_limit"] = acc.monthly_withdrawal_limit
        d["withdrawals_this_month"] = acc._withdrawals_this_month
    return d


def _dict_to_account(d):
    """Reconstruct an Account subclass from a persisted JSON dict."""
    if d.get("account_type") == "Checking":
        acc = CheckingAccount(
            d["account_id"], d["owner"],
            initial_balance=d["balance"],
            overdraft_limit=d.get("overdraft_limit", 500.0),
        )
    else:
        acc = SavingsAccount(
            d["account_id"], d["owner"],
            initial_balance=d["balance"],
            monthly_withdrawal_limit=d.get("monthly_withdrawal_limit", 6),
        )
        acc._withdrawals_this_month = d.get("withdrawals_this_month", 0)
    acc.transactions = d.get("transactions", [])
    return acc


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def save_accounts(username, accounts):
    """Serialize accounts and write to accounts.json.

    Other users' records in the file are preserved unchanged.
    Wraps all file operations in try/except with friendly error messages.

    Args:
        username (str): Owner whose accounts are being saved.
        accounts (dict): Mapping of account_id -> Account instance.
    """
    _ensure_data_dir()

    # Read existing file to preserve other users' data.
    try:
        with open(_JSON_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"users": {}, "accounts": {}}
    except json.JSONDecodeError as e:
        print(f"  [Warning] accounts.json was corrupt and will be rebuilt: {e}")
        data = {"users": {}, "accounts": {}}
    except PermissionError as e:
        print(f"  [Error] Cannot read accounts.json — save aborted: {e}")
        return

    # Replace this user's records with current in-memory state.
    data["accounts"] = {
        k: v for k, v in data["accounts"].items()
        if v.get("owner") != username
    }
    for acc_id, acc in accounts.items():
        data["accounts"][acc_id] = _account_to_dict(acc)

    try:
        with open(_JSON_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except PermissionError as e:
        print(f"  [Error] Cannot write accounts.json: {e}")


def load_accounts(username):
    """Read accounts.json and reconstruct Account objects owned by username.

    Returns an empty dict on missing file, corrupt JSON, or permission error,
    printing a friendly message in the latter two cases.

    Args:
        username (str): Logged-in user whose accounts to load.

    Returns:
        dict: Mapping of account_id -> Account instance.
    """
    accounts = {}
    try:
        with open(_JSON_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return accounts
    except json.JSONDecodeError as e:
        print(f"  [Warning] accounts.json is corrupt; starting with no accounts: {e}")
        return accounts
    except PermissionError as e:
        print(f"  [Error] Cannot read accounts.json: {e}")
        return accounts

    for acc_dict in data.get("accounts", {}).values():
        if acc_dict.get("owner") == username:
            try:
                acc = _dict_to_account(acc_dict)
                accounts[acc.account_id] = acc
            except (KeyError, TypeError, ValueError) as e:
                print(f"  [Warning] Skipping malformed account record: {e}")

    return accounts


def append_transaction_csv(username, account_id, txn):
    """Append one transaction row to data/transactions.csv in real time.

    Writes the header row if the file does not yet exist.
    Wraps all file operations in try/except with friendly error messages.

    Args:
        username (str): Account owner.
        account_id (str): The account that was affected.
        txn (dict): Transaction dict with keys txn_id, type, amount,
                    timestamp, balance_after.
    """
    _ensure_data_dir()
    write_header = not os.path.exists(_CSV_FILE)
    try:
        with open(_CSV_FILE, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_HEADERS)
            if write_header:
                writer.writeheader()
            writer.writerow({
                'timestamp':     txn['timestamp'],
                'txn_id':        txn['txn_id'],
                'username':      username,
                'account_id':    account_id,
                'type':          txn['type'],
                'amount':        f"{txn['amount']:.2f}",
                'balance_after': f"{txn['balance_after']:.2f}",
            })
    except PermissionError as e:
        print(f"  [Warning] Could not write transactions.csv: {e}")
    except (KeyError, ValueError) as e:
        print(f"  [Warning] Malformed transaction record — CSV row skipped: {e}")


def write_audit(username, event_type, details):
    """Append one timestamped line to data/audit.log.

    Used by auth.py for LOGIN/LOGOUT events and by transactions.py for
    every financial operation.

    Args:
        username (str): User performing the action.
        event_type (str): Event label (e.g. LOGIN, LOGOUT, DEPOSIT).
        details (str): Extra context (account IDs, amounts, etc.).
    """
    _ensure_data_dir()
    timestamp = datetime.now().isoformat(timespec='seconds')
    line = f"[{timestamp}] user={username} type={event_type} {details}\n"
    try:
        with open(_AUDIT_FILE, 'a') as f:
            f.write(line)
    except PermissionError as e:
        print(f"  [Warning] Could not write audit.log: {e}")
