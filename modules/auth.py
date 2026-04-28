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

# Module-level session state; None means no user is logged in.
_current_user = None


class User:
    """An authenticated user session created after successful login or registration.

    Attributes:
        user_id (str): Read-only unique 8-character user identifier.
        username (str): Read-only username chosen at registration.
    """

    def __init__(self, user_id, username):
        """Initialize a User.

        Args:
            user_id (str): Unique identifier assigned at registration.
            username (str): The user's chosen login name.
        """
        self._user_id = user_id
        self._username = username

    @property
    def user_id(self):
        """str: Read-only unique user identifier."""
        return self._user_id

    @property
    def username(self):
        """str: Read-only username chosen at registration."""
        return self._username

    def __str__(self):
        """Return the username as the informal string representation."""
        return self._username

    def __repr__(self):
        """Return a developer-facing representation of the User."""
        return f"User(user_id='{self._user_id}', username='{self._username}')"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _hash_password(password):
    """Compute the SHA-256 hex digest of a plaintext password.

    Args:
        password (str): Plaintext password string.

    Returns:
        str: 64-character lowercase hexadecimal SHA-256 digest.
    """
    return hashlib.sha256(password.encode()).hexdigest()


def _load_data():
    """Read accounts.json and return the parsed data dict.

    Creates the file with an empty structure if it does not exist.
    Returns a safe default on JSON decode or permission errors.

    Returns:
        dict: Parsed data with 'users' and 'accounts' top-level keys.
    """
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
    """Serialise data to accounts.json.

    Args:
        data (dict): Full data dict with 'users' and 'accounts' keys.
    """
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
    """Return the currently logged-in User.

    Returns:
        User | None: The active User session, or None if no user is
            logged in.
    """
    return _current_user


def register():
    """Interactively register a new user account.

    Prompts for a unique username and a password (minimum 4 characters,
    confirmed by a second entry). Saves credentials with a SHA-256 hashed
    password and automatically logs the new user in.

    Returns:
        User | None: The newly created and logged-in User, or None if
            the process is interrupted before completion.
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
    """Interactively authenticate an existing user.

    Allows up to 3 credential attempts before locking out and returning
    None. A LOGIN_FAILED audit event is written after the third failure.

    Returns:
        User | None: The authenticated User on success, or None after
            3 failed attempts.
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
    """Log out the current user and clear the session.

    Writes a LOGOUT audit entry, prints a farewell message, then sets
    the module-level ``_current_user`` to None unconditionally.
    """
    global _current_user
    if _current_user:
        write_audit(_current_user.username, "LOGOUT", f"user_id={_current_user.user_id}")
        print(f"\n  Goodbye, {_current_user.username}! You have been logged out.")
    _current_user = None
