"""Location lookup: exact ids, names, aliases and forgiving fuzzy search."""

import difflib
import re


def normalize(value):
    if value is None:
        return ""
    value = str(value).strip().lower()
    value = value.replace("_", " ").replace("-", " ").replace("/", " ").replace("(", " ").replace(")", " ")
    value = re.sub(r"[^\w\s]", "", value)
    return re.sub(r"\s+", " ", value).strip()


class LocationService:
    def __init__(self, nodes, views):
        self.nodes = {n["id"]: n for n in nodes}
        self.views = views
        self.locations = [n for n in nodes if n["search"]]
        self._keys = {}                       # normalised text -> node id
        for n in self.locations:
            for text in [n["id"], n["name"], *n["aliases"]]:
                self._keys.setdefault(normalize(text), n["id"])
        # a bare room number such as "213" or "117a" finds "Room 213"
        for n in self.locations:
            if n["name"].startswith("Room "):
                self._keys.setdefault(normalize(n["name"][5:]), n["id"])

    # ------------------------------------------------------------------
    def get(self, node_id):
        return self.nodes.get(node_id)

    def name(self, node_id):
        n = self.nodes.get(node_id)
        return n["name"] if n else str(node_id or "")

    def view_of(self, node_id):
        return self.nodes[node_id]["view"]

    # ------------------------------------------------------------------
    def public(self, node):
        """JSON-friendly description of a searchable location."""
        v = self.views[node["view"]]
        return {
            "id": node["id"], "name": node["name"], "group": node["group"],
            "category": node["category"], "view": node["view"],
            "floor": v["short"] if v["building"] else "Outdoors",
            "aliases": node["aliases"], "x": node["x"], "y": node["y"],
        }

    def all_public(self):
        order = {"campus": 0, "floor_1": 1, "floor_2": 2, "floor_3": 3, "admin": 4, "lab": 5}
        items = sorted(self.locations, key=lambda n: (order.get(n["view"], 9), n["name"].lower()))
        return [self.public(n) for n in items]

    # ------------------------------------------------------------------
    def score(self, node, q):
        """Higher is better; 0 means no match."""
        texts = [node["name"], *node["aliases"], node["id"]]
        best = 0
        for t in texts:
            nt = normalize(t)
            if not nt:
                continue
            if nt == q:
                best = max(best, 100)
            elif nt.startswith(q):
                best = max(best, 80)
            elif any(w.startswith(q) for w in nt.split()):
                best = max(best, 65)
            elif q in nt:
                best = max(best, 50)
            else:
                words = q.split()
                if len(words) > 1 and all(w in nt for w in words):
                    best = max(best, 45)
        return best

    def search(self, query, limit=12):
        q = normalize(query)
        if not q:
            return []
        scored = []
        for n in self.locations:
            s = self.score(n, q)
            if s:
                scored.append((-s, len(n["name"]), n["name"], n))
        scored.sort(key=lambda t: t[:3])
        return [self.public(t[3]) for t in scored[:limit]]

    def resolve(self, value):
        """Turn user input (id, name, alias, or a rough guess) into a node id."""
        if not value:
            return None
        raw = str(value).strip()
        if raw in self.nodes and self.nodes[raw]["search"]:
            return raw
        q = normalize(raw)
        if not q:
            return None
        if q in self._keys:
            return self._keys[q]
        hits = self.search(raw, limit=1)
        if hits:
            return hits[0]["id"]
        close = difflib.get_close_matches(q, list(self._keys), n=1, cutoff=0.78)
        return self._keys[close[0]] if close else None
