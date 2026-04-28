"""
main.py — Application entry point for the CLI Banking Application.
Run with: python main.py
"""

import modules.auth as auth
import modules.file_io as file_io
import modules.reports as rpt
import modules.search_sort as ss
import modules.transactions as txn
from modules.accounts import CheckingAccount, SavingsAccount
from modules.utils import clear_screen, format_currency, generate_id, validate_amount

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


def _show_transactions_menu(user):
    print(f"\n  Logged in as: {user.username}")
    print("  +-----------------------------------+")
    print("  |      TRANSACTIONS  MENU           |")
    print("  +-----------------------------------+")
    print("  |  1. Deposit                       |")
    print("  |  2. Withdraw                      |")
    print("  |  3. Transfer                      |")
    print("  |  4. Apply Interest                |")
    print("  |  5. Back to Banking Menu          |")
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


def _show_search_sort_menu(user):
    print(f"\n  Logged in as: {user.username}")
    print("  +-----------------------------------+")
    print("  |     SEARCH & SORT  MENU           |")
    print("  +-----------------------------------+")
    print("  |  1. Linear Search (ID or type)    |")
    print("  |  2. Binary Search (by amount)     |")
    print("  |  3. Sort by Date  (oldest first)  |")
    print("  |  4. Sort by Date  (newest first)  |")
    print("  |  5. Sort by Amount (lowest first) |")
    print("  |  6. Sort by Amount (highest first)|")
    print("  |  7. Back to Banking Menu          |")
    print("  +-----------------------------------+")


def _show_reports_menu(user):
    print(f"\n  Logged in as: {user.username}")
    print("  +-----------------------------------+")
    print("  |         REPORTS  MENU             |")
    print("  +-----------------------------------+")
    print("  |  1. Balance Chart (PNG)           |")
    print("  |  2. Export History (CSV)          |")
    print("  |  3. Transaction Summary (stats)   |")
    print("  |  4. Account Statement (terminal)  |")
    print("  |  5. Back to Banking Menu          |")
    print("  +-----------------------------------+")


# ---------------------------------------------------------------------------
# Account persistence helpers — delegate to file_io (Sprint 4)
# ---------------------------------------------------------------------------

def _load_user_accounts(username):
    """Populate _accounts with every account owned by username."""
    global _accounts
    _accounts = file_io.load_accounts(username)


def _save_user_accounts(username):
    """Write _accounts back to accounts.json via file_io."""
    file_io.save_accounts(username, _accounts)


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
# Transaction helpers
# ---------------------------------------------------------------------------

def _select_account(user_accs, prompt):
    """List user_accs and return the chosen Account, or None to cancel."""
    if not user_accs:
        print("  You have no accounts yet.")
        input("  Press Enter to continue...")
        return None

    for i, acc in enumerate(user_accs, 1):
        print(f"  [{i}] {acc.account_type} Account [{acc.account_id}]"
              f"  Balance: {format_currency(acc.balance)}")

    raw = input(f"\n  {prompt} (0 to cancel): ").strip()
    try:
        idx = int(raw)
    except ValueError:
        print("  Invalid input.")
        input("  Press Enter to continue...")
        return None

    if idx == 0:
        return None
    if not (1 <= idx <= len(user_accs)):
        print("  Invalid selection.")
        input("  Press Enter to continue...")
        return None

    return user_accs[idx - 1]


def _do_deposit(user):
    """Prompt for account and amount, then execute a deposit."""
    print("\n  --- Deposit ---")
    user_accs = [a for a in _accounts.values() if a.owner == user.username]
    account = _select_account(user_accs, "Select account number")
    if account is None:
        return

    raw = input("  Amount to deposit: $").strip()
    try:
        amount = validate_amount(raw)
    except ValueError as e:
        print(f"  Error: {e}")
        input("  Press Enter to continue...")
        return

    try:
        txn.deposit(account, amount)
        _save_user_accounts(user.username)
    except ValueError as e:
        print(f"  Error: {e}")

    input("\n  Press Enter to continue...")


def _do_withdraw(user):
    """Prompt for account and amount, then execute a withdrawal."""
    print("\n  --- Withdraw ---")
    user_accs = [a for a in _accounts.values() if a.owner == user.username]
    account = _select_account(user_accs, "Select account number")
    if account is None:
        return

    raw = input("  Amount to withdraw: $").strip()
    try:
        amount = validate_amount(raw)
    except ValueError as e:
        print(f"  Error: {e}")
        input("  Press Enter to continue...")
        return

    try:
        txn.withdraw(account, amount)
        _save_user_accounts(user.username)
    except ValueError as e:
        print(f"  Error: {e}")

    input("\n  Press Enter to continue...")


def _do_transfer(user):
    """Prompt for source, destination, and amount, then execute a transfer."""
    print("\n  --- Transfer ---")
    user_accs = [a for a in _accounts.values() if a.owner == user.username]

    if len(user_accs) < 2:
        print("  You need at least 2 accounts to transfer between them.")
        input("  Press Enter to continue...")
        return

    print("  Select SOURCE account:")
    from_acc = _select_account(user_accs, "Select source account number")
    if from_acc is None:
        return

    remaining = [a for a in user_accs if a.account_id != from_acc.account_id]
    print("  Select DESTINATION account:")
    to_acc = _select_account(remaining, "Select destination account number")
    if to_acc is None:
        return

    raw = input("  Amount to transfer: $").strip()
    try:
        amount = validate_amount(raw)
    except ValueError as e:
        print(f"  Error: {e}")
        input("  Press Enter to continue...")
        return

    try:
        txn.transfer(from_acc, to_acc, amount)
        _save_user_accounts(user.username)
    except ValueError as e:
        print(f"  Error: {e}")

    input("\n  Press Enter to continue...")


