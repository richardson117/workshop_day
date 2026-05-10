import argparse
import csv
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from time import sleep

from lobby_db import DEFAULT_DB_PATH, DEFAULT_PROJECT, connect, ingest_snapshot


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121 Safari/537.36"
)

GEO_SUFFIX = {"AU": "au", "DE": "de"}
LUCKY_LOCALE = {"AU": "en-AU", "DE": "de"}

CANONICAL_RULES = [
    ("bonus_wagering", ["bonus wagering", "bonus wager", "bonus friendly", "wagering bonus"]),
    ("recommended", ["recommended", "rec"]),
    ("top", ["top", "popular", "hot games", "trending"]),
    ("new", ["new", "new releases"]),
    ("crypto", ["crypto", "btc"]),
    ("jackpot", ["jackpot"]),
    ("bonus_buy", ["bonus buy", "buy feature", "buyfeature"]),
    ("megaways", ["megaways"]),
    ("table", ["table"]),
    ("live", ["live", "game shows", "roulette", "blackjack", "baccarat"]),
    ("slots", ["slots", "pokies"]),
    ("crash", ["crash"]),
    ("coins", ["coin"]),
    ("scratch", ["scratch"]),
]

GEO = {
    "AU": {
        "label": "Australia",
        "accept_language": "en-AU,en;q=0.9",
        "timezone": "Australia/Sydney",
        "env_proxy": "GEO_PROXY_AU",
        "rocketplay_url": "https://rocketplay.com/en-AU/",
        "rocketplay_category": "top:au",
        "lucky_url": "https://www.luckydreams.com/en-AU",
        "lucky_category": "popular:en-AU",
    },
    "DE": {
        "label": "Germany",
        "accept_language": "de-DE,de;q=0.9,en;q=0.7",
        "timezone": "Europe/Berlin",
        "env_proxy": "GEO_PROXY_DE",
        "rocketplay_url": "https://rocketplay.com/de-DE/",
        "rocketplay_category": "top:de",
        "lucky_url": "https://www.luckydreams.com/de-DE",
        "lucky_category": "popular:de-DE",
    }
}


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_opener(proxy_url=None):
    handlers = []
    if proxy_url:
        handlers.append(urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url}))
    return urllib.request.build_opener(*handlers)


def request_json(opener, method, url, headers=None, body=None, timeout=25):
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with opener.open(req, timeout=timeout) as response:
        raw = response.read()
        text = raw.decode(response.headers.get_content_charset() or "utf-8", errors="replace")
        return {
            "status": response.status,
            "url": response.geturl(),
            "headers": dict(response.headers.items()),
            "json": json.loads(text),
        }


def request_text(opener, url, headers=None, timeout=25, max_bytes=900_000):
    req = urllib.request.Request(url, headers=headers or {})
    with opener.open(req, timeout=timeout) as response:
        raw = response.read(max_bytes)
        return {
            "status": response.status,
            "url": response.geturl(),
            "headers": dict(response.headers.items()),
            "text": raw.decode(response.headers.get_content_charset() or "utf-8", errors="replace"),
        }


def safe_request(fn, *args, retries=2, **kwargs):
    last_error = None
    for attempt in range(retries + 1):
        try:
            return fn(*args, **kwargs), None
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP {exc.code}: {exc.reason}"
            if exc.code < 500:
                break
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        if attempt < retries:
            sleep(1.5 * (attempt + 1))
    return None, last_error


def detect_title(html_text):
    match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.I | re.S)
    return re.sub(r"\s+", " ", match.group(1)).strip() if match else ""


def detect_rocket_context(html_text):
    match = re.search(r"context\.js\?[^\"']+", html_text)
    if not match:
        return {}
    query = urllib.parse.urlsplit("https://x/" + match.group(0)).query
    params = urllib.parse.parse_qs(query)
    return {key: values[0] for key, values in params.items() if values}


def normalize_text(value):
    return re.sub(r"\s+", " ", (value or "").strip())


def canonical_category(title, identity):
    text = f"{identity or ''} {title or ''}".lower().replace("-", " ").replace("_", " ")
    for canonical, needles in CANONICAL_RULES:
        if any(needle in text for needle in needles):
            return canonical
    return "other"


def collection_id(item):
    return item.get("id") or item.get("identity") or item.get("identifier") or ""


def collection_title(item):
    return normalize_text(item.get("title") or item.get("name") or collection_id(item))


def enrich_collection(item):
    identity = collection_id(item)
    title = collection_title(item)
    return {
        "id": identity,
        "title": title,
        "games_count": item.get("games_count") or item.get("gamesCount"),
        "canonical": canonical_category(title, identity),
        "raw": item,
    }


