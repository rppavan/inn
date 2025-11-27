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
                current_scene TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scenario_id) REFERENCES scenarios(id)
            )
        """)

        # Scenes table (scene history for an adventure)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                adventure_id INTEGER NOT NULL,
                location_name TEXT DEFAULT '',
                location_description TEXT DEFAULT '',
                characters_present TEXT DEFAULT '[]',
                situation TEXT DEFAULT '',
                mood TEXT DEFAULT '',
                time_of_day TEXT DEFAULT '',
                weather TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (adventure_id) REFERENCES adventures(id) ON DELETE CASCADE
            )
        """)

        # Events table (adventure history)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                adventure_id INTEGER NOT NULL,
                action_type TEXT DEFAULT 'do',
                actor_name TEXT DEFAULT '',
                player_input TEXT DEFAULT '',
                narration TEXT DEFAULT '',
                character_actions TEXT DEFAULT '[]',
                scene_update TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (adventure_id) REFERENCES adventures(id) ON DELETE CASCADE
            )
        """)

        # Character states table (tracks dynamic character state per adventure)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS character_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                adventure_id INTEGER NOT NULL,
                character_name TEXT NOT NULL,
                character_card_id INTEGER,
                is_pc INTEGER DEFAULT 0,
                personality_traits TEXT DEFAULT '[]',
                char_values TEXT DEFAULT '[]',
                fears TEXT DEFAULT '[]',
                speech_style TEXT DEFAULT '',
                current_mood TEXT DEFAULT '',
                current_goal TEXT DEFAULT '',
                long_term_goals TEXT DEFAULT '[]',
                inventory TEXT DEFAULT '[]',
                equipped TEXT DEFAULT '[]',
                relationships TEXT DEFAULT '{}',
                stats TEXT DEFAULT '{}',
                recent_actions_summary TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (adventure_id) REFERENCES adventures(id) ON DELETE CASCADE,
                FOREIGN KEY (character_card_id) REFERENCES story_cards(id),
                UNIQUE(adventure_id, character_name)
            )
        """)

        # Create indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_story_cards_scenario ON story_cards(scenario_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_adventures_scenario ON adventures(scenario_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_adventure ON events(adventure_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scenes_adventure ON scenes(adventure_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_character_states_adventure ON character_states(adventure_id)")


# Initialize database on module import
init_db()
