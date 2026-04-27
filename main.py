"""
main.py — Application entry point for the CLI Banking Application.
Run with: python main.py
"""

import json
import os

import modules.auth as auth
from modules.accounts import CheckingAccount, SavingsAccount
from modules.utils import clear_screen, format_currency, generate_id

_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          'data', 'accounts.json')

# Session-level account registry: account_id -> Account instance.
# Populated on login, cleared on logout.
# Sprint 4 (file_io.py) will absorb the persistence helpers below.
_accounts = {}


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

def _make_banner():
    """Build the welcome banner with perfect box alignment."""
    W = 54
    border = '+' + '=' * W + '+'
    blank  = '|' + ' ' * W + '|'

    def row(text=''):
        return '|' + text.ljust(W) + '|'

    # "AG Bank" in figlet small font — trailing space on last line avoids
    # the raw-string-cannot-end-in-backslash restriction.
    art = [
        "    _      ____    ____              _    ",
        r"   / \    / ___|  | __ )  __ _ _ __ | | __",
        r"  / _ \  | |  _   |  _ \ / _` | '_ \| |/ /",
        r" / ___ \ | |_| |  | |_) | (_| | | | |   < ",
        r"/_/   \_\ \____|  |____/ \__,_|_| |_|_|\_\ ",
    ]

    return '\n'.join([
        '',
        border,
        blank,
        *[row(a) for a in art],
        blank,
        row('          CLI  BANKING  APPLICATION'),
        row('        Python-Based Banking Simulator'),
        blank,
        row('    COP1047C  |  Miami Dade College'),
        row('    Student   |  Andres Gonzalez  #4000530842'),
        border,
        '',
    ])


_BANNER = _make_banner()


# ---------------------------------------------------------------------------
# Menu display helpers
# ---------------------------------------------------------------------------

def _show_banner():
    clear_screen()
    print(_BANNER)


def _show_main_menu():
    print("  +-----------------------------------+")
    print("  |          MAIN  MENU               |")
    print("  +-----------------------------------+")
    print("  |  1. Register                      |")
    print("  |  2. Login                         |")
    print("  |  3. Exit                          |")
    print("  +-----------------------------------+")


def _show_banking_menu(user):
    print(f"\n  Logged in as: {user.username}  (ID: {user.user_id})")
    print("  +-----------------------------------+")
    print("  |         BANKING  MENU             |")
    print("  +-----------------------------------+")
    print("  |  1. Manage Accounts               |")
    print("  |  2. Deposit / Withdraw / Transfer |")
    print("  |  3. Search & Sort Transactions    |")
    print("  |  4. View Reports                  |")
    print("  |  5. Logout                        |")
    print("  +-----------------------------------+")


def _show_accounts_menu(user):
    print(f"\n  Logged in as: {user.username}")
    print("  +-----------------------------------+")
    print("  |       MANAGE  ACCOUNTS            |")
    print("  +-----------------------------------+")
    print("  |  1. Create Checking Account       |")
    print("  |  2. Create Savings Account        |")
    print("  |  3. View All Accounts             |")
    print("  |  4. Delete Account                |")
    print("  |  5. Back to Banking Menu          |")
    print("  +-----------------------------------+")


# ---------------------------------------------------------------------------
# Account persistence helpers
# Sprint 4 (file_io.py) will replace these with save_accounts() /
# load_accounts() — the call sites in this file will be the only change.
# ---------------------------------------------------------------------------

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
    """Reconstruct an Account subclass from a JSON dict."""
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


def _load_user_accounts(username):
    """Populate _accounts with every account owned by username."""
    global _accounts
    _accounts = {}
    try:
        with open(_DATA_FILE, 'r') as f:
            data = json.load(f)
        for acc_dict in data.get("accounts", {}).values():
            if acc_dict.get("owner") == username:
                acc = _dict_to_account(acc_dict)
                _accounts[acc.account_id] = acc
    except (FileNotFoundError, json.JSONDecodeError):
        pass


