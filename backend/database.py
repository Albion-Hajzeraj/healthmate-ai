"""
Baza e të dhënave (SQLite).

SQLite është një bazë të dhënash që ruhet në një skedar të vetëm
(data/healthmate.db). Nuk ka nevojë për server të veçantë, prandaj
është ideale për një aplikacion personal.
"""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# Dosja e të dhënave (mund të ndryshohet me HEALTHMATE_DATA_DIR, p.sh. për testime)
DATA_DIR = Path(os.getenv("HEALTHMATE_DATA_DIR") or Path(__file__).resolve().parent.parent / "data")
DB_PATH = DATA_DIR / "healthmate.db"
UPLOADS_DIR = DATA_DIR / "uploads"   # fotot e fletëve të analizave

SCHEMA = """
CREATE TABLE IF NOT EXISTS profile (
    id                 INTEGER PRIMARY KEY CHECK (id = 1),
    name               TEXT DEFAULT '',
    birth_year         INTEGER,
    sex                TEXT DEFAULT '',          -- 'F' ose 'M'
    country            TEXT DEFAULT 'ALB',       -- kodi ISO3 për të dhënat e OBSH-së
    height_cm          REAL,
    weight_kg          REAL,
    allergies          TEXT DEFAULT '',
    conditions         TEXT DEFAULT '',          -- sëmundje kronike
    doctor_name        TEXT DEFAULT '',
    doctor_phone       TEXT DEFAULT '',
    emergency_name     TEXT DEFAULT '',
    emergency_phone    TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS lab_results (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    test_key    TEXT NOT NULL,       -- p.sh. 'glucose' ose 'custom'
    test_name   TEXT NOT NULL,
    value       REAL NOT NULL,
    unit        TEXT DEFAULT '',
    ref_low     REAL,
    ref_high    REAL,
    taken_on    TEXT NOT NULL,       -- data YYYY-MM-DD
    note        TEXT DEFAULT '',
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS therapies (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    medication  TEXT NOT NULL,
    dose        TEXT DEFAULT '',     -- p.sh. '500 mg'
    times       TEXT DEFAULT '',     -- p.sh. 'morning,evening'
    reason      TEXT DEFAULT '',
    start_date  TEXT,
    end_date    TEXT,                -- bosh = ende aktive
    notes       TEXT DEFAULT '',
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dose_log (
    therapy_id  INTEGER NOT NULL,
    day         TEXT NOT NULL,
    slot        TEXT NOT NULL,       -- morning / noon / evening / night
    PRIMARY KEY (therapy_id, day, slot),
    FOREIGN KEY (therapy_id) REFERENCES therapies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS symptoms (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    severity    INTEGER DEFAULT 5,   -- 1 (lehtë) deri 10 (shumë e rëndë)
    started_on  TEXT,
    notes       TEXT DEFAULT '',
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lab_reports (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    taken_on    TEXT NOT NULL,       -- data e analizave
    content     TEXT NOT NULL,       -- raporti i shkruar nga asistenti
    image_file  TEXT,                -- emri i fotos në data/uploads (nëse ka)
    item_count  INTEGER DEFAULT 0,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    role        TEXT NOT NULL,       -- 'user' ose 'assistant'
    content     TEXT NOT NULL,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO profile (id) VALUES (1);
"""


def init_db() -> None:
    """Krijon skedarin e bazës dhe tabelat nëse nuk ekzistojnë."""
    DATA_DIR.mkdir(exist_ok=True)
    UPLOADS_DIR.mkdir(exist_ok=True)
    with get_conn() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def get_conn():
    """Hap një lidhje me bazën; e ruan (commit) dhe e mbyll në fund."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def rows(cursor) -> list[dict]:
    """Kthen rreshtat e një query-je si listë fjalorësh (dict)."""
    return [dict(r) for r in cursor.fetchall()]
