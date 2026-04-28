# AG Bank — CLI Banking Application

A fully-featured Python command-line banking simulator built as the final
project for **COP1047C Introduction to Python Programming** at Miami Dade
College.

- **Student:** Andres Gonzalez — ID #4000530842
- **Course:** COP1047C · Section 2263-8684
- **Semester:** Spring 2026

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.10 or higher (Anaconda 3.12 recommended) |
| matplotlib | 3.x — balance chart generation |
| pandas | 2.x — transaction summary statistics |

Install all dependencies in one step:

```
pip install -r requirements.txt
```

---

## How to Run

```
python main.py
```

No command-line arguments are needed. All data files are created automatically
under `data/` on first run.

---

## Full Feature List

### Authentication
- User registration with unique username and SHA-256 hashed password
- Password confirmation prompt and 4-character minimum enforcement
- Login with up to 3 attempts before lockout
- Timestamped `LOGIN`, `LOGOUT`, `REGISTER`, and `LOGIN_FAILED` events written to `data/audit.log`

### Account Management
- Create **Checking Accounts** with a configurable overdraft limit (default $500)
- Create **Savings Accounts** with a configurable monthly withdrawal limit (default 6)
- View all accounts with balance summaries
- Delete an account (requires typing `DELETE` to confirm)
- Accounts persist across sessions via `data/accounts.json`

### Transactions
- **Deposit** — adds funds; receipt printed to terminal
- **Withdraw** — Checking allows overdraft down to −limit; Savings enforces no-negative balance and monthly withdrawal cap
- **Transfer** — moves funds between two accounts owned by the same user
- **Apply Interest** — recursive compound interest via `apply_interest(balance, rate, periods)` with a 120-period safety cap
- Every transaction generates a formatted ASCII receipt
- Every transaction is appended in real time to `data/transactions.csv`
- Every transaction writes a timestamped entry to `data/audit.log`

### Search & Sort
- **Linear search** — O(n) scan by exact Txn ID or case-insensitive type keyword
- **Binary search** — O(log n) search by amount; assertion enforces sorted-list precondition
- **Bubble sort** — sorts by date (ascending or descending); returns a copy, original unchanged
- **sorted_by_amount** — Python built-in `sorted()` with a lambda key (ascending or descending)
- Results displayed in a formatted ASCII table

### Reports & Visualization
- **Balance chart** — matplotlib line chart of balance over time, saved as `reports/balance_chart_<id>_<date>.png` via `plt.savefig()` (no display window)
- **Transaction history CSV** — full account history exported to `reports/transactions_<id>_<date>.csv`
- **Summary statistics** — pandas `DataFrame` with `describe()` output for amount and balance fields
- **Account statement** — formatted ASCII statement with header box and full transaction table printed to terminal

---

## Module Overview

| File | Description |
|------|-------------|
| `main.py` | Entry point; menu loops, session state, and operation dispatch |
| `modules/auth.py` | `User` class; registration, login, logout, SHA-256 password hashing |
| `modules/accounts.py` | `Account` base class; `CheckingAccount` and `SavingsAccount` with OOP inheritance |
| `modules/transactions.py` | Deposit, withdraw, transfer; recursive `apply_interest`; ASCII receipts |
| `modules/file_io.py` | JSON persistence, real-time CSV log, and audit log writer |
| `modules/search_sort.py` | Linear/binary search and bubble sort on transaction lists |
| `modules/reports.py` | matplotlib chart, pandas summary, CSV export, account statement |
| `modules/utils.py` | `format_currency`, `validate_amount`, `print_table`, `generate_id` |
| `tests/test_accounts.py` | 43 pytest unit tests for account classes (all passing) |

---

## Sample Input / Output

### Login and Banking Menu