def is_noisy_collection(item):
    text = f"{item['id']} {item['title']}".lower()
    noisy = [
        "test",
        "invite only",
        "tournament",
        "calendar",
        "points",
        "double points",
        "triple points",
        "cashboost",
        "leaderboard",
        "drops",
        "race",
    ]
    return any(word in text for word in noisy)


def pick_by_ids(collections, ids):
    by_id = {item["id"]: item for item in collections}
    picked = []
    seen = set()
    for identity in ids:
        item = by_id.get(identity)
        if item and item["id"] not in seen:
            picked.append(item)
            seen.add(item["id"])
    return picked, seen


def select_rocket_lobby_collections(raw_collections, geo_code):
    collections = [enrich_collection(item) for item in raw_collections]
    suffix = GEO_SUFFIX.get(geo_code, geo_code.lower())
    preferred_ids = [
        f"top:{suffix}",
        f"recommended:{suffix}",
        "new",
        "bonus-wagering",
        "btc-games",
        "jackpot",
        "coin",
        "megaways",
        "bonus-buy",
        "table",
        "live",
        "crash-games",
        "game-shows",
        "blackjack",
        "roulette",
    ]
    picked, seen = pick_by_ids(collections, preferred_ids)
    for item in collections:
        if len(picked) >= 16:
            break
        if item["id"] in seen or is_noisy_collection(item):
            continue
        if ":" in item["id"] and not item["id"].endswith(f":{suffix}"):
            continue
        if item["canonical"] in {"other"}:
            continue
        picked.append(item)
        seen.add(item["id"])
    return picked


def select_lucky_lobby_collections(raw_collections, geo_code):
    collections = [enrich_collection(item) for item in raw_collections]
    locale = LUCKY_LOCALE.get(geo_code, geo_code.lower())
    preferred_ids = [
        f"popular:{locale}",
        f"recommended:{locale}",
        f"jackpot_games:{locale}",
        "trending",
        "crash",
        "live",
        "live-casino",
        "bonus-buy",
        "megaways",
        "table-games",
    ]
    picked, seen = pick_by_ids(collections, preferred_ids)
    for item in collections:
        if len(picked) >= 14:
            break
        if item["id"] in seen or is_noisy_collection(item):
            continue
        if ":" in item["id"] and locale.lower() not in item["id"].lower():
            continue
        if item["canonical"] in {"other"}:
            continue
        picked.append(item)
        seen.add(item["id"])
    return picked


def select_onlywin_lobby_collections(raw_collections, geo_code):
    collections = [enrich_collection(item) for item in raw_collections]
    picked = []
    seen = set()
    for item in collections:
        if len(picked) >= 18:
            break
        if item["id"] in seen or is_noisy_collection(item):
            continue
        if "adult" in f"{item['id']} {item['title']}".lower():
            continue
        picked.append(item)
        seen.add(item["id"])
    return picked


def compact_category_game(game, position, category):
    item = compact_game(game, position, category["id"])
    original_identity = item.get("identity") or f"{item.get('provider')}::{item.get('title')}"
    item["identity"] = f"{category['id']}::{original_identity}"
    item["category_label"] = category["title"]
    item["category_canonical"] = category["canonical"]
    return item


def compact_game(game, position, category):
    provider = game.get("provider")
    if isinstance(provider, dict):
        provider_name = provider.get("name") or provider.get("identity")
        provider_id = provider.get("identity") or provider.get("id")
        blocked_countries = provider.get("blockedCountries") or []
    else:
        provider_name = provider
        provider_id = provider
        blocked_countries = []

    collections = game.get("collections") or game.get("categories") or []
    if collections and isinstance(collections[0], dict):
        collections = [item.get("identity") or item.get("name") for item in collections]

    image_url = ""
    images = game.get("images") or {}
    if isinstance(images, dict):
        for group in ("universal", "200x300", "200x200"):
            if isinstance(images.get(group), dict):
                image_url = images[group].get("1x") or images[group].get("2x") or ""
                break

    return {
        "position": position,
        "category": category,
        "title": game.get("title") or game.get("name") or "",
        "provider": provider_name or "",
        "provider_id": provider_id or "",
        "identity": game.get("identifier") or game.get("identity") or "",
        "seo_title": game.get("seo_title") or "",
        "is_geo_available": game.get("is_geo_available"),
        "provider_blocked_countries": blocked_countries,
        "collections": [item for item in collections if item],
        "image_url": image_url,
    }


