import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DB_PATH = Path(__file__).resolve().parent / "voice_bot.db"


def init_db():
    """Initializes SQLite database tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            joined_at REAL,
            last_active REAL,
            voice_count INTEGER DEFAULT 0,
            tts_count INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action_type TEXT,
            detail TEXT,
            created_at REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()


def register_user(user_id: int, username: Optional[str], first_name: Optional[str]) -> Tuple[bool, dict]:
    """Registers a new user or updates info."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = time.time()

    cursor.execute("SELECT user_id, username, first_name, voice_count, tts_count FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    is_new = False
    if row is None:
        is_new = True
        cursor.execute("""
            INSERT INTO users (user_id, username, first_name, joined_at, last_active, voice_count, tts_count)
            VALUES (?, ?, ?, ?, ?, 0, 0)
        """, (user_id, username or "", first_name or "", now, now))
    else:
        cursor.execute("""
            UPDATE users SET username = ?, first_name = ?, last_active = ? WHERE user_id = ?
        """, (username or "", first_name or "", now, user_id))

    conn.commit()
    conn.close()
    return is_new, {"user_id": user_id, "username": username, "first_name": first_name}


def log_action(user_id: int, action_type: str, detail: str = ""):
    """Logs every single user action into analytics history."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO usage_logs (user_id, action_type, detail, created_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, action_type, detail, time.time()))
    conn.commit()
    conn.close()


def increment_voice(user_id: int, effect_name: str = ""):
    """Increments the processed voice count for a user and logs effect."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = time.time()
    cursor.execute("UPDATE users SET voice_count = voice_count + 1, last_active = ? WHERE user_id = ?", (now, user_id))
    cursor.execute("INSERT INTO usage_logs (user_id, action_type, detail, created_at) VALUES (?, 'voice_effect', ?, ?)", (user_id, effect_name, now))
    conn.commit()
    conn.close()


def increment_tts(user_id: int, voice_name: str = ""):
    """Increments the generated TTS count for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = time.time()
    cursor.execute("UPDATE users SET tts_count = tts_count + 1, last_active = ? WHERE user_id = ?", (now, user_id))
    cursor.execute("INSERT INTO usage_logs (user_id, action_type, detail, created_at) VALUES (?, 'tts', ?, ?)", (user_id, voice_name, now))
    conn.commit()
    conn.close()


def get_detailed_statistics() -> dict:
    """Calculates comprehensive deep analytics."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*), SUM(voice_count), SUM(tts_count) FROM users")
    row = cursor.fetchone()
    total_users = row[0] or 0
    total_voices = row[1] or 0
    total_tts = row[2] or 0

    # Today active (since 00:00 today)
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    cursor.execute("SELECT COUNT(*) FROM users WHERE last_active >= ?", (today_start,))
    today_active = cursor.fetchone()[0] or 0

    # Top popular effects
    cursor.execute("""
        SELECT detail, COUNT(*) as cnt
        FROM usage_logs
        WHERE action_type = 'voice_effect' AND detail != ''
        GROUP BY detail
        ORDER BY cnt DESC
        LIMIT 5
    """)
    top_effects = cursor.fetchall()

    conn.close()
    return {
        "total_users": total_users,
        "today_active": today_active,
        "total_voices": total_voices,
        "total_tts": total_tts,
        "top_effects": top_effects
    }


def get_recent_users(limit: int = 10) -> List[dict]:
    """Fetches recently active users."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, username, first_name, joined_at, last_active, voice_count, tts_count
        FROM users
        ORDER BY last_active DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "user_id": r[0],
            "username": r[1],
            "first_name": r[2],
            "joined_at": r[3],
            "last_active": r[4],
            "voice_count": r[5],
            "tts_count": r[6]
        })
    return result


def get_all_user_ids() -> List[int]:
    """Returns all registered user IDs for broadcast announcements."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]


def set_admin_id(admin_id: int):
    """Sets primary admin ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('admin_id', ?)", (str(admin_id),))
    conn.commit()
    conn.close()


def get_admin_id() -> Optional[int]:
    """Gets primary admin ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'admin_id'")
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        try:
            return int(row[0])
        except ValueError:
            return None
    return None


init_db()
