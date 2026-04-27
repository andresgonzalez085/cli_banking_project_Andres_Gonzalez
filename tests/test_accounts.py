"""
test_accounts.py — pytest unit tests for Account, CheckingAccount, SavingsAccount.
Run with: python -m pytest tests/
"""

import pytest
from modules.accounts import Account, CheckingAccount, SavingsAccount


# ---------------------------------------------------------------------------
# CheckingAccount tests
# ---------------------------------------------------------------------------

class TestCheckingAccount:

    def test_create_with_defaults(self):
        ca = CheckingAccount("ACC001", "alice")
        assert ca.account_id == "ACC001"
        assert ca.owner == "alice"
        assert ca.balance == 0.0
        assert ca.overdraft_limit == 500.0
        assert ca.transactions == []
        assert ca.account_type == "Checking"

    def test_create_with_initial_balance(self):
        ca = CheckingAccount("ACC002", "alice", initial_balance=1000.0)
        assert ca.balance == 1000.0

    def test_deposit_increases_balance(self):
        ca = CheckingAccount("ACC003", "alice")
        returned = ca.deposit(500.0)
        assert returned == 500.0
        assert ca.balance == 500.0

    def test_multiple_deposits_accumulate(self):
        ca = CheckingAccount("ACC004", "alice")
        ca.deposit(200.0)
        ca.deposit(300.0)
        assert ca.balance == 500.0

    def test_deposit_records_transaction(self):
        ca = CheckingAccount("ACC005", "alice")
        ca.deposit(200.0)
        assert len(ca.transactions) == 1
        txn = ca.transactions[0]
        assert txn["type"] == "DEPOSIT"
        assert txn["amount"] == 200.0
        assert txn["balance_after"] == 200.0
        assert "txn_id" in txn
        assert "timestamp" in txn

    def test_withdraw_decreases_balance(self):
        ca = CheckingAccount("ACC006", "alice", initial_balance=500.0)
        returned = ca.withdraw(200.0)
        assert returned == 300.0
        assert ca.balance == 300.0

    def test_withdraw_records_transaction(self):
        ca = CheckingAccount("ACC007", "alice", initial_balance=500.0)
        ca.withdraw(100.0)
        assert len(ca.transactions) == 1
        txn = ca.transactions[0]
        assert txn["type"] == "WITHDRAWAL"
        assert txn["amount"] == 100.0
        assert txn["balance_after"] == 400.0

    def test_overdraft_allowed_within_limit(self):
        ca = CheckingAccount("ACC008", "alice", initial_balance=100.0,
                             overdraft_limit=200.0)
        returned = ca.withdraw(250.0)   # balance goes to -150, within -200
        assert returned == -150.0
        assert ca.balance == -150.0

    def test_overdraft_exact_limit_allowed(self):
        ca = CheckingAccount("ACC009", "alice", initial_balance=0.0,
                             overdraft_limit=500.0)
        returned = ca.withdraw(500.0)   # balance hits exactly -500
        assert returned == -500.0

    def test_overdraft_exceeded_raises(self):
        ca = CheckingAccount("ACC010", "alice", initial_balance=100.0,
                             overdraft_limit=200.0)
        with pytest.raises(ValueError):
            ca.withdraw(350.0)          # would reach -250, exceeds -200

    def test_deposit_zero_raises(self):
        ca = CheckingAccount("ACC011", "alice")
        with pytest.raises(ValueError):
            ca.deposit(0.0)

    def test_deposit_negative_raises(self):
        ca = CheckingAccount("ACC012", "alice")
        with pytest.raises(ValueError):
            ca.deposit(-100.0)

    def test_withdraw_zero_raises(self):
        ca = CheckingAccount("ACC013", "alice", initial_balance=500.0)
        with pytest.raises(ValueError):
            ca.withdraw(0.0)

    def test_withdraw_negative_raises(self):
        ca = CheckingAccount("ACC014", "alice", initial_balance=500.0)
        with pytest.raises(ValueError):
            ca.withdraw(-50.0)

    def test_get_balance(self):
        ca = CheckingAccount("ACC015", "alice", initial_balance=750.0)
        assert ca.get_balance() == 750.0

    def test_get_summary_is_string(self):
        ca = CheckingAccount("ACC016", "alice", initial_balance=100.0)
        summary = ca.get_summary()
        assert isinstance(summary, str)
        assert "ACC016" in summary
        assert "alice" in summary

    def test_str_is_string(self):
        ca = CheckingAccount("ACC017", "alice")
        result = str(ca)
        assert isinstance(result, str)

    def test_repr_identifies_class(self):
        ca = CheckingAccount("ACC018", "alice")
        result = repr(ca)
        assert isinstance(result, str)
        assert "CheckingAccount" in result

    def test_balance_property_is_readonly(self):
        ca = CheckingAccount("ACC019", "alice")
        with pytest.raises(AttributeError):
            ca.balance = 9999.0

    def test_account_id_property_is_readonly(self):
        ca = CheckingAccount("ACC020", "alice")
        with pytest.raises(AttributeError):
            ca.account_id = "FAKE"


# ---------------------------------------------------------------------------
# SavingsAccount tests
# ---------------------------------------------------------------------------

