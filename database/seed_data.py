"""Rebuild the SQLite database from scratch:   python -m database.seed_data"""

from database.campus_db import initialize_database, load_graph_data

if __name__ == "__main__":
    initialize_database(force=True)
    nodes, edges = load_graph_data()
    print(f"Database rebuilt: {len(nodes)} nodes, {len(edges)} edges")
