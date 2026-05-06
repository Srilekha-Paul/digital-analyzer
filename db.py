"""
Digital Detox Tracker — db.py
SQLite database initialisation and helper functions.
Passwords are hashed with werkzeug's pbkdf2 (bcrypt-level security).
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')


def get_connection():
    """Return a Row-factory SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't already exist."""
    conn = get_connection()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL,
            created  TEXT    DEFAULT (datetime('now'))
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS usage_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            app_name   TEXT    NOT NULL,
            minutes    REAL    NOT NULL DEFAULT 0,
            log_date   TEXT    DEFAULT (date('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()


# ── User Operations ──────────────────────────────────────────────

def user_exists(username: str) -> bool:
    """Return True if the username is already taken."""
    conn = get_connection()
    row  = conn.execute(
        'SELECT 1 FROM users WHERE username = ?', (username,)
    ).fetchone()
    conn.close()
    return row is not None


def create_user(username: str, password: str) -> dict:
    """Insert a new user and return their record as a dict."""
    hashed = generate_password_hash(password)
    conn   = get_connection()
    c      = conn.cursor()
    c.execute(
        'INSERT INTO users (username, password) VALUES (?, ?)',
        (username, hashed)
    )
    conn.commit()
    user_id = c.lastrowid
    conn.close()
    return {'id': user_id, 'username': username}


def get_user(username: str, password: str):
    """
    Validate credentials and return the user row as a dict,
    or None if authentication fails.
    """
    conn = get_connection()
    row  = conn.execute(
        'SELECT * FROM users WHERE username = ?', (username,)
    ).fetchone()
    conn.close()

    if row and check_password_hash(row['password'], password):
        return dict(row)
    return None


# ── Usage Log Operations ─────────────────────────────────────────

def log_usage(user_id: int, app_name: str, minutes: float):
    """Insert or update today's usage record for an app."""
    conn = get_connection()
    existing = conn.execute(
        '''SELECT id FROM usage_log
           WHERE user_id=? AND app_name=? AND log_date=date('now')''',
        (user_id, app_name)
    ).fetchone()

    if existing:
        conn.execute(
            'UPDATE usage_log SET minutes=minutes+? WHERE id=?',
            (minutes, existing['id'])
        )
    else:
        conn.execute(
            'INSERT INTO usage_log (user_id, app_name, minutes) VALUES (?,?,?)',
            (user_id, app_name, minutes)
        )
    conn.commit()
    conn.close()


def get_today_usage(user_id: int) -> list:
    """Return today's usage rows for a user, ordered by minutes desc."""
    conn = get_connection()
    rows = conn.execute(
        '''SELECT app_name, minutes FROM usage_log
           WHERE user_id=? AND log_date=date('now')
           ORDER BY minutes DESC''',
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]