class TestSavingsAccount:

    def test_create_with_defaults(self):
        sa = SavingsAccount("SAV001", "bob")
        assert sa.account_id == "SAV001"
        assert sa.owner == "bob"
        assert sa.balance == 0.0
        assert sa.monthly_withdrawal_limit == 6
        assert sa.transactions == []
        assert sa.account_type == "Savings"

    def test_deposit(self):
        sa = SavingsAccount("SAV002", "bob")
        returned = sa.deposit(1000.0)
        assert returned == 1000.0
        assert sa.balance == 1000.0

    def test_withdraw(self):
        sa = SavingsAccount("SAV003", "bob", initial_balance=500.0)
        returned = sa.withdraw(200.0)
        assert returned == 300.0
        assert sa.balance == 300.0

    def test_withdraw_records_transaction(self):
        sa = SavingsAccount("SAV004", "bob", initial_balance=500.0)
        sa.withdraw(100.0)
        assert len(sa.transactions) == 1
        txn = sa.transactions[0]
        assert txn["type"] == "WITHDRAWAL"
        assert txn["amount"] == 100.0

    def test_negative_balance_not_allowed(self):
        sa = SavingsAccount("SAV005", "bob", initial_balance=100.0)
        with pytest.raises(ValueError):
            sa.withdraw(200.0)

    def test_exact_balance_withdraw_allowed(self):
        sa = SavingsAccount("SAV006", "bob", initial_balance=100.0)
        returned = sa.withdraw(100.0)
        assert returned == 0.0

    def test_monthly_withdrawal_limit_enforced(self):
        sa = SavingsAccount("SAV007", "bob", initial_balance=1000.0,
                            monthly_withdrawal_limit=3)
        sa.withdraw(10.0)
        sa.withdraw(10.0)
        sa.withdraw(10.0)
        with pytest.raises(ValueError):
            sa.withdraw(10.0)   # 4th withdrawal exceeds limit of 3

    def test_withdrawal_counter_increments(self):
        sa = SavingsAccount("SAV008", "bob", initial_balance=1000.0)
        sa.withdraw(10.0)
        sa.withdraw(10.0)
        assert sa._withdrawals_this_month == 2

    def test_reset_monthly_withdrawals(self):
        sa = SavingsAccount("SAV009", "bob", initial_balance=1000.0,
                            monthly_withdrawal_limit=1)
        sa.withdraw(10.0)
        sa.reset_monthly_withdrawals()
        returned = sa.withdraw(10.0)    # should succeed after reset
        assert returned == 980.0

    def test_get_summary_is_string(self):
        sa = SavingsAccount("SAV010", "bob", initial_balance=500.0)
        summary = sa.get_summary()
        assert isinstance(summary, str)
        assert "SAV010" in summary

    def test_str_is_string(self):
        sa = SavingsAccount("SAV011", "bob")
        assert isinstance(str(sa), str)

    def test_repr_identifies_class(self):
        sa = SavingsAccount("SAV012", "bob")
        result = repr(sa)
        assert isinstance(result, str)
        assert "SavingsAccount" in result

    def test_balance_property_is_readonly(self):
        sa = SavingsAccount("SAV013", "bob")
        with pytest.raises(AttributeError):
            sa.balance = 9999.0

    def test_account_id_property_is_readonly(self):
        sa = SavingsAccount("SAV014", "bob")
        with pytest.raises(AttributeError):
            sa.account_id = "FAKE"


# ---------------------------------------------------------------------------
# Inheritance & polymorphism tests
# ---------------------------------------------------------------------------

class TestInheritance:

    def test_checking_is_account_instance(self):
        ca = CheckingAccount("INH001", "carol")
        assert isinstance(ca, Account)

    def test_savings_is_account_instance(self):
        sa = SavingsAccount("INH002", "carol")
        assert isinstance(sa, Account)

    def test_checking_account_type_label(self):
        ca = CheckingAccount("INH003", "carol")
        assert ca.account_type == "Checking"

    def test_savings_account_type_label(self):
        sa = SavingsAccount("INH004", "carol")
        assert sa.account_type == "Savings"

    def test_deposit_polymorphism(self):
        """Both subclasses share the same deposit() implementation."""
        accounts = [
            CheckingAccount("INH005", "carol"),
            SavingsAccount("INH006", "carol"),
        ]
        for acc in accounts:
            result = acc.deposit(100.0)
            assert result == 100.0

    def test_withdraw_polymorphism_different_rules(self):
        """Withdraw behaves differently per subclass (overdraft vs. no-negative)."""
        ca = CheckingAccount("INH007", "carol", initial_balance=50.0,
                             overdraft_limit=100.0)
        sa = SavingsAccount("INH008", "carol", initial_balance=50.0)

        # CheckingAccount allows overdraft
        ca.withdraw(100.0)
        assert ca.balance == -50.0

        # SavingsAccount raises on overdraft
        with pytest.raises(ValueError):
            sa.withdraw(100.0)

    def test_str_differs_between_subclasses(self):
        ca = CheckingAccount("INH009", "carol")
        sa = SavingsAccount("INH010", "carol")
        assert str(ca) != str(sa)

    def test_get_balance_inherited(self):
        """get_balance() is inherited from Account and works on both subclasses."""
        ca = CheckingAccount("INH011", "carol", initial_balance=300.0)
        sa = SavingsAccount("INH012", "carol", initial_balance=700.0)
        assert ca.get_balance() == 300.0
        assert sa.get_balance() == 700.0

    def test_transactions_list_per_instance(self):
        """Each account has its own independent transactions list."""
        ca = CheckingAccount("INH013", "carol")
        sa = SavingsAccount("INH014", "carol")
        ca.deposit(100.0)
        assert len(ca.transactions) == 1
        assert len(sa.transactions) == 0
