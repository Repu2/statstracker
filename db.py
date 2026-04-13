from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(os.environ.get("SCRIMTRACKER_DB", "scrimtracker.sqlite3"))


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def db() -> sqlite3.Connection:
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def _row_count(conn: sqlite3.Connection, table: str) -> int:
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except sqlite3.OperationalError:
        return 0


def _cleanup_old_new_tables(conn: sqlite3.Connection) -> None:
    """Drop _old and _new tables, consolidate into single working tables."""
    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        for main in ("scrims", "scrim_maps", "player_map_stats"):
            old_t = f"{main}_old"
            new_t = f"{main}_new"
            has_main = _table_exists(conn, main)
            has_old = _table_exists(conn, old_t)
            has_new = _table_exists(conn, new_t)

            if has_old or has_new:
                if has_main:
                    main_rows = _row_count(conn, main)
                    new_rows = _row_count(conn, new_t) if has_new else 0
                    old_rows = _row_count(conn, old_t) if has_old else 0
                    # If main is empty but _new or _old has data, use that
                    if main_rows == 0 and (new_rows > 0 or old_rows > 0):
                        conn.execute(f"DROP TABLE {main}")
                        src = new_t if new_rows >= old_rows else old_t
                        conn.execute(f"ALTER TABLE {src} RENAME TO {main}")
                        conn.execute(f"DROP TABLE IF EXISTS {old_t}")
                        conn.execute(f"DROP TABLE IF EXISTS {new_t}")
                    else:
                        conn.execute(f"DROP TABLE IF EXISTS {old_t}")
                        conn.execute(f"DROP TABLE IF EXISTS {new_t}")
                else:
                    src = new_t if has_new else old_t
                    conn.execute(f"ALTER TABLE {src} RENAME TO {main}")
                    conn.execute(f"DROP TABLE IF EXISTS {old_t}")
                    conn.execute(f"DROP TABLE IF EXISTS {new_t}")

        # Fix player_map_stats FK if it references scrim_maps_old or scrim_maps_new
        if _table_exists(conn, "player_map_stats"):
            try:
                fks = conn.execute("PRAGMA foreign_key_list(player_map_stats)").fetchall()
                for fk in fks:
                    if fk[2] in ("scrim_maps_old", "scrim_maps_new"):
                        _recreate_player_map_stats(conn)
                        break
            except sqlite3.OperationalError:
                pass
    finally:
        conn.execute("PRAGMA foreign_keys = ON")


