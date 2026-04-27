"""
accounts.py — Account, CheckingAccount, and SavingsAccount classes.
Implemented in Sprint 2.
"""

from datetime import datetime
from modules.utils import generate_id, format_currency


class Account:
    """Base class representing a bank account.

    Attributes:
        owner (str): Username of the account holder.
        account_type (str): Human-readable type label set by subclasses.
        transactions (list): Ordered list of transaction dicts.
    """

    def __init__(self, account_id, owner, account_type, initial_balance=0.0):
        """Initialize an Account.

        Args:
            account_id (str): Unique account identifier.
            owner (str): Username of the account holder.
            account_type (str): Label such as 'Checking' or 'Savings'.
            initial_balance (float): Opening balance (default 0.0).
        """
        self._account_id = account_id
        self.owner = owner
        self.account_type = account_type
        self._balance = float(initial_balance)
        self.transactions = []

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def account_id(self):
        """str: Read-only unique account identifier."""
        return self._account_id

    @property
    def balance(self):
        """float: Read-only current balance; mutated only via deposit/withdraw."""
        return self._balance

    # ------------------------------------------------------------------
    # Core methods
    # ------------------------------------------------------------------

    def deposit(self, amount):
        """Add funds to the account.

        Args:
            amount (float): Positive dollar amount to deposit.

        Returns:
            float: New balance after the deposit.

        Raises:
            ValueError: If amount is not positive.
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self._balance += amount
        self._record("DEPOSIT", amount)
        return self._balance

    def withdraw(self, amount):
        """Remove funds from the account (base: no negative balance).

        Subclasses override this to apply their own limit rules.

        Args:
            amount (float): Positive dollar amount to withdraw.

        Returns:
            float: New balance after the withdrawal.

        Raises:
            ValueError: If amount is not positive or exceeds available balance.
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if amount > self._balance:
            raise ValueError("Insufficient funds.")
        self._balance -= amount
        self._record("WITHDRAWAL", amount)
        return self._balance

    def get_balance(self):
        """Return the current balance.

        Returns:
            float: Current account balance.
        """
        return self._balance

    def get_summary(self):
        """Return a formatted multi-line account summary string.

        Returns:
            str: Account details suitable for terminal display.
        """
        lines = [
            f"  Account ID   : {self._account_id}",
            f"  Type         : {self.account_type}",
            f"  Owner        : {self.owner}",
            f"  Balance      : {format_currency(self._balance)}",
            f"  Transactions : {len(self.transactions)}",
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _record(self, txn_type, amount):
        """Append a transaction dict to the transactions list.

        Args:
            txn_type (str): One of DEPOSIT, WITHDRAWAL, TRANSFER, INTEREST.
            amount (float): Dollar amount of the transaction.
        """
        self.transactions.append({
            "txn_id": generate_id(),
            "type": txn_type,
            "amount": amount,
            "timestamp": datetime.now().isoformat(timespec='seconds'),
            "balance_after": self._balance,
        })

    # ------------------------------------------------------------------
    # String representations
    # ------------------------------------------------------------------

    def __str__(self):
        return (
            f"{self.account_type} Account [{self._account_id}] "
            f"owner={self.owner} balance={format_currency(self._balance)}"
        )

    def __repr__(self):
        return (
            f"Account(id='{self._account_id}', type='{self.account_type}', "
            f"owner='{self.owner}', balance={self._balance:.2f})"
        )


# ---------------------------------------------------------------------------

class CheckingAccount(Account):
    """Checking account with an overdraft limit.

    Allows the balance to go negative down to -overdraft_limit before
    raising an error.

    Attributes:
        overdraft_limit (float): Maximum negative balance permitted.
    """

    def __init__(self, account_id, owner, initial_balance=0.0, overdraft_limit=500.0):
        """Initialize a CheckingAccount.

        Args:
            account_id (str): Unique account identifier.
            owner (str): Username of the account holder.
            initial_balance (float): Opening balance (default 0.0).
            overdraft_limit (float): Max overdraft allowed (default $500).
        """
        super().__init__(account_id, owner, "Checking", initial_balance)
        self.overdraft_limit = overdraft_limit

    def withdraw(self, amount):
        """Withdraw funds, permitting overdraft up to overdraft_limit.

        Args:
            amount (float): Positive dollar amount to withdraw.

        Returns:
            float: New balance (may be negative within overdraft limit).

        Raises:
            ValueError: If amount is not positive or exceeds available credit.
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if (self._balance - amount) < -self.overdraft_limit:
            raise ValueError(
                f"Exceeds overdraft limit of {format_currency(self.overdraft_limit)}. "
                f"Available: {format_currency(self._balance + self.overdraft_limit)}."
            )
        self._balance -= amount
        self._record("WITHDRAWAL", amount)
        return self._balance

    def get_summary(self):
        """Return account summary including overdraft information."""
        base = super().get_summary()
        return base + f"\n  Overdraft    : {format_currency(self.overdraft_limit)}"

    def __str__(self):
        return (
            f"Checking Account [{self._account_id}] "
            f"owner={self.owner} "
            f"balance={format_currency(self._balance)} "
            f"(overdraft: {format_currency(self.overdraft_limit)})"
        )

    def __repr__(self):
        return (
            f"CheckingAccount(id='{self._account_id}', "
            f"owner='{self.owner}', "
            f"balance={self._balance:.2f}, "
            f"overdraft_limit={self.overdraft_limit:.2f})"
        )


# ---------------------------------------------------------------------------

class SavingsAccount(Account):
    """Savings account with a monthly withdrawal limit and no overdraft.

    Balance can never go negative. Withdrawals are capped at
    monthly_withdrawal_limit per calendar-month window.

    Attributes:
        monthly_withdrawal_limit (int): Max withdrawals allowed per month.
    """

    def __init__(self, account_id, owner, initial_balance=0.0,
                 monthly_withdrawal_limit=6):
        """Initialize a SavingsAccount.

        Args:
            account_id (str): Unique account identifier.
            owner (str): Username of the account holder.
            initial_balance (float): Opening balance (default 0.0).
            monthly_withdrawal_limit (int): Max withdrawals per month (default 6).
        """
        super().__init__(account_id, owner, "Savings", initial_balance)
        self.monthly_withdrawal_limit = monthly_withdrawal_limit
        self._withdrawals_this_month = 0

    def withdraw(self, amount):
        """Withdraw funds, enforcing no-negative and monthly limit rules.

        Args:
            amount (float): Positive dollar amount to withdraw.

        Returns:
            float: New balance after the withdrawal.

        Raises:
            ValueError: If amount is not positive, exceeds balance,
                        or the monthly withdrawal limit has been reached.
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if amount > self._balance:
            raise ValueError(
                "Insufficient funds: Savings account cannot go negative."
            )
        if self._withdrawals_this_month >= self.monthly_withdrawal_limit:
            raise ValueError(
                f"Monthly withdrawal limit of {self.monthly_withdrawal_limit} reached."
            )
        self._balance -= amount
        self._withdrawals_this_month += 1
        self._record("WITHDRAWAL", amount)
        return self._balance

    def reset_monthly_withdrawals(self):
        """Reset the monthly withdrawal counter (call at start of each month)."""
        self._withdrawals_this_month = 0

    def get_summary(self):
        """Return account summary including withdrawal limit information."""
        base = super().get_summary()
        return (
            base
            + f"\n  Withdrawals  : {self._withdrawals_this_month}"
              f" / {self.monthly_withdrawal_limit} this month"
        )

    def __str__(self):
        return (
            f"Savings Account [{self._account_id}] "
            f"owner={self.owner} "
            f"balance={format_currency(self._balance)} "
            f"(withdrawals: {self._withdrawals_this_month}/{self.monthly_withdrawal_limit})"
        )

    def __repr__(self):
        return (
            f"SavingsAccount(id='{self._account_id}', "
            f"owner='{self.owner}', "
            f"balance={self._balance:.2f}, "
            f"monthly_withdrawal_limit={self.monthly_withdrawal_limit})"
        )
