import json
import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = Path("data") / "lobby_monitor.sqlite3"
DEFAULT_PROJECT = "Casino Lobby Radar"


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  slug TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS geos (
  code TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  timezone TEXT,
  accept_language TEXT
);

CREATE TABLE IF NOT EXISTS brands (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  name TEXT NOT NULL,
  slug TEXT NOT NULL,
  default_url TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(project_id, slug)
);

CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  geo_code TEXT NOT NULL REFERENCES geos(code),
  run_at TEXT NOT NULL,
  proxy_country TEXT,
  proxy_city TEXT,
  proxy_ip TEXT,
  source_path TEXT,
  raw_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(project_id, geo_code, run_at)
);

CREATE TABLE IF NOT EXISTS brand_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
  brand_id INTEGER NOT NULL REFERENCES brands(id),
  status TEXT NOT NULL,
  site_url TEXT,
  detected_json TEXT,
  errors_json TEXT,
  UNIQUE(run_id, brand_id)
);

CREATE TABLE IF NOT EXISTS games (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  brand_run_id INTEGER NOT NULL REFERENCES brand_runs(id) ON DELETE CASCADE,
  position INTEGER NOT NULL,
  category TEXT,
  category_label TEXT,
  category_canonical TEXT,
  title TEXT NOT NULL,
  provider TEXT,
  provider_id TEXT,
  identity TEXT,
  seo_title TEXT,
  is_geo_available INTEGER,
  provider_blocked_countries_json TEXT,
  collections_json TEXT,
  image_url TEXT,
  UNIQUE(brand_run_id, position, identity)
);

CREATE TABLE IF NOT EXISTS scan_jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  geo_code TEXT NOT NULL REFERENCES geos(code),
  status TEXT NOT NULL,
  requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  started_at TEXT,
  finished_at TEXT,
  run_id INTEGER REFERENCES runs(id),
  stdout TEXT,
  stderr TEXT,
  error TEXT
);

CREATE TABLE IF NOT EXISTS schedules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  geo_code TEXT NOT NULL REFERENCES geos(code),
  cadence TEXT NOT NULL,
  time_of_day TEXT,
  day_of_week INTEGER,
  enabled INTEGER NOT NULL DEFAULT 1,
  last_run_at TEXT,
  next_run_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(project_id, geo_code, cadence)
);

