"""
main.py — Application entry point for the CLI Banking Application.
Run with: python main.py
"""

import modules.auth as auth
from modules.utils import clear_screen

_BANNER = r"""
+======================================================+
|                                                      |
|   ____    _    _   _  _  __                          |
|  | __ )  / \  | \ | || |/ /                          |
|  |  _ \ / _ \ |  \| || ' /                           |
|  | |_) / ___ \| |\  || . \                           |
|  |____/_/   \_\_| \_||_|\_\                          |
|                                                      |
|          CLI  BANKING  APPLICATION                   |
|        Python-Based Banking Simulator                |
|                                                      |
|    COP1047C  |  Miami Dade College                   |
|    Student   |  Andres Gonzalez  #4000530842         |
+======================================================+
"""


# ---------------------------------------------------------------------------
# Menu displays
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


# ---------------------------------------------------------------------------
# Placeholder handlers (wired in later sprints)
# ---------------------------------------------------------------------------

def _handle_manage_accounts():
    """Sprint 2: account creation and management."""
    print("\n  [Manage Accounts — available in Sprint 2]")
    input("  Press Enter to continue...")


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
# Menu loops
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
                _banking_menu_loop(user)
        elif choice == '2':
            user = auth.login()
            if user:
                _banking_menu_loop(user)
        elif choice == '3':
            print("\n  Thank you for using CLI Banking. Goodbye!\n")
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
            _handle_manage_accounts()
        elif choice == '2':
            _handle_transactions()
        elif choice == '3':
            _handle_search_sort()
        elif choice == '4':
            _handle_reports()
        elif choice == '5':
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
