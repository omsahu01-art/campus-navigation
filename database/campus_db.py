"""SQLite storage for the campus graph.

The database is (re)built automatically from `campus_data.py` whenever the
schema version stored inside it differs from SCHEMA_VERSION, so an old or
half-broken `campus.db` can never make the app fail.
"""

import json
import sqlite3

from config.config import DATABASE_PATH
from database import campus_data

SCHEMA_VERSION = "2.1"


def _connect():
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _current_version(conn):
    try:
        row = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
        return row["value"] if row else None
    except sqlite3.DatabaseError:
        return None


def rebuild_database():
    """Drop everything and re-create the tables from campus_data.py."""
    nodes, edges = campus_data.build()
    conn = _connect()
    cur = conn.cursor()
    for table in ("nodes", "edges", "meta"):
        cur.execute(f"DROP TABLE IF EXISTS {table}")
    cur.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
    cur.execute("""
        CREATE TABLE nodes (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, view TEXT NOT NULL,
            x REAL NOT NULL, y REAL NOT NULL, kind TEXT NOT NULL,
            searchable INTEGER NOT NULL DEFAULT 0, category TEXT, group_name TEXT,
            aliases TEXT, label TEXT, ref TEXT, attach TEXT
        )""")
    cur.execute("""
        CREATE TABLE edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            a TEXT NOT NULL REFERENCES nodes(id), b TEXT NOT NULL REFERENCES nodes(id),
            kind TEXT NOT NULL, way TEXT, length_m REAL NOT NULL, cost REAL NOT NULL,
            via TEXT, emergency_only INTEGER NOT NULL DEFAULT 0
        )""")
    cur.executemany(
        "INSERT INTO nodes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [(n["id"], n["name"], n["view"], n["x"], n["y"], n["kind"], n["search"],
          n["category"], n["group"], json.dumps(n["aliases"]), n["label"], n["ref"],
          n["attach"]) for n in nodes])
    cur.executemany(
        "INSERT INTO edges (a,b,kind,way,length_m,cost,via,emergency_only) VALUES (?,?,?,?,?,?,?,?)",
        [(e["a"], e["b"], e["kind"], e["way"], e["length_m"], e["cost"],
          json.dumps(e["via"]), e["emergency_only"]) for e in edges])
    cur.execute("INSERT INTO meta VALUES ('schema_version', ?)", (SCHEMA_VERSION,))
    conn.commit()
    conn.close()


def initialize_database(force=False):
    """Make sure a valid database exists. Returns True if it was (re)built."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = _connect()
    version = _current_version(conn)
    conn.close()
    if force or version != SCHEMA_VERSION:
        rebuild_database()
        return True
    return False


def load_graph_data():
    """Return (nodes, edges) as plain dicts."""
    conn = _connect()
    nodes = []
    for r in conn.execute("SELECT * FROM nodes"):
        nodes.append({
            "id": r["id"], "name": r["name"], "view": r["view"], "x": r["x"], "y": r["y"],
            "kind": r["kind"], "search": bool(r["searchable"]), "category": r["category"] or "",
            "group": r["group_name"] or "", "aliases": json.loads(r["aliases"] or "[]"),
            "label": r["label"], "ref": r["ref"], "attach": r["attach"],
        })
    edges = []
    for r in conn.execute("SELECT * FROM edges ORDER BY id"):
        edges.append({
            "id": r["id"], "a": r["a"], "b": r["b"], "kind": r["kind"], "way": r["way"] or "",
            "length_m": r["length_m"], "cost": r["cost"], "via": json.loads(r["via"] or "[]"),
            "emergency_only": bool(r["emergency_only"]),
        })
    conn.close()
    return nodes, edges


if __name__ == "__main__":
    initialize_database(force=True)
    n, e = load_graph_data()
    print(f"Database ready: {len(n)} nodes, {len(e)} edges, "
          f"{sum(1 for x in n if x['search'])} searchable locations")
