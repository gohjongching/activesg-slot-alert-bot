import sqlite3
from datetime import datetime, timedelta
from typing import Optional
from config import Config

def get_connection():
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_slots (
                slot_id TEXT PRIMARY KEY,
                venue TEXT NOT NULL,
                activity TEXT NOT NULL,
                date TEXT NOT NULL,
                time_slot TEXT NOT NULL,
                court_no TEXT,
                first_seen TIMESTAMP NOT NULL,
                last_seen TIMESTAMP NOT NULL,
                last_alerted TIMESTAMP NOT NULL
            )
        """)
        conn.commit()

def is_slot_recently_alerted(slot_id: str, cooldown_hours: int = 4) -> bool:
    """
    Returns True if an alert for this exact slot was sent within cooldown_hours.
    """
    cutoff = datetime.now() - timedelta(hours=cooldown_hours)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT last_alerted FROM seen_slots WHERE slot_id = ?",
            (slot_id,)
        )
        row = cursor.fetchone()
        if not row:
            return False
        
        last_alerted = datetime.fromisoformat(row["last_alerted"])
        return last_alerted > cutoff

def record_slot_alert(
    slot_id: str,
    venue: str,
    activity: str,
    date: str,
    time_slot: str,
    court_no: Optional[str] = None
):
    now = datetime.now().isoformat()
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO seen_slots (
                slot_id, venue, activity, date, time_slot, court_no,
                first_seen, last_seen, last_alerted
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slot_id) DO UPDATE SET
                last_seen = excluded.last_seen,
                last_alerted = excluded.last_alerted
        """, (slot_id, venue, activity, date, time_slot, court_no or "", now, now, now))
        conn.commit()

def clean_old_slots(days_old: int = 7):
    """
    Removes entries older than days_old to keep DB lightweight.
    """
    cutoff = (datetime.now() - timedelta(days=days_old)).isoformat()
    with get_connection() as conn:
        conn.execute("DELETE FROM seen_slots WHERE last_seen < ?", (cutoff,))
        conn.commit()
