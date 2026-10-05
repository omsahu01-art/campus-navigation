"""Campus graph + Dijkstra's shortest-path algorithm."""

import heapq


class CampusGraph:
    """Undirected weighted graph.  Every edge remembers its database record so
    the router can later draw the exact polyline (corridors, roads, stairs)."""

    def __init__(self):
        self.adj = {}          # node_id -> list of (neighbour_id, cost, edge)

    # ------------------------------------------------------------------
    def add_node(self, node_id):
        self.adj.setdefault(node_id, [])

    def add_edge(self, a, b, cost, edge):
        self.add_node(a)
        self.add_node(b)
        self.adj[a].append((b, cost, edge))
        self.adj[b].append((a, cost, edge))

    def __contains__(self, node_id):
        return node_id in self.adj

    # ------------------------------------------------------------------
    def dijkstra(self, start, blocked=None, target=None):
        """Classic Dijkstra with a binary heap.

        blocked : optional function(edge) -> True if the edge must not be used
        target  : optional node; stop early when it is settled
        Returns (dist, previous) dictionaries.
        """
        dist = {start: 0.0}
        previous = {}
        done = set()
        heap = [(0.0, start)]
        while heap:
            d, u = heapq.heappop(heap)
            if u in done:
                continue
            done.add(u)
            if u == target:
                break
            for v, cost, edge in self.adj[u]:
                if v in done or (blocked and blocked(edge)):
                    continue
                nd = d + cost
                if nd < dist.get(v, float("inf")):
                    dist[v] = nd
                    previous[v] = (u, edge)
                    heapq.heappush(heap, (nd, v))
        return dist, previous

    @staticmethod
    def rebuild_path(previous, start, end):
        """Walk the `previous` map backwards. Returns (nodes, edges) or (None, None)."""
        if end != start and end not in previous:
            return None, None
        nodes, edges = [end], []
        cur = end
        while cur != start:
            cur, edge = previous[cur][0], previous[cur][1]
            nodes.append(cur)
            edges.append(edge)
        nodes.reverse()
        edges.reverse()
        return nodes, edges

    def shortest_path(self, start, end, blocked=None):
        """Return (node_ids, edges, total_cost) or (None, None, inf)."""
        if start not in self.adj or end not in self.adj:
            return None, None, float("inf")
        dist, previous = self.dijkstra(start, blocked, target=end)
        nodes, edges = self.rebuild_path(previous, start, end)
        if nodes is None:
            return None, None, float("inf")
        return nodes, edges, dist[end]

    def nearest(self, start, targets, blocked=None):
        """Closest node from `targets`. Returns (target, nodes, edges, cost) or Nones."""
        if start not in self.adj:
            return None, None, None, float("inf")
        dist, previous = self.dijkstra(start, blocked)
        best, best_cost = None, float("inf")
        for t in targets:
            if t in dist and dist[t] < best_cost:
                best, best_cost = t, dist[t]
        if best is None:
            return None, None, None, float("inf")
        nodes, edges = self.rebuild_path(previous, start, best)
        return best, nodes, edges, best_cost


def build_graph(nodes, edges):
    graph = CampusGraph()
    for n in nodes:
        graph.add_node(n["id"])
    for e in edges:
        graph.add_edge(e["a"], e["b"], e["cost"], e)
    return graph
