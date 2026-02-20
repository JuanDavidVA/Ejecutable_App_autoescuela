import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parents[1]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "driving_exams.db"

COLUMNS = [
    ("province", "Provincia"),
    ("exam_center", "Centro"),
    ("exam_type", "Tipo"),
    ("driving_school", "Autoescuela"),
    ("exam_month", "Mes"),
    ("presented", "Presentados"),
    ("passed", "Aptos"),
    ("failed", "No aptos"),
]


def get_connection():
    DATA_DIR.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                province TEXT,
                exam_center TEXT,
                exam_type TEXT,
                driving_school TEXT,
                exam_month TEXT,
                presented INTEGER,
                passed INTEGER,
                failed INTEGER
            )
        """)
        # Keep only one row per logical record before enforcing uniqueness.
        conn.execute("""
            DELETE FROM exams
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM exams
                GROUP BY
                    province, exam_center, exam_type, driving_school,
                    exam_month, presented, passed, failed
            )
        """)
        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_exams_unique_row
            ON exams (
                province, exam_center, exam_type, driving_school,
                exam_month, presented, passed, failed
            )
        """)


def fetch(sql, params=()):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()