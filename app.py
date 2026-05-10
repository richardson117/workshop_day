import json
import mimetypes
import os
import subprocess
import sys
import threading
from collections import Counter, defaultdict
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from lobby_db import DEFAULT_DB_PATH, connect, init_db, rows_to_dicts


ROOT = Path(__file__).parent
STATIC_DIR = ROOT / "static"
SUPPORTED_SCAN_GEOS = {"AU", "DE"}
JOBS = {}


CANONICAL_RULES = [
    ("new", ["new", "new releases"]),
    ("top", ["top", "popular", "hot games", "trending"]),
    ("live", ["live", "game shows", "roulette", "blackjack", "baccarat"]),
    ("jackpot", ["jackpot"]),
    ("bonus_buy", ["bonus buy", "buy feature"]),
    ("slots", ["slots", "pokies"]),
]


def load_local_env(path=ROOT / ".env", override=False):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and (override or key not in os.environ):
            os.environ[key] = value


def normalize(value):
    return " ".join(str(value or "").lower().replace("&", "and").split())


def canonical_for_game(game):
    stored = (game.get("category_canonical") or "").strip()
    if stored and stored != "other":
        return stored
    text = normalize(f"{game.get('category') or ''} {game.get('category_label') or ''}")
    for canonical, needles in CANONICAL_RULES:
        if any(needle in text for needle in needles):
            return canonical
    return stored or "other"


def game_key(game):
    return f"{normalize(game.get('title'))}|{normalize(game.get('provider'))}|{canonical_for_game(game)}"


def json_response(handler, payload, status=200):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def query_params(handler):
    parsed = urlparse(handler.path)
    return {key: values[-1] for key, values in parse_qs(parsed.query).items()}


def read_json_body(handler):
    length = int(handler.headers.get("Content-Length") or 0)
    if not length:
        return {}
    return json.loads(handler.rfile.read(length).decode("utf-8"))