def _save_user_accounts(username):
    """Write _accounts back to accounts.json, preserving other users' data."""
    try:
        with open(_DATA_FILE, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"users": {}, "accounts": {}}

    # Remove all existing records for this user, then re-insert current state.
    data["accounts"] = {
        k: v for k, v in data["accounts"].items()
        if v.get("owner") != username
    }
    for acc_id, acc in _accounts.items():
        data["accounts"][acc_id] = _account_to_dict(acc)

    os.makedirs(os.path.dirname(_DATA_FILE), exist_ok=True)
    with open(_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Manage Accounts — individual operations
# ---------------------------------------------------------------------------

def _create_account(account_class, user):
    """Prompt for parameters, create an Account subclass, persist it."""
    label = "Checking" if account_class is CheckingAccount else "Savings"
    print(f"\n  --- Create {label} Account ---")

    # Initial deposit (0 is allowed)
    while True:
        raw = input("  Initial deposit (or 0 to start empty): $").strip()
        try:
            amount = float(raw)
            if amount < 0:
                print("  Amount cannot be negative.")
                continue
            break
        except ValueError:
            print("  Please enter a valid number.")

    # Type-specific optional parameter
    kwargs = {}
    if account_class is CheckingAccount:
        raw = input(
            "  Overdraft limit [default $500.00, press Enter to keep]: $"
        ).strip()
        if raw:
            try:
                kwargs["overdraft_limit"] = float(raw)
            except ValueError:
                print("  Invalid input; using default $500.00.")
    else:
        raw = input(
            "  Monthly withdrawal limit [default 6, press Enter to keep]: "
        ).strip()
        if raw:
            try:
                kwargs["monthly_withdrawal_limit"] = int(raw)
            except ValueError:
                print("  Invalid input; using default of 6.")

    acc_id = generate_id()
    acc = account_class(acc_id, user.username, initial_balance=amount, **kwargs)
    _accounts[acc_id] = acc
    _save_user_accounts(user.username)

    print(f"\n  {label} Account created successfully!")
    print(acc.get_summary())
    input("\n  Press Enter to continue...")


def _view_all_accounts(user):
    """Display a summary of every account owned by the logged-in user."""
    print(f"\n  === Accounts for {user.username} ===")
    user_accs = [a for a in _accounts.values() if a.owner == user.username]

    if not user_accs:
        print("  You have no accounts yet.")
        input("\n  Press Enter to continue...")
        return

    for i, acc in enumerate(user_accs, 1):
        print(f"\n  [{i}] {acc.account_type} Account  [{acc.account_id}]")
        print(acc.get_summary())

    print(f"\n  Total: {len(user_accs)} account(s)")
    input("\n  Press Enter to continue...")


def _delete_account(user):
    """List accounts and prompt the user to permanently delete one."""
    print("\n  === Delete Account ===")
    user_accs = [a for a in _accounts.values() if a.owner == user.username]

    if not user_accs:
        print("  You have no accounts to delete.")
        input("\n  Press Enter to continue...")
        return

    for i, acc in enumerate(user_accs, 1):
        print(f"  [{i}] {acc.account_type} Account [{acc.account_id}]"
              f"  Balance: {format_currency(acc.balance)}")

    raw = input("\n  Enter account number to delete (0 to cancel): ").strip()
    try:
        idx = int(raw)
    except ValueError:
        print("  Invalid input.")
        input("  Press Enter to continue...")
        return

    if idx == 0:
        return
    if not (1 <= idx <= len(user_accs)):
        print("  Invalid selection.")
        input("  Press Enter to continue...")
        return

    target = user_accs[idx - 1]
    print(f"\n  WARNING: This will permanently delete account {target.account_id}.")
    print(f"  Current balance: {format_currency(target.balance)}")
    confirm = input("  Type 'DELETE' to confirm, or press Enter to cancel: ").strip()

    if confirm == "DELETE":
        del _accounts[target.account_id]
        _save_user_accounts(user.username)
        print(f"\n  Account {target.account_id} has been deleted.")
    else:
        print("  Deletion cancelled.")

    input("\n  Press Enter to continue...")


# ---------------------------------------------------------------------------
# Manage Accounts submenu loop
# ---------------------------------------------------------------------------

def _handle_manage_accounts(user):
    """Open the Manage Accounts submenu for the logged-in user."""
    while True:
        _show_banner()
        _show_accounts_menu(user)
        choice = input("\n  Select an option (1-5): ").strip()

        if choice == '1':
            _create_account(CheckingAccount, user)
        elif choice == '2':
            _create_account(SavingsAccount, user)
        elif choice == '3':
            _view_all_accounts(user)
        elif choice == '4':
            _delete_account(user)
        elif choice == '5':
            break
        else:
            print("  Invalid option. Please enter 1 through 5.")
            input("  Press Enter to continue...")


# ---------------------------------------------------------------------------
# Placeholder handlers (wired in later sprints)
# ---------------------------------------------------------------------------

def _handle_transactions():
    """Sprint 3: deposit, withdraw, transfer."""
    print("\n  [Transactions — available in Sprint 3]")
    input("  Press Enter to continue...")


def _handle_search_sort():
    """Sprint 5: search and sort transaction history."""
    print("\n  [Search & Sort — available in Sprint 5]")
    input("  Press Enter to continue...")


def _handle_reports():
    """Sprint 5: balance chart and CSV export."""
    print("\n  [Reports & Visualization — available in Sprint 5]")
    input("  Press Enter to continue...")


# ---------------------------------------------------------------------------
# Top-level menu loops
# ---------------------------------------------------------------------------

def _main_menu_loop():
    """Loop the pre-authentication menu until the user logs in or exits."""
    while True:
        _show_banner()
        _show_main_menu()
        choice = input("\n  Select an option (1-3): ").strip()

        if choice == '1':
            user = auth.register()
            if user:
                _load_user_accounts(user.username)
                _banking_menu_loop(user)
        elif choice == '2':
            user = auth.login()
            if user:
                _load_user_accounts(user.username)
                _banking_menu_loop(user)
        elif choice == '3':
            print("\n  Thank you for using AG Bank. Goodbye!\n")
            break
        else:
            print("  Invalid option. Please enter 1, 2, or 3.")
            input("  Press Enter to continue...")


def _banking_menu_loop(user):
    """Loop the authenticated banking menu until the user logs out."""
    while True:
        _show_banner()
        _show_banking_menu(user)
        choice = input("\n  Select an option (1-5): ").strip()

        if choice == '1':
            _handle_manage_accounts(user)
        elif choice == '2':
            _handle_transactions()
        elif choice == '3':
            _handle_search_sort()
        elif choice == '4':
            _handle_reports()
        elif choice == '5':
            _accounts.clear()
            auth.logout()
            break
        else:
            print("  Invalid option. Please enter 1 through 5.")
            input("  Press Enter to continue...")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        _main_menu_loop()
    except KeyboardInterrupt:
        print("\n\n  Session interrupted. Goodbye!\n")
