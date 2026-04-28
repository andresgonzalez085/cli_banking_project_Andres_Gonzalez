"""
auth.py — User registration, login, logout, and session state.
Implemented in Sprint 1.
"""

import hashlib
import json
import os

from modules.file_io import write_audit
from modules.utils import generate_id

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_BASE_DIR, 'data')
_DATA_FILE = os.path.join(_DATA_DIR, 'accounts.json')

_current_user = None  # session state: None when logged out


class User:
    """Represents an authenticated user session."""

    def __init__(self, user_id, username):
        """Initialize a User with a unique ID and username."""
        self._user_id = user_id
        self._username = username

    @property
    def user_id(self):
        """Unique user identifier."""
        return self._user_id

    @property
    def username(self):
        """Unique username chosen at registration."""
        return self._username

    def __str__(self):
        return self._username

    def __repr__(self):
        return f"User(user_id='{self._user_id}', username='{self._username}')"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _hash_password(password):
    """Return the SHA-256 hex digest of password."""
    return hashlib.sha256(password.encode()).hexdigest()


def _load_data():
    """Load accounts.json; return the parsed dict, creating the file if absent."""
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.exists(_DATA_FILE):
        empty = {"users": {}, "accounts": {}}
        _save_data(empty)
        return empty
    try:
        with open(_DATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, PermissionError) as e:
        print(f"  [Error] Could not read data file: {e}")
        return {"users": {}, "accounts": {}}


def _save_data(data):
    """Write data dict to accounts.json."""
    os.makedirs(_DATA_DIR, exist_ok=True)
    try:
        with open(_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except PermissionError as e:
        print(f"  [Error] Could not save data file: {e}")


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def get_current_user():
    """Return the currently logged-in User, or None."""
    return _current_user


def register():
    """Prompt for a new username and password, then create the account.

    Returns the new User on success, or None if registration is cancelled.
    """
    global _current_user
    print("\n  --- Register New User ---")

    data = _load_data()

    while True:
        username = input("  Username: ").strip()
        if not username:
            print("  Username cannot be empty.")
            continue
        if username in data["users"]:
            print("  Username already taken. Please choose another.")
            continue
        break

    while True:
        password = input("  Password: ").strip()
        if len(password) < 4:
            print("  Password must be at least 4 characters.")
            continue
        confirm = input("  Confirm password: ").strip()
        if password != confirm:
            print("  Passwords do not match. Try again.")
            continue
        break

    user_id = generate_id()
    data["users"][username] = {
        "user_id": user_id,
        "username": username,
        "password_hash": _hash_password(password),
    }
    _save_data(data)

    print(f"\n  Account created! Welcome, {username}.")
    _current_user = User(user_id, username)
    write_audit(username, "REGISTER", f"user_id={user_id}")
    return _current_user


def login():
    """Prompt for credentials and authenticate the user.

    Returns the User on success, or None on failure.
    """
    global _current_user
    print("\n  --- Login ---")

    data = _load_data()

    for attempt in range(3):
        username = input("  Username: ").strip()
        password = input("  Password: ").strip()

        user_record = data["users"].get(username)
        if user_record and user_record["password_hash"] == _hash_password(password):
            _current_user = User(user_record["user_id"], username)
            print(f"\n  Login successful. Welcome back, {username}!")
            write_audit(username, "LOGIN", f"user_id={user_record['user_id']}")
            return _current_user

        remaining = 2 - attempt
        if remaining > 0:
            print(f"  Invalid username or password. {remaining} attempt(s) remaining.")
        else:
            print("  Too many failed attempts. Returning to main menu.")
            write_audit(username or "unknown", "LOGIN_FAILED", "max_attempts_reached")

    return None


def logout():
    """Clear the current session and return to the main menu."""
    global _current_user
    if _current_user:
        write_audit(_current_user.username, "LOGOUT", f"user_id={_current_user.user_id}")
        print(f"\n  Goodbye, {_current_user.username}! You have been logged out.")
    _current_user = None