def _recreate_player_map_stats(conn: sqlite3.Connection) -> None:
    """Recreate player_map_stats with correct FK to scrim_maps."""
    old_cols = {row[1] for row in conn.execute("PRAGMA table_info(player_map_stats)")}
    conn.execute("DROP TABLE IF EXISTS player_map_stats_new")
    conn.execute(
        """
        CREATE TABLE player_map_stats_new (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          scrim_map_id INTEGER NOT NULL REFERENCES scrim_maps(id) ON DELETE CASCADE,
          player_name TEXT NOT NULL,
          agent TEXT,
          kills INTEGER,
          deaths INTEGER,
          assists INTEGER,
          acs INTEGER,
          kast_pct REAL,
          first_kills INTEGER,
          first_deaths INTEGER,
          notes TEXT,
          created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    sel_parts = ["id", "scrim_map_id", "player_name", "agent", "kills", "deaths", "assists", "acs"]
    sel_parts.append("kast_pct" if "kast_pct" in old_cols else "0 AS kast_pct")
    sel_parts.extend(["first_kills", "first_deaths", "notes"])
    sel_parts.append(
        "COALESCE(created_at, datetime('now')) AS created_at"
        if "created_at" in old_cols
        else "datetime('now') AS created_at"
    )
    ins_cols = "id, scrim_map_id, player_name, agent, kills, deaths, assists, acs, kast_pct, first_kills, first_deaths, notes, created_at"
    conn.execute(
        f"INSERT INTO player_map_stats_new ({ins_cols}) SELECT {', '.join(sel_parts)} FROM player_map_stats"
    )
    conn.execute("DROP TABLE player_map_stats")
    conn.execute("ALTER TABLE player_map_stats_new RENAME TO player_map_stats")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_stats_map_id ON player_map_stats(scrim_map_id)")


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with db() as conn:
        # Avoid orphaned _old table references from ALTER TABLE + foreign keys (SQLite 3.25+)
        conn.execute("PRAGMA legacy_alter_table = ON;")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS scrims (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              played_on TEXT NOT NULL,                 -- YYYY-MM-DD
              match_kind TEXT NOT NULL DEFAULT 'scrim', -- 'scrim' or 'official'
              official_type TEXT,                      -- 'tournament' or 'premier' (optional)
              event_name TEXT,                         -- tournament name / premier stage (optional)
              opponent TEXT NOT NULL,
              patch TEXT,
              vod_url TEXT,
              notes TEXT,
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS scrim_maps (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              scrim_id INTEGER NOT NULL REFERENCES scrims(id) ON DELETE CASCADE,
              map_name TEXT NOT NULL,
              our_score INTEGER NOT NULL,
              opp_score INTEGER NOT NULL,
              our_attack_rounds INTEGER,
              our_def_rounds INTEGER,
              opp_attack_rounds INTEGER,
              opp_def_rounds INTEGER,
              our_pistol_atk_won INTEGER, -- 1/0, optional
              our_pistol_def_won INTEGER, -- 1/0, optional
              notes TEXT,
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS player_map_stats (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              scrim_map_id INTEGER NOT NULL REFERENCES scrim_maps(id) ON DELETE CASCADE,
              player_name TEXT NOT NULL,
              agent TEXT,
              kills INTEGER,
              deaths INTEGER,
              assists INTEGER,
              acs INTEGER,
              kast_pct REAL,
              first_kills INTEGER,
              first_deaths INTEGER,
              notes TEXT,
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_scrims_played_on ON scrims(played_on);
            CREATE INDEX IF NOT EXISTS idx_maps_scrim_id ON scrim_maps(scrim_id);
            CREATE INDEX IF NOT EXISTS idx_stats_map_id ON player_map_stats(scrim_map_id);

            CREATE TABLE IF NOT EXISTS app_settings (
              key TEXT PRIMARY KEY,
              value TEXT
            );
            """
        )

        cols = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(player_map_stats);").fetchall()
        }
        if "kast_pct" not in cols:
            conn.execute("ALTER TABLE player_map_stats ADD COLUMN kast_pct REAL;")

        scrim_cols = {
            row["name"] for row in conn.execute("PRAGMA table_info(scrims);").fetchall()
        }
        if "match_kind" not in scrim_cols:
            conn.execute(
                "ALTER TABLE scrims ADD COLUMN match_kind TEXT NOT NULL DEFAULT 'scrim';"
            )
        if "official_type" not in scrim_cols:
            conn.execute("ALTER TABLE scrims ADD COLUMN official_type TEXT;")
        if "event_name" not in scrim_cols:
            conn.execute("ALTER TABLE scrims ADD COLUMN event_name TEXT;")
        if "skill_level" not in scrim_cols:
            conn.execute("ALTER TABLE scrims ADD COLUMN skill_level TEXT;")

        scrim_map_cols = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(scrim_maps);").fetchall()
        }
        if "our_pistol_atk_won" not in scrim_map_cols:
            conn.execute("ALTER TABLE scrim_maps ADD COLUMN our_pistol_atk_won INTEGER;")
        if "our_pistol_def_won" not in scrim_map_cols:
            conn.execute("ALTER TABLE scrim_maps ADD COLUMN our_pistol_def_won INTEGER;")

        # Cleanup: remove _old and _new tables, consolidate into single working tables
        _cleanup_old_new_tables(conn)