```
+======================================================+
|                                                      |
|    _      ____    ____              _                |
|   / \    / ___|  | __ )  __ _ _ __ | | __           |
|  / _ \  | |  _   |  _ \ / _` | '_ \| |/ /           |
| / ___ \ | |_| |  | |_) | (_| | | | |   <            |
|/_/   \_\ \____|  |____/ \__,_|_| |_|_|\_\           |
|                                                      |
|          CLI  BANKING  APPLICATION                   |
|        Python-Based Banking Simulator                |
|                                                      |
|    COP1047C  |  Miami Dade College                   |
|    Student   |  Andres Gonzalez  #4000530842         |
+======================================================+

  Logged in as: andres  (ID: 38FFF5FC)
  +-----------------------------------+
  |         BANKING  MENU             |
  +-----------------------------------+
  |  1. Manage Accounts               |
  |  2. Deposit / Withdraw / Transfer |
  |  3. Search & Sort Transactions    |
  |  4. View Reports                  |
  |  5. Logout                        |
  +-----------------------------------+
```

### Deposit Receipt

```
  +---------------------------------+
  |  TRANSACTION RECEIPT            |
  +---------------------------------+
  |  Type     : DEPOSIT             |
  |  Account  : 891A1E89            |
  |  Amount   : $500.00             |
  |  Balance  : $1,500.00           |
  |  Date/Time: 2026-04-27T21:00:00 |
  |  Txn ID   : 848387BD            |
  +---------------------------------+
```

### Search Results Table

```
  +----------+------------+------------+------------------+------------+
  | Txn ID   | Type       | Amount     | Date/Time        | Balance    |
  +----------+------------+------------+------------------+------------+
  | 848387BD | DEPOSIT    | $500.00    | 2026-04-27T21:00 | $1,500.00  |
  | 1499C0D8 | DEPOSIT    | $250.00    | 2026-04-27T21:01 | $1,750.00  |
  +----------+------------+------------+------------------+------------+
  2 result(s)
```

---

## Challenges Encountered and How Resolved

**1. Windows cp1252 terminal encoding**
The initial banner used Unicode box-drawing characters (╔, ║, ═) that the
Windows cp1252 code page cannot encode, causing `UnicodeEncodeError` at startup.
Fixed by replacing all Unicode characters with plain ASCII equivalents
(`+`, `-`, `|`, `=`).

**2. Raw string cannot end with a backslash**
The last line of the AG Bank ASCII art ends with `\_\ `. A Python raw string
`r"..."` cannot end with an odd number of backslashes before the closing quote.
Fixed by appending a trailing space — harmless because the line is padded with
`str.ljust(54)` during banner construction.

**3. Banner box misalignment**
A static multi-line string produced subtly different line widths due to
invisible trailing spaces. Fixed by building the banner programmatically:
each line is padded to exactly W=54 characters with `str.ljust(W)`, guaranteeing
pixel-perfect alignment regardless of content length.

**4. TRANSFER and INTEREST transaction types**
`account.withdraw()` and `account.deposit()` always record WITHDRAWAL and
DEPOSIT internally. Post-hoc mutation of `account.transactions[-1]["type"]`
to "TRANSFER" or "INTEREST" allowed reusing the tested account layer without
modification.

**5. Recursive interest stack depth**
`apply_interest` calls itself recursively once per compounding period.
Python's default recursion limit is 1000, so 120 periods is safe — but the
`MAX_INTEREST_PERIODS = 120` cap is enforced with an explicit `ValueError`
to prevent runaway recursion from user input.

**6. Binary search precondition**
Python's `assert` statement is used to verify that the input list is sorted
by amount before binary search begins. This taught the concept of algorithm
preconditions and the difference between precondition failures (programmer
error, use `assert`) and runtime errors (user error, use `ValueError`).

**7. Avoiding circular imports in file_io.py**
`file_io.py` imports `CheckingAccount` and `SavingsAccount` from `accounts.py`
for deserialization. Import order across the eight modules was planned carefully
to ensure no circular dependencies: `utils` ← `accounts` ← `file_io` ←
`transactions` / `auth` / `reports` / `search_sort` ← `main`.

---

## Reflections — What Was Learned

**Object-Oriented Programming** — Designing a three-class hierarchy (`Account`,
`CheckingAccount`, `SavingsAccount`) made the difference between inheritance and
composition concrete. Overriding `withdraw()` in each subclass to enforce
different rules illustrated polymorphism in a realistic context.

**`@property` for encapsulation** — Using read-only properties for `balance` and
`account_id` enforced the rule that balances can only change through `deposit()`
and `withdraw()`, and that account IDs are immutable after creation.

**Recursive algorithms** — Implementing `apply_interest(balance, rate, periods)`
recursively clarified base cases, recursive cases, and why a depth cap matters
in practice (not just in theory).

**File I/O patterns** — Managing three file formats simultaneously — JSON for
state, CSV for a running log, and a plain-text audit trail — highlighted the
importance of separating concerns and handling every error path explicitly.

**Algorithm complexity** — Implementing both linear search (O(n)) and binary
search (O(log n) with sorted precondition) in the same module made the
trade-off between simplicity and performance tangible.

**Third-party library integration** — Using pandas `DataFrame.describe()` for
statistics and matplotlib `plt.savefig()` for charts without a display (Agg
backend) showed how professional tools fit into a larger application.

**Test-driven thinking** — Writing 43 pytest tests against `accounts.py` before
the rest of the project was complete revealed edge cases (exact overdraft limit,
zero-balance savings withdrawal, monthly limit reset) that would otherwise have
been discovered at runtime.

---

## GitHub Repository

[https://github.com/andres-gonzalez/cli_banking_project_Andres_Gonzalez](https://github.com/andres-gonzalez/cli_banking_project_Andres_Gonzalez)