def fetch_rocketplay(opener, geo):
    site_url = geo["rocketplay_url"]
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": geo["accept_language"],
        "Referer": site_url,
    }
    page, page_error = safe_request(
        request_text,
        opener,
        site_url,
        {**headers, "Accept": "text/html,*/*"},
    )
    collections, collections_error = safe_request(
        request_json,
        opener,
        "GET",
        "https://rocketplay.com/api/games/collections",
        headers,
    )
    selected_categories = select_rocket_lobby_collections(collections["json"] if collections else [], geo["code"])
    all_games = []
    category_errors = []
    for category in selected_categories:
        body = {
            "device": "desktop",
            "filter": {"categories": {"identifiers": [category["id"]], "strategy": "OR"}},
            "page": 1,
            "page_size": 20,
        }
        games, games_error = safe_request(
            request_json,
            opener,
            "POST",
            "https://rocketplay.com/api/games_filter",
            {**headers, "Content-Type": "application/json"},
            body,
        )
        if games_error:
            category_errors.append(f"{category['title']}: {games_error}")
        raw_games = games["json"].get("data", []) if games else []
        all_games.extend(compact_category_game(game, index + 1, category) for index, game in enumerate(raw_games))
    page_text = page["text"] if page else ""
    return {
        "competitor": "RocketPlay",
        "site_url": site_url,
        "status": "ok" if all_games else "partial",
        "errors": [e for e in [page_error, collections_error] if e] + category_errors,
        "detected": {
            "title": detect_title(page_text),
            "context": detect_rocket_context(page_text),
            "lobby_categories": len(selected_categories),
        },
        "collections": selected_categories,
        "games": all_games,
    }


def fetch_lucky_dreams(opener, geo):
    site_url = geo["lucky_url"]
    base_headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": geo["accept_language"],
        "Referer": site_url,
        "X-Content-Policy": "1",
    }
    ip_data, ip_error = safe_request(
        request_json,
        opener,
        "GET",
        "https://www.luckydreams.com/api/current_ip",
        {**base_headers, "Accept": "application/json"},
    )
    collections, collections_error = safe_request(
        request_json,
        opener,
        "GET",
        "https://www.luckydreams.com/api/games/collections?device=desktop",
        {**base_headers, "Accept": "application/vnd.s.v1+json"},
    )
    selected_categories = select_lucky_lobby_collections(collections["json"] if collections else [], geo["code"])
    all_games = []
    category_errors = []
    for category in selected_categories:
        body = {
            "device": "desktop",
            "filter": {"categories": {"identifiers": [category["id"]], "strategy": "OR"}},
            "page": 1,
            "page_size": 20,
        }
        games, games_error = safe_request(
            request_json,
            opener,
            "POST",
            "https://www.luckydreams.com/api/games_filter",
            {**base_headers, "Accept": "application/vnd.s.v2+json", "Content-Type": "application/json"},
            body,
        )
        if games_error:
            category_errors.append(f"{category['title']}: {games_error}")
        raw_games = games["json"].get("data", []) if games else []
        all_games.extend(compact_category_game(game, index + 1, category) for index, game in enumerate(raw_games))
    return {
        "competitor": "Lucky Dreams",
        "site_url": site_url,
        "status": "ok" if all_games else "partial",
        "errors": [e for e in [ip_error, collections_error] if e] + category_errors,
        "detected": {"current_ip": ip_data["json"] if ip_data else {}, "lobby_categories": len(selected_categories)},
        "collections": selected_categories,
        "games": all_games,
    }


def fetch_onlywin(opener, geo):
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": geo["accept_language"],
        "Referer": "https://only1.win/",
    }
    page, page_error = safe_request(
        request_text,
        opener,
        "https://only1.win/",
        {**headers, "Accept": "text/html,*/*"},
    )
    collections, collections_error = safe_request(
        request_json,
        opener,
        "GET",
        "https://only1.win/api/game/collections",
        headers,
    )
    raw_collections = collections["json"].get("data", []) if collections else []
    selected_categories = select_onlywin_lobby_collections(raw_collections, geo["code"])
    all_games = []
    category_errors = []
    for category in selected_categories:
        category_id = category["raw"].get("id")
        query = urllib.parse.urlencode({"page": 1, "perPage": 20, "collectionId": category_id or ""})
        games, games_error = safe_request(
            request_json,
            opener,
            "GET",
            f"https://only1.win/api/game/games?{query}",
            headers,
        )
        if games_error:
            category_errors.append(f"{category['title']}: {games_error}")
        raw_games = games["json"].get("data", []) if games else []
        all_games.extend(compact_category_game(game, index + 1, category) for index, game in enumerate(raw_games))
    category_id = None
    if collections:
        for item in collections["json"].get("data", []):
            if item.get("identity") == "top":
                category_id = item.get("id")
                break
    return {
        "competitor": "OnlyWin",
        "site_url": "https://only1.win/",
        "status": "ok" if all_games else "partial",
        "errors": [e for e in [page_error, collections_error] if e] + category_errors,
        "detected": {
            "title": detect_title(page["text"] if page else ""),
            "collection_id": category_id,
            "lobby_categories": len(selected_categories),
        },
        "collections": selected_categories,
        "games": all_games,
    }


