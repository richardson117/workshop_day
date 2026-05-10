import argparse

from lobby_db import DEFAULT_DB_PATH, DEFAULT_PROJECT, ingest_snapshot_folder


def main():
    parser = argparse.ArgumentParser(description="Import JSON lobby snapshots into SQLite")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--folder", default="snapshots")
    parser.add_argument("--project", default=DEFAULT_PROJECT)
    args = parser.parse_args()

    imported = ingest_snapshot_folder(args.db, args.folder, args.project)
    print(f"Imported {len(imported)} snapshot run(s) into {args.db}")


if __name__ == "__main__":
    main()

