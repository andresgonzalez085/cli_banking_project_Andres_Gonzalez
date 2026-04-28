"""
transactions.py — Deposit, withdraw, transfer, and recursive interest.
Implemented in Sprint 3.
"""

from datetime import datetime

from modules.file_io import append_transaction_csv, write_audit
from modules.utils import format_currency, generate_id

MAX_INTEREST_PERIODS = 120


# ---------------------------------------------------------------------------
# Public record factory
# ---------------------------------------------------------------------------

def record_transaction(txn_type, amount, balance_after):
    """Create and return a standard transaction dict (does not append to any account).

    All transaction functions in this module use this factory to guarantee
    a consistent record structure: txn_id, type, amount, timestamp, balance_after.

    Args:
        txn_type (str): One of DEPOSIT, WITHDRAWAL, TRANSFER, INTEREST.
        amount (float): Dollar amount of the transaction.
        balance_after (float): Account balance immediately after the operation.

    Returns:
        dict: Transaction record with the five standard fields.
    """
    return {
        "txn_id": generate_id(),
        "type": txn_type,
        "amount": amount,
        "timestamp": datetime.now().isoformat(timespec='seconds'),
        "balance_after": balance_after,
    }


# ---------------------------------------------------------------------------
# Receipt display
# ---------------------------------------------------------------------------

def _print_receipt(txn_type, account, amount, note=""):
    """Print a formatted transaction receipt to the terminal.

    Args:
        txn_type (str): Display label for the transaction type.
        account (Account): The account affected by the transaction.
        amount (float): Dollar amount of the transaction.
        note (str): Optional extra line (e.g. interest rate info).
    """
    txn = account.transactions[-1]
    W = 35
    sep = "  +" + "-" * W + "+"

    def dline(label, value):
        return f"  |  {label:<9}: {str(value):<22}|"

    def title(text):
        return f"  |  {text:<33}|"

    print()
    print(sep)
    print(title("TRANSACTION RECEIPT"))
    print(sep)
    print(dline("Type",      txn_type))
    print(dline("Account",   account.account_id))
    print(dline("Amount",    format_currency(amount)))
    print(dline("Balance",   format_currency(account.balance)))
    print(dline("Date/Time", txn["timestamp"]))
    print(dline("Txn ID",    txn["txn_id"]))
    if note:
        print(dline("Note", note[:22]))
    print(sep)


def _print_transfer_receipt(from_acc, to_acc, amount):
    """Print a formatted transfer receipt showing both account balances.

    Args:
        from_acc (Account): Debited account.
        to_acc (Account): Credited account.
        amount (float): Transfer amount.
    """
    txn = from_acc.transactions[-1]
    W = 35
    sep = "  +" + "-" * W + "+"

    def dline(label, value):
        return f"  |  {label:<9}: {str(value):<22}|"

    def title(text):
        return f"  |  {text:<33}|"

    print()
    print(sep)
    print(title("TRANSFER RECEIPT"))
    print(sep)
    print(dline("From",     from_acc.account_id))
    print(dline("To",       to_acc.account_id))
    print(dline("Amount",   format_currency(amount)))
    print(dline("From Bal", format_currency(from_acc.balance)))
    print(dline("To Bal",   format_currency(to_acc.balance)))
    print(dline("Date/Time", txn["timestamp"]))
    print(dline("Txn ID",   txn["txn_id"]))
    print(sep)


# ---------------------------------------------------------------------------
# Core transaction functions
# ---------------------------------------------------------------------------

def deposit(account, amount):
    """Deposit amount into account, write audit log, and print receipt.

    Delegates balance mutation and internal recording to account.deposit(),
    then writes the audit log and displays the receipt.

    Args:
        account (Account): Target account.
        amount (float): Positive dollar amount to deposit.

    Returns:
        dict: The transaction dict appended to account.transactions.

    Raises:
        ValueError: If amount is not positive (raised by account.deposit()).
    """
    account.deposit(amount)
    txn = account.transactions[-1]

    write_audit(
        account.owner, "DEPOSIT",
        f"account={account.account_id} amount={amount:.2f} "
        f"balance={account.balance:.2f}"
    )
    append_transaction_csv(account.owner, account.account_id, txn)
    _print_receipt("DEPOSIT", account, amount)
    return txn


