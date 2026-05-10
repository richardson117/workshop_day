from lobby_db import DEFAULT_DB_PATH, connect, init_db


with connect(DEFAULT_DB_PATH) as conn:
    init_db(conn)
    runs = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    games = conn.execute("SELECT COUNT(*) FROM games").fetchone()[0]
    brands = conn.execute("SELECT COUNT(*) FROM brands").fetchone()[0]

print(f"ok: {runs} runs, {brands} brands, {games} game placements")
