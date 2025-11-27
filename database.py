"""
SQLite database initialization and connection management for the Lore feature.
"""
import sqlite3
from pathlib import Path
from contextlib import contextmanager

DATABASE_PATH = Path(__file__).parent / "lore.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory enabled."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize the database schema."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Scenarios table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                status TEXT DEFAULT 'draft',
                plot TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Story cards table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS story_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id INTEGER NOT NULL,
                type TEXT DEFAULT 'custom',
                name TEXT NOT NULL,
                entry TEXT DEFAULT '',
                triggers TEXT DEFAULT '[]',
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
            )
        """)

        # Adventures table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adventures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                current_story_summary TEXT DEFAULT '',
                memory TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scenario_id) REFERENCES scenarios(id)
            )
        """)

        # Events table (adventure history)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                adventure_id INTEGER NOT NULL,
                action_type TEXT DEFAULT 'do',
                player_input TEXT DEFAULT '',
                ai_response TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (adventure_id) REFERENCES adventures(id) ON DELETE CASCADE
            )
        """)

        # Create indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_story_cards_scenario ON story_cards(scenario_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_adventures_scenario ON adventures(scenario_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_adventure ON events(adventure_id)")


# Initialize database on module import
init_db()