def _do_interest(user):
    """Prompt for account, rate, and periods, then apply compound interest."""
    print("\n  --- Apply Interest ---")
    user_accs = [a for a in _accounts.values() if a.owner == user.username]
    account = _select_account(user_accs, "Select account number")
    if account is None:
        return

    raw_rate = input("  Annual/periodic interest rate (e.g. 0.05 for 5%): ").strip()
    try:
        rate = float(raw_rate)
        if rate <= 0:
            raise ValueError("Rate must be positive.")
    except ValueError as e:
        print(f"  Error: {e}")
        input("  Press Enter to continue...")
        return

    raw_periods = input("  Number of compounding periods (1-120): ").strip()
    try:
        periods = int(raw_periods)
        if not (1 <= periods <= 120):
            raise ValueError("Periods must be between 1 and 120.")
    except ValueError as e:
        print(f"  Error: {e}")
        input("  Press Enter to continue...")
        return

    try:
        txn.apply_account_interest(account, rate, periods)
        _save_user_accounts(user.username)
    except ValueError as e:
        print(f"  Error: {e}")

    input("\n  Press Enter to continue...")


# ---------------------------------------------------------------------------
# Transactions submenu loop
# ---------------------------------------------------------------------------

def _handle_transactions(user):
    """Open the Transactions submenu for the logged-in user."""
    while True:
        _show_banner()
        _show_transactions_menu(user)
        choice = input("\n  Select an option (1-5): ").strip()

        if choice == '1':
            _do_deposit(user)
        elif choice == '2':
            _do_withdraw(user)
        elif choice == '3':
            _do_transfer(user)
        elif choice == '4':
            _do_interest(user)
        elif choice == '5':
            break
        else:
            print("  Invalid option. Please enter 1 through 5.")
            input("  Press Enter to continue...")


# ---------------------------------------------------------------------------
# Search & Sort submenu loop
# ---------------------------------------------------------------------------

def _handle_search_sort(user):
    """Open the Search & Sort submenu for the logged-in user."""
    while True:
        _show_banner()
        _show_search_sort_menu(user)
        choice = input("\n  Select an option (1-7): ").strip()

        if choice == '7':
            break

        if choice not in ('1', '2', '3', '4', '5', '6'):
            print("  Invalid option. Please enter 1 through 7.")
            input("  Press Enter to continue...")
            continue

        user_accs = [a for a in _accounts.values() if a.owner == user.username]
        account = _select_account(user_accs, "Select account number")
        if account is None:
            continue

        txns = account.transactions
        if not txns:
            print("  This account has no transaction history.")
            input("  Press Enter to continue...")
            continue

        if choice == '1':
            query = input("  Search query (Txn ID or type keyword): ").strip()
            if not query:
                print("  Query cannot be empty.")
                input("  Press Enter to continue...")
                continue
            results = ss.linear_search(txns, query)
            print(f"\n  Linear Search results for '{query}':")
            ss.print_results(results)
            input("  Press Enter to continue...")

        elif choice == '2':
            raw = input("  Amount to search for: $").strip()
            try:
                amount = float(raw)
            except ValueError:
                print("  Invalid amount.")
                input("  Press Enter to continue...")
                continue
            sorted_txns = ss.sorted_by_amount(txns)
            results = ss.binary_search(sorted_txns, amount)
            print(f"\n  Binary Search results for ${amount:.2f}:")
            ss.print_results(results)
            input("  Press Enter to continue...")

        elif choice == '3':
            results = ss.bubble_sort(txns, reverse=False)
            print("\n  Sorted by Date (oldest first):")
            ss.print_results(results)
            input("  Press Enter to continue...")

        elif choice == '4':
            results = ss.bubble_sort(txns, reverse=True)
            print("\n  Sorted by Date (newest first):")
            ss.print_results(results)
            input("  Press Enter to continue...")

        elif choice == '5':
            results = ss.sorted_by_amount(txns, reverse=False)
            print("\n  Sorted by Amount (lowest first):")
            ss.print_results(results)
            input("  Press Enter to continue...")

        elif choice == '6':
            results = ss.sorted_by_amount(txns, reverse=True)
            print("\n  Sorted by Amount (highest first):")
            ss.print_results(results)
            input("  Press Enter to continue...")


# ---------------------------------------------------------------------------
# Reports submenu loop
# ---------------------------------------------------------------------------

def _handle_reports(user):
    """Open the Reports submenu for the logged-in user."""
    while True:
        _show_banner()
        _show_reports_menu(user)
        choice = input("\n  Select an option (1-5): ").strip()

        if choice == '5':
            break

        if choice not in ('1', '2', '3', '4'):
            print("  Invalid option. Please enter 1 through 5.")
            input("  Press Enter to continue...")
            continue

        user_accs = [a for a in _accounts.values() if a.owner == user.username]
        account = _select_account(user_accs, "Select account number")
        if account is None:
            continue

        if choice == '1':
            print("\n  Generating balance chart...")
            path = rpt.generate_balance_chart(account)
            if path:
                print(f"\n  Chart saved to:\n  {path}")
            input("\n  Press Enter to continue...")

        elif choice == '2':
            path = rpt.export_transactions_csv(account)
            if path:
                print(f"\n  CSV saved to:\n  {path}")
            input("\n  Press Enter to continue...")

        elif choice == '3':
            rpt.generate_summary(account)
            input("  Press Enter to continue...")

        elif choice == '4':
            rpt.print_account_statement(account)
            input("\n  Press Enter to continue...")


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
            _handle_transactions(user)
        elif choice == '3':
            _handle_search_sort(user)
        elif choice == '4':
            _handle_reports(user)
        elif choice == '5':
            _save_user_accounts(user.username)
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