def save_proxy_env(payload, path=ROOT / ".env"):
    allowed = {"GEO_PROXY_AU", "GEO_PROXY_DE"}
    current = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line or line.strip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() in allowed:
                current[key.strip()] = value.strip()
    for key in allowed:
        value = (payload.get(key) or "").strip()
        if value:
            current[key] = value
    lines = [f"{key}={current.get(key, '')}" for key in sorted(allowed)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    load_local_env(override=True)
    return {key: bool(os.environ.get(key)) for key in sorted(allowed)}


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_defaults(conn):
    defaults = [
        ("AU", "Australia", "Australia/Sydney", "en-AU,en;q=0.9"),
        ("DE", "Germany", "Europe/Berlin", "de-DE,de;q=0.9,en;q=0.7"),
    ]
    for code, name, timezone_name, accept_language in defaults:
        conn.execute(
            """
            INSERT INTO geos(code, name, timezone, accept_language)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(code) DO NOTHING
            """,
            (code, name, timezone_name, accept_language),
        )
    conn.commit()


def meta(conn):
    load_local_env(override=True)
    geos = rows_to_dicts(conn.execute("SELECT code, name FROM geos ORDER BY code"))
    for geo in geos:
        geo["scan_supported"] = geo["code"] in SUPPORTED_SCAN_GEOS
        geo["proxy_ready"] = bool(os.environ.get(f"GEO_PROXY_{geo['code']}"))
    runs = rows_to_dicts(
        conn.execute(
            """
            SELECT r.id, r.geo_code, r.run_at, r.proxy_country, r.proxy_city,
                   COUNT(g.id) AS game_count
            FROM runs r
            LEFT JOIN brand_runs br ON br.run_id = r.id
            LEFT JOIN games g ON g.brand_run_id = br.id
            GROUP BY r.id
            ORDER BY r.run_at DESC
            """
        )
    )
    brands = rows_to_dicts(
        conn.execute(
            """
            SELECT DISTINCT b.name
            FROM brands b
            JOIN brand_runs br ON br.brand_id = b.id
            ORDER BY b.name
            """
        )
    )
    return {"geos": geos, "runs": runs, "brands": brands}


def pick_run(conn, geo=None, run_id=None):
    if run_id:
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        return row
    row = conn.execute(
        """
        SELECT * FROM runs
        WHERE (? IS NULL OR geo_code = ?)
        ORDER BY run_at DESC
        LIMIT 1
        """,
        (geo, geo),
    ).fetchone()
    return row


def previous_run(conn, run):
    if not run:
        return None
    return conn.execute(
        """
        SELECT * FROM runs
        WHERE geo_code = ? AND project_id = ? AND run_at < ?
        ORDER BY run_at DESC
        LIMIT 1
        """,
        (run["geo_code"], run["project_id"], run["run_at"]),
    ).fetchone()


def load_games(conn, run_id):
    rows = rows_to_dicts(
        conn.execute(
            """
            SELECT b.name AS brand, g.position, g.category, g.category_label,
                   g.category_canonical, g.title, g.provider, g.identity, g.is_geo_available
            FROM games g
            JOIN brand_runs br ON br.id = g.brand_run_id
            JOIN brands b ON b.id = br.brand_id
            WHERE br.run_id = ?
            ORDER BY b.name, g.position
            """,
            (run_id,),
        )
    )
    for row in rows:
        row["canonical"] = canonical_for_game(row)
    return rows


def diff_games(current_games, previous_games, canonical=None):
    result = {}
    brands = sorted({game["brand"] for game in current_games + previous_games})
    for brand in brands:
        current = [game for game in current_games if game["brand"] == brand]
        previous = [game for game in previous_games if game["brand"] == brand]
        if canonical:
            current = [game for game in current if game["canonical"] == canonical]
            previous = [game for game in previous if game["canonical"] == canonical]
        current_by_key = {game_key(game): game for game in current}
        previous_by_key = {game_key(game): game for game in previous}
        added = [current_by_key[key] for key in current_by_key.keys() - previous_by_key.keys()]
        removed = [previous_by_key[key] for key in previous_by_key.keys() - current_by_key.keys()]
        if added or removed:
            result[brand] = {
                "added": sorted(added, key=lambda game: game.get("position") or 999)[:12],
                "removed": sorted(removed, key=lambda game: game.get("position") or 999)[:12],
            }
    return result


def overview(conn, params):
    geo = (params.get("geo") or "AU").upper()
    run = pick_run(conn, geo, params.get("run_id"))
    if not run:
        return {"error": f"No {geo} run found. Import snapshots or run a live scan first."}
    previous = previous_run(conn, run)
    games = load_games(conn, run["id"])
    previous_games = load_games(conn, previous["id"]) if previous else []

    brand = params.get("brand") or "all"
    search = normalize(params.get("search"))
    if brand != "all":
        games = [game for game in games if game["brand"] == brand]
        previous_games = [game for game in previous_games if game["brand"] == brand]
    if search:
        games = [
            game
            for game in games
            if search in normalize(f"{game['brand']} {game['title']} {game.get('provider')} {game.get('category_label')}")
        ]

    providers = Counter(game.get("provider") or "Unknown" for game in games)
    groups = Counter(game["canonical"] for game in games)
    new_section = [game for game in games if game["canonical"] == "new"]
    new_section_diff = diff_games(games, previous_games, "new")
    all_diff = diff_games(games, previous_games)
    return {
        "run": dict(run),
        "previous_run": dict(previous) if previous else None,
        "proxy": {
            "country": run["proxy_country"],
            "city": run["proxy_city"],
        },
        "stats": {
            "games": len(games),
            "new_section_games": len(new_section),
            "brands": len({game["brand"] for game in games}),
            "providers": len(providers),
        },
        "top_providers": providers.most_common(8),
        "groups": groups.most_common(),
        "new_section": new_section[:80],
        "new_section_diff": new_section_diff,
        "diff": all_diff,
        "games": games[:250],
    }


def run_scan(job_id, geo):
    load_local_env(override=True)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env_name = f"GEO_PROXY_{geo}"
    if not env.get(env_name):
        JOBS[job_id].update({"status": "failed", "error": f"Missing {env_name}. Add it in Codespaces secrets or .env."})
        return
    command = [sys.executable, str(ROOT / "competitor_lobby_monitor.py"), "--geo", geo]
    completed = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=240)
    JOBS[job_id].update(
        {
            "status": "done" if completed.returncode == 0 else "failed",
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "error": None if completed.returncode == 0 else f"Collector exited with {completed.returncode}",
            "finished_at": now_iso(),
        }
    )


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/meta":
            with connect(DEFAULT_DB_PATH) as conn:
                init_db(conn)
                ensure_defaults(conn)
                json_response(self, meta(conn))
            return
        if parsed.path == "/api/overview":
            with connect(DEFAULT_DB_PATH) as conn:
                init_db(conn)
                ensure_defaults(conn)
                json_response(self, overview(conn, query_params(self)))
            return
        if parsed.path == "/api/jobs":
            json_response(self, {"jobs": list(JOBS.values())[-10:]})
            return
        self.serve_static(parsed.path)

    def do_POST(self):
        parsed = urlparse(self.path)
        payload = read_json_body(self)
        if parsed.path == "/api/scan":
            geo = (payload.get("geo") or "AU").upper()
            if geo not in SUPPORTED_SCAN_GEOS:
                json_response(self, {"error": f"{geo} collector is not configured in this workshop starter."}, 400)
                return
            job_id = str(len(JOBS) + 1)
            JOBS[job_id] = {"id": job_id, "geo": geo, "status": "running", "started_at": now_iso()}
            threading.Thread(target=run_scan, args=(job_id, geo), daemon=True).start()
            json_response(self, JOBS[job_id])
            return
        if parsed.path == "/api/proxy-env":
            json_response(self, {"ready": save_proxy_env(payload)})
            return
        json_response(self, {"error": "Unknown endpoint"}, 404)

    def serve_static(self, path):
        if path in {"", "/"}:
            path = "/index.html"
        target = (STATIC_DIR / path.lstrip("/")).resolve()
        if not str(target).startswith(str(STATIC_DIR.resolve())) or not target.exists():
            self.send_error(404)
            return
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(str(target))[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def main():
    load_local_env(override=True)
    with connect(DEFAULT_DB_PATH) as conn:
        init_db(conn)
        ensure_defaults(conn)
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("Lobby Radar Starter: http://127.0.0.1:8765")
    server.serve_forever()


if __name__ == "__main__":
    main()