def withdraw(account, amount):
    """Withdraw amount from account, write audit log, and print receipt.

    Delegates to account.withdraw(), which enforces each account type's
    own rules (overdraft for Checking, no-negative + monthly cap for Savings).

    Args:
        account (Account): Source account.
        amount (float): Positive dollar amount to withdraw.

    Returns:
        dict: The transaction dict appended to account.transactions.

    Raises:
        ValueError: Per account type's withdrawal rules.
    """
    account.withdraw(amount)
    txn = account.transactions[-1]

    write_audit(
        account.owner, "WITHDRAWAL",
        f"account={account.account_id} amount={amount:.2f} "
        f"balance={account.balance:.2f}"
    )
    append_transaction_csv(account.owner, account.account_id, txn)
    _print_receipt("WITHDRAWAL", account, amount)
    return txn


def transfer(from_acc, to_acc, amount):
    """Transfer amount between two accounts owned by the same user.

    Both accounts receive a TRANSFER-typed transaction record.
    from_acc's own withdrawal rules (overdraft, savings limits) are enforced.

    Args:
        from_acc (Account): Debited account.
        to_acc (Account): Credited account.
        amount (float): Positive dollar amount to transfer.

    Returns:
        tuple[dict, dict]: (from_txn, to_txn) transaction dicts.

    Raises:
        ValueError: If accounts belong to different owners, are the same
                    account, amount is not positive, or withdrawal fails.
    """
    if from_acc.owner != to_acc.owner:
        raise ValueError("Transfer is only allowed between your own accounts.")
    if from_acc.account_id == to_acc.account_id:
        raise ValueError("Cannot transfer to the same account.")
    if amount <= 0:
        raise ValueError("Transfer amount must be positive.")

    # Withdraw enforces account-specific rules (overdraft / savings limits).
    from_acc.withdraw(amount)
    from_acc.transactions[-1]["type"] = "TRANSFER"

    to_acc.deposit(amount)
    to_acc.transactions[-1]["type"] = "TRANSFER"

    from_txn = from_acc.transactions[-1]
    to_txn = to_acc.transactions[-1]

    write_audit(
        from_acc.owner, "TRANSFER",
        f"from={from_acc.account_id} to={to_acc.account_id} "
        f"amount={amount:.2f} from_bal={from_acc.balance:.2f} "
        f"to_bal={to_acc.balance:.2f}"
    )
    append_transaction_csv(from_acc.owner, from_acc.account_id, from_txn)
    append_transaction_csv(to_acc.owner, to_acc.account_id, to_txn)
    _print_transfer_receipt(from_acc, to_acc, amount)
    return from_txn, to_txn


# ---------------------------------------------------------------------------
# Recursive interest
# ---------------------------------------------------------------------------

def apply_interest(balance, rate, periods):
    """Recursively compute compound interest.

    Each recursive call multiplies the balance by (1 + rate), reducing
    periods by 1. Returns the original balance unchanged when periods == 0.

    Args:
        balance (float): Starting balance.
        rate (float): Periodic interest rate as a decimal (e.g. 0.05 = 5%).
        periods (int): Number of compounding periods remaining (max 120).

    Returns:
        float: Balance after all compounding periods have been applied.

    Raises:
        ValueError: If periods exceeds MAX_INTEREST_PERIODS (120).
    """
    if periods > MAX_INTEREST_PERIODS:
        raise ValueError(
            f"Period count {periods} exceeds the cap of {MAX_INTEREST_PERIODS}. "
            f"Use a value between 0 and {MAX_INTEREST_PERIODS}."
        )
    if periods == 0:                    # base case
        return balance
    return apply_interest(balance * (1 + rate), rate, periods - 1)


def apply_account_interest(account, rate, periods):
    """Apply compound interest to an account and record an INTEREST transaction.

    Calls apply_interest() to compute the new balance, then credits the
    difference as a deposit. The transaction type is updated to INTEREST.

    Args:
        account (Account): Account to credit.
        rate (float): Periodic interest rate (must be positive).
        periods (int): Compounding periods, 1–120.

    Returns:
        dict: The INTEREST transaction dict.

    Raises:
        ValueError: If rate <= 0, periods out of range, or no interest earned.
    """
    if rate <= 0:
        raise ValueError("Interest rate must be a positive decimal (e.g. 0.05).")

    old_balance = account.balance
    new_balance = apply_interest(old_balance, rate, periods)
    interest_earned = new_balance - old_balance

    if interest_earned <= 0:
        raise ValueError("No interest earned: balance or rate too small.")

    account.deposit(interest_earned)
    account.transactions[-1]["type"] = "INTEREST"
    txn = account.transactions[-1]

    write_audit(
        account.owner, "INTEREST",
        f"account={account.account_id} rate={rate:.4f} periods={periods} "
        f"earned={interest_earned:.2f} balance={account.balance:.2f}"
    )
    append_transaction_csv(account.owner, account.account_id, txn)
    _print_receipt(
        "INTEREST", account, interest_earned,
        note=f"{rate*100:.2f}% x {periods}p"
    )
    return txn