CREATE INDEX IF NOT EXISTS idx_runs_project_geo_time ON runs(project_id, geo_code, run_at DESC);
CREATE INDEX IF NOT EXISTS idx_games_brand_run_position ON games(brand_run_id, position);
CREATE INDEX IF NOT EXISTS idx_games_provider ON games(provider);
CREATE INDEX IF NOT EXISTS idx_games_category ON games(category);
CREATE INDEX IF NOT EXISTS idx_scan_jobs_requested ON scan_jobs(requested_at DESC);
CREATE INDEX IF NOT EXISTS idx_schedules_next_run ON schedules(enabled, next_run_at);
"""


def slugify(value):
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-").replace("--", "-")


def connect(db_path=DEFAULT_DB_PATH):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn):
    conn.executescript(SCHEMA)
    ensure_migrations(conn)
    conn.commit()


def ensure_migrations(conn):
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(games)")}
    for name, definition in {
        "category_label": "TEXT",
        "category_canonical": "TEXT",
    }.items():
        if name not in columns:
            conn.execute(f"ALTER TABLE games ADD COLUMN {name} {definition}")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_games_category_canonical ON games(category_canonical)")


def ensure_project(conn, name=DEFAULT_PROJECT):
    slug = slugify(name)
    conn.execute(
        "INSERT OR IGNORE INTO projects(name, slug) VALUES(?, ?)",
        (name, slug),
    )
    row = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
    return row["id"]


def ensure_geo(conn, snapshot_geo):
    code = snapshot_geo["country_code"]
    conn.execute(
        """
        INSERT INTO geos(code, name, timezone, accept_language)
        VALUES(?, ?, ?, ?)
        ON CONFLICT(code) DO UPDATE SET
          name = excluded.name,
          timezone = excluded.timezone,
          accept_language = excluded.accept_language
        """,
        (
            code,
            snapshot_geo.get("label") or code,
            snapshot_geo.get("timezone"),
            snapshot_geo.get("accept_language"),
        ),
    )
    return code


def ensure_brand(conn, project_id, competitor):
    name = competitor["competitor"]
    slug = slugify(name)
    conn.execute(
        """
        INSERT INTO brands(project_id, name, slug, default_url)
        VALUES(?, ?, ?, ?)
        ON CONFLICT(project_id, slug) DO UPDATE SET
          name = excluded.name,
          default_url = excluded.default_url
        """,
        (project_id, name, slug, competitor.get("site_url")),
    )
    row = conn.execute(
        "SELECT id FROM brands WHERE project_id = ? AND slug = ?",
        (project_id, slug),
    ).fetchone()
    return row["id"]


def bool_to_int(value):
    if value is None:
        return None
    return 1 if bool(value) else 0


def ingest_snapshot(conn, snapshot, source_path=None, project_name=DEFAULT_PROJECT):
    init_db(conn)
    project_id = ensure_project(conn, project_name)
    geo_code = ensure_geo(conn, snapshot["geo"])
    proxy = snapshot.get("proxy_check") or {}
    conn.execute(
        """
        INSERT OR IGNORE INTO runs(
          project_id, geo_code, run_at, proxy_country, proxy_city, proxy_ip, source_path, raw_json
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            project_id,
            geo_code,
            snapshot["run_at"],
            proxy.get("country"),
            proxy.get("city"),
            proxy.get("ip"),
            str(source_path) if source_path else None,
            json.dumps(snapshot, ensure_ascii=False),
        ),
    )
    run = conn.execute(
        "SELECT id FROM runs WHERE project_id = ? AND geo_code = ? AND run_at = ?",
        (project_id, geo_code, snapshot["run_at"]),
    ).fetchone()
    run_id = run["id"]

    for competitor in snapshot.get("competitors", []):
        brand_id = ensure_brand(conn, project_id, competitor)
        conn.execute(
            """
            INSERT OR REPLACE INTO brand_runs(
              run_id, brand_id, status, site_url, detected_json, errors_json
            )
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                brand_id,
                competitor.get("status") or "unknown",
                competitor.get("site_url"),
                json.dumps(competitor.get("detected") or {}, ensure_ascii=False),
                json.dumps(competitor.get("errors") or [], ensure_ascii=False),
            ),
        )
        brand_run_id = conn.execute(
            "SELECT id FROM brand_runs WHERE run_id = ? AND brand_id = ?",
            (run_id, brand_id),
        ).fetchone()["id"]
        conn.execute("DELETE FROM games WHERE brand_run_id = ?", (brand_run_id,))
        for game in competitor.get("games", []):
            conn.execute(
                """
                INSERT INTO games(
                  brand_run_id, position, category, category_label, category_canonical,
                  title, provider, provider_id, identity,
                  seo_title, is_geo_available, provider_blocked_countries_json,
                  collections_json, image_url
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    brand_run_id,
                    game.get("position"),
                    game.get("category"),
                    game.get("category_label"),
                    game.get("category_canonical"),
                    game.get("title"),
                    game.get("provider"),
                    game.get("provider_id"),
                    game.get("identity"),
                    game.get("seo_title"),
                    bool_to_int(game.get("is_geo_available")),
                    json.dumps(game.get("provider_blocked_countries") or [], ensure_ascii=False),
                    json.dumps(game.get("collections") or [], ensure_ascii=False),
                    game.get("image_url"),
                ),
            )
    conn.commit()
    return run_id


def ingest_snapshot_file(db_path, snapshot_path, project_name=DEFAULT_PROJECT):
    snapshot_file = Path(snapshot_path)
    snapshot = json.loads(snapshot_file.read_text(encoding="utf-8"))
    with connect(db_path) as conn:
        return ingest_snapshot(conn, snapshot, snapshot_file, project_name)


def ingest_snapshot_folder(db_path=DEFAULT_DB_PATH, folder="snapshots", project_name=DEFAULT_PROJECT):
    folder_path = Path(folder)
    imported = []
    with connect(db_path) as conn:
        init_db(conn)
        for path in sorted(folder_path.glob("*.json")):
            snapshot = json.loads(path.read_text(encoding="utf-8"))
            imported.append(ingest_snapshot(conn, snapshot, path, project_name))
    return imported


def rows_to_dicts(rows):
    return [dict(row) for row in rows]