def summarize(snapshot):
    lines = [
        f"# {snapshot['geo']['country_code']} Competitor Lobby Snapshot",
        "",
        f"- Run at: `{snapshot['run_at']}`",
        f"- Requested geo: `{snapshot['geo']['country_code']} / {snapshot['geo']['label']}`",
        f"- Proxy check: `{snapshot['proxy_check'].get('country', 'unknown')}` / `{snapshot['proxy_check'].get('city', 'unknown')}` / `{snapshot['proxy_check'].get('ip', 'unknown')}`",
        "",
    ]
    for competitor in snapshot["competitors"]:
        games = competitor["games"]
        providers = Counter(game["provider"] or "Unknown" for game in games)
        lines.extend(
            [
                f"## {competitor['competitor']}",
                "",
                f"- Status: `{competitor['status']}`",
                f"- URL: {competitor['site_url']}",
                f"- Games captured: `{len(games)}`",
                f"- Top providers: {', '.join(f'{name} ({count})' for name, count in providers.most_common(5)) or 'n/a'}",
            ]
        )
        if competitor["errors"]:
            lines.append(f"- Notes: {'; '.join(competitor['errors'])}")
        detected = competitor.get("detected") or {}
        if detected:
            lines.append(f"- Detected context: `{json.dumps(detected, ensure_ascii=False)[:500]}`")
        lines.append("")
        lines.append("| # | Game | Provider | Category | Geo available |")
        lines.append("|---:|---|---|---|---|")
        for game in games[:10]:
            lines.append(
                f"| {game['position']} | {game['title']} | {game['provider']} | "
                f"{game['category']} | {game['is_geo_available']} |"
            )
        lines.append("")
    return "\n".join(lines)


def write_csv(path, snapshot):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "run_at",
                "geo",
                "competitor",
                "position",
                "category",
                "title",
                "provider",
                "provider_id",
                "identity",
                "seo_title",
                "is_geo_available",
            ],
        )
        writer.writeheader()
        for competitor in snapshot["competitors"]:
            for game in competitor["games"]:
                writer.writerow(
                    {
                        "run_at": snapshot["run_at"],
                        "geo": snapshot["geo"]["country_code"],
                        "competitor": competitor["competitor"],
                        **{key: game.get(key) for key in writer.fieldnames if key in game},
                    }
                )


def main():
    parser = argparse.ArgumentParser(description="Geo-aware competitor lobby monitor")
    parser.add_argument("--geo", default="AU", choices=sorted(GEO.keys()))
    parser.add_argument("--out-dir", default="snapshots")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--project", default=DEFAULT_PROJECT)
    args = parser.parse_args()

    geo = {**GEO[args.geo], "code": args.geo}
    proxy = os.environ.get(geo["env_proxy"])
    if not proxy:
        print(f"Missing proxy env var: {geo['env_proxy']}", file=sys.stderr)
        return 2

    opener = build_opener(proxy)
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    proxy_check, proxy_error = safe_request(request_json, opener, "GET", "https://ipinfo.io/json", headers)
    snapshot = {
        "run_at": utc_now(),
        "geo": {
            "country_code": args.geo,
            "label": geo["label"],
            "accept_language": geo["accept_language"],
            "timezone": geo["timezone"],
        },
        "proxy_check": proxy_check["json"] if proxy_check else {"error": proxy_error},
        "competitors": [
            fetch_rocketplay(opener, geo),
            fetch_lucky_dreams(opener, geo),
            fetch_onlywin(opener, geo),
        ],
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = snapshot["run_at"].replace(":", "").replace("+", "Z")
    prefix = f"{args.geo.lower()}-lobby"
    json_path = out_dir / f"{prefix}-{stamp}.json"
    md_path = out_dir / f"{prefix}-{stamp}.md"
    csv_path = out_dir / f"{prefix}-{stamp}.csv"

    json_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(summarize(snapshot), encoding="utf-8")
    write_csv(csv_path, snapshot)
    with connect(args.db) as conn:
        run_id = ingest_snapshot(conn, snapshot, json_path, args.project)

    print(f"JSON: {json_path}")
    print(f"MD:   {md_path}")
    print(f"CSV:  {csv_path}")
    print(f"DB:   {args.db} (run_id={run_id})")
    print()
    print(summarize(snapshot))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
