import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS wardrobe_items (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT,
    colors TEXT NOT NULL,
    source TEXT NOT NULL,
    verification_status TEXT NOT NULL,
    asset_id TEXT,
    analysis_job_id TEXT UNIQUE,
    analysis_provider TEXT,
    analysis_unknown_attributes TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
    ,representation TEXT
    ,verified_attributes TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_wardrobe_items_user_id
ON wardrobe_items (user_id);

CREATE TABLE IF NOT EXISTS feedback (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    wardrobe_item_id TEXT NOT NULL,
    action TEXT NOT NULL,
    context TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_feedback_user_id
ON feedback (user_id);
"""


def initialize_database(database_path: str) -> None:
    path = Path(database_path)
    if path != Path(":memory:"):
        path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        connection.executescript(SCHEMA)
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(wardrobe_items)")
        }
        additions = {
            "asset_id": "TEXT",
            "analysis_job_id": "TEXT",
            "analysis_provider": "TEXT",
            "analysis_unknown_attributes": "TEXT NOT NULL DEFAULT '[]'",
            "representation": "TEXT",
            "verified_attributes": "TEXT NOT NULL DEFAULT '{}'",
        }
        for name, definition in additions.items():
            if name not in columns:
                connection.execute(f"ALTER TABLE wardrobe_items ADD COLUMN {name} {definition}")
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_wardrobe_items_analysis_job "
            "ON wardrobe_items (analysis_job_id) WHERE analysis_job_id IS NOT NULL"
        )
