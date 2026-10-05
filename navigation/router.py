"""Turns a Dijkstra path into everything the front-end needs:

* **legs**   - the part of the route that lies on one drawing (Campus, 1st Floor,
               2nd Floor, Lab Block ...). Each leg has the exact polyline in drawing pixels.
* **steps**  - human instructions. Every step points at a leg and a vertex range,
               so pressing *Next* can switch the map and move the route forward.
* **summary**- distance, time, floors, buildings.
"""

import math

from config.config import WALKING_SPEED_MPS, TRANSITION_SECONDS
from database.campus_data import TRANSITION_KINDS

CARDINALS = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"]

WAY_TEXT = {
    "corridor": "the corridor",
    "Main Road": "the Main Road",
    "Approach Road": "the Approach Road",
    "footpath": "the footpath",
}

EMERGENCY_EXIT_TARGETS = ["c_fire_exit", "c_emergency_exit", "c_gate"]
EMERGENCY_MEDICAL_TARGETS = ["nurse", "c_medical_room"]


class RouteError(Exception):
    def __init__(self, message, code="route_error"):
        super().__init__(message)
        self.message = message
        self.code = code


# ----------------------------------------------------------------------
# geometry helpers
# ----------------------------------------------------------------------
def _heading(p, q):
    """Compass bearing of p->q on a north-up drawing (0 = north, 90 = east)."""
    return (math.degrees(math.atan2(q[0] - p[0], -(q[1] - p[1]))) + 360) % 360


def _turn(h_from, h_to):
    """Signed turn in degrees: positive = right, negative = left."""
    return (h_to - h_from + 540) % 360 - 180


def _cardinal(h):
    return CARDINALS[int((h + 22.5) // 45) % 8]


def _seg_len(p, q):
    return math.hypot(q[0] - p[0], q[1] - p[1])


def _join(names):
    names = list(names)
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


# ----------------------------------------------------------------------
# blocking rules
# ----------------------------------------------------------------------
def blocked_rule(accessible=False, emergency=False):
    def blocked(edge):
        if edge["emergency_only"] and not emergency:
            return True                      # exit doors are not shortcuts
        if accessible and edge["kind"] == "stairs":
            return True                      # step-free route: lifts only
        if emergency and edge["kind"] == "lift":
            return True                      # never use lifts in an emergency
        return False
    return blocked


# ----------------------------------------------------------------------
# building legs
# ----------------------------------------------------------------------
def _new_leg(index, node, views):
    return {
        "index": index, "view": node["view"], "points": [[node["x"], node["y"]]],
        "marks": {0: node["id"]}, "seg_way": [], "px_per_m": views[node["view"]]["px_per_m"],
    }


def _append_edge(leg, edge, from_node, to_node):
    via = edge["via"] if edge["a"] == from_node["id"] else list(reversed(edge["via"]))
    way = edge["way"]
    verts = [list(p) for p in via] + [[to_node["x"], to_node["y"]]]
    for i, v in enumerate(verts):
        last = leg["points"][-1]
        if abs(last[0] - v[0]) < 0.01 and abs(last[1] - v[1]) < 0.01:
            if i == len(verts) - 1:
                leg["marks"][len(leg["points"]) - 1] = to_node["id"]
            continue
        leg["points"].append(v)
        leg["seg_way"].append(way)
        if i == len(verts) - 1:
            leg["marks"][len(leg["points"]) - 1] = to_node["id"]


def _build_legs(node_ids, edges, nodes, views):
    legs, transitions = [], []
    cur = _new_leg(0, nodes[node_ids[0]], views)
    pending = None
    for i, edge in enumerate(edges):
        a, b = nodes[node_ids[i]], nodes[node_ids[i + 1]]
        if edge["kind"] in TRANSITION_KINDS:
            if cur is None and pending and pending["kind"] == edge["kind"]:
                pending["to"], pending["floors"] = b["id"], pending["floors"] + 1   # stairs 1->3 = one step
            else:
                if cur is None:                                        # two different transitions in a row
                    transitions.append(pending)
                    cur = _new_leg(len(legs), a, views)
                legs.append(cur)
                pending = {"kind": edge["kind"], "from": a["id"], "to": b["id"], "floors": 1}
                cur = None
        else:
            if cur is None:
                transitions.append(pending)
                pending = None
                cur = _new_leg(len(legs), a, views)
            _append_edge(cur, edge, a, b)
    if cur is None:
        transitions.append(pending)
        cur = _new_leg(len(legs), nodes[node_ids[-1]], views)
    legs.append(cur)
    for leg in legs:
        cum, total = [0.0], 0.0
        for p, q in zip(leg["points"], leg["points"][1:]):
            total += _seg_len(p, q)
            cum.append(total)
        leg["cum"] = cum
    return legs, transitions


# ----------------------------------------------------------------------
# wording
# ----------------------------------------------------------------------
def _ref(node):
    if node.get("ref"):
        return node["ref"]
    if node["kind"] in ("junction", "corridor", "door") and node.get("label"):
        return node["label"]
    name = node["name"]
    return name if name.startswith("Room ") else "the " + name


def _floor_phrase(views, view):
    v = views[view]
    if view == "campus":
        return "outdoors on the campus"
    if view.startswith("floor_"):
        return f"on the {v['short'].lower()}"
    return "on the ground floor"


def _dominant_way(leg, a, b):
    acc = {}
    for i in range(a, b):
        w = leg["seg_way"][i]
        acc[w] = acc.get(w, 0) + _seg_len(leg["points"][i], leg["points"][i + 1])
    return max(acc, key=acc.get) if acc else ""


def _runs(leg):
    """Split a leg's polyline into straight runs (a new run starts at every real turn).
    Tiny jogs (< 3 m) are folded into the next run so instructions stay readable."""
    pts = leg["points"]
    n = len(pts)
    if n < 2:
        return []
    hs = [_heading(pts[i], pts[i + 1]) for i in range(n - 1)]
    cuts = [0]
    for i in range(1, n - 1):
        if abs(_turn(hs[i - 1], hs[i])) > 30:
            cuts.append(i)
    cuts.append(n - 1)
    min_px = 3 * leg["px_per_m"]
    changed = True
    while changed and len(cuts) > 2:
        changed = False
        for k in range(len(cuts) - 1):
            seg = leg["cum"][cuts[k + 1]] - leg["cum"][cuts[k]]
            if seg < min_px:
                if k + 1 < len(cuts) - 1:
                    del cuts[k + 1]          # merge with next run
                elif k > 0:
                    del cuts[k]              # last run is tiny: merge with previous
                else:
                    continue
                changed = True
                break
    return list(zip(cuts, cuts[1:]))


def _passing(leg, a, b, nodes, exclude):
    names = []
    for idx in range(a + 1, b):
        nid = leg["marks"].get(idx)
        if not nid:
            continue
        node = nodes[nid]
        name = node["attach"] if node["kind"] == "corridor" else (node["name"] if node["kind"] in ("room", "poi") else None)
        if name and name not in exclude and name not in names:
            names.append(name)
    return names


def _leg_steps(leg, nodes, views, first_leg, steps_out):
    prev_heading = None
    runs = _runs(leg)
    for ri, (a, b) in enumerate(runs):
        pts = leg["points"]
        longest = max(range(a, b), key=lambda i: _seg_len(pts[i], pts[i + 1]))
        h = _heading(pts[longest], pts[longest + 1])
        dist_px = leg["cum"][b] - leg["cum"][a]
        dist_m = max(1, round(dist_px / leg["px_per_m"]))
        way = _dominant_way(leg, a, b)
        start_node = nodes[leg["marks"][a]] if a in leg["marks"] else None
        end_node = nodes[leg["marks"][b]] if b in leg["marks"] else None
        card = _cardinal(h)
        way_txt = WAY_TEXT.get(way, "")

        if prev_heading is None:
            kind, title = "head", f"Head {card}"
            if way == "room" and start_node and end_node and end_node["kind"] == "corridor":
                text = (f"Leave {start_node['name']} and step out into the corridor"
                        if start_node["kind"] == "room" else f"Walk in from {_ref(start_node)} to the corridor")
            else:
                verb = "Head" if first_leg else "Walk"
                text = f"{verb} {card}" + (f" along {way_txt}" if way_txt else "") + f" for {dist_m} m"
        else:
            delta = _turn(prev_heading, h)
            if abs(delta) <= 30:
                kind, title = "straight", "Continue straight"
            elif abs(delta) >= 150:
                kind, title = "around", "Turn around"
            elif delta > 0:
                kind, title = "turn_right", "Turn right"
            else:
                kind, title = "turn_left", "Turn left"
            onto = ""
            if way == "corridor":
                onto = " into the corridor"
            elif way_txt:
                onto = f" onto {way_txt}"
            text = f"{title}{onto} and walk {dist_m} m"

        exclude = {n["name"] for n in (start_node, end_node) if n}
        exclude |= {n["attach"] for n in (start_node, end_node) if n and n.get("attach")}
        passing = _passing(leg, a, b, nodes, exclude)
        if passing:
            shown = passing[:2]
            extra = len(passing) - len(shown)
            text += ", passing " + _join(shown + ([f"{extra} more"] if extra else []))
        if end_node and not (way == "room" and end_node["kind"] == "corridor" and prev_heading is None):
            if end_node["kind"] == "room" and end_node["category"] != "exit":
                text += f" into {_ref(end_node)}"
            else:
                text += f" to {_ref(end_node)}"
        text += "."

        steps_out.append({
            "kind": kind, "title": title, "text": text, "distance_m": dist_m,
            "leg": leg["index"], "from_idx": a, "to_idx": b,
        })
        prev_heading = h


def _transition_step(tr, leg_index, nodes, views):
    a, b = nodes[tr["from"]], nodes[tr["to"]]
    va, vb = views[a["view"]], views[b["view"]]
    base = {"leg": leg_index, "from_idx": 0, "to_idx": 0, "distance_m": 0}
    if tr["kind"] in ("stairs", "lift"):
        up = vb["floor"] > va["floor"]
        k = tr["floors"]
        what = "stairs" if tr["kind"] == "stairs" else "lift"
        floors_txt = "" if k == 1 else f" {k} floors"
        title = f"Take the {what} {'up' if up else 'down'}{floors_txt} to the {vb['short']}"
        text = (f"Use {_ref(a)} and go {'up' if up else 'down'} {k} floor{'s' if k > 1 else ''}. "
                f"You will arrive {_floor_phrase(views, b['view'])} at {_ref(b)}.")
        base.update(kind=f"{what}_{'up' if up else 'down'}", title=title, text=text,
                    badge={"from": va["short"], "to": vb["short"], "dir": "up" if up else "down", "mode": what})
    elif tr["kind"] == "door":
        if a["view"] == "campus":
            bld = vb["building"]
            base.update(kind="door_in", title=f"Enter the {bld}",
                        text=f"Go in through {_ref(a)}. You are now {_floor_phrase(views, b['view'])}.",
                        badge={"from": "Campus", "to": vb["short"], "dir": "in", "mode": "door"})
        else:
            bld = va["building"]
            base.update(kind="door_out", title=f"Exit the {bld}",
                        text=f"Walk out through {_ref(b) if b['kind'] == 'door' else 'the door'} and back onto the campus.",
                        badge={"from": va["short"], "to": "Campus", "dir": "out", "mode": "door"})
    else:  # exit_door (emergency)
        base.update(kind="door_out", title="Leave the building through the exit",
                    text="Go through the exit door and out onto the campus.",
                    badge={"from": va["short"], "to": "Campus", "dir": "out", "mode": "door"})
    return base


# ----------------------------------------------------------------------
# main entry points
# ----------------------------------------------------------------------
def _assemble(locs, node_ids, edges, accessible, emergency):
    nodes, views = locs.nodes, locs.views
    start, end = nodes[node_ids[0]], nodes[node_ids[-1]]
    legs, transitions = _build_legs(node_ids, edges, nodes, views)

    steps = [{
        "kind": "start", "title": "Start",
        "text": f"You are at {start['name']} ({views[start['view']]['title']}).",
        "distance_m": 0, "leg": 0, "from_idx": 0, "to_idx": 0,
    }]
    for leg in legs:
        if leg["index"] > 0:
            steps.append(_transition_step(transitions[leg["index"] - 1], leg["index"], nodes, views))
        _leg_steps(leg, nodes, views, leg["index"] == 0, steps)
    last_leg = legs[-1]
    steps.append({
        "kind": "arrive", "title": "You have arrived",
        "text": f"{end['name']} is here ({views[end['view']]['title']}).",
        "distance_m": 0, "leg": last_leg["index"],
        "from_idx": len(last_leg["points"]) - 1, "to_idx": len(last_leg["points"]) - 1,
    })

    # enrich steps with display info
    for i, s in enumerate(steps):
        view = legs[s["leg"]]["view"]
        s["index"], s["view"] = i, view
        s["floor"] = views[view]["short"]
        s["building"] = views[view]["building"] or "Campus"
        s["distance_m"] = int(s["distance_m"])

    walk_m = sum(e["length_m"] for e in edges)
    seconds = walk_m / WALKING_SPEED_MPS + sum(TRANSITION_SECONDS.get(e["kind"], 0) for e in edges)
    buildings = []
    for leg in legs:
        b = views[leg["view"]]["building"]
        if b and b not in buildings:
            buildings.append(b)
    floor_moves = sum(1 for e in edges if e["kind"] in ("stairs", "lift"))
    modes = {e["kind"] for e in edges if e["kind"] in ("stairs", "lift")}
    summary = {
        "distance_m": int(round(walk_m)),
        "time_s": int(round(seconds)),
        "time_min": max(1, int(math.ceil(seconds / 60))),
        "floors_changed": floor_moves,
        "buildings": buildings,
        "vertical": "lift" if "lift" in modes else ("stairs" if "stairs" in modes else None),
        "steps": len(steps) - 2,
        "accessible": bool(accessible),
        "emergency": bool(emergency),
    }
    out_legs = [{
        "index": l["index"], "view": l["view"],
        "points": [[round(p[0], 1), round(p[1], 1)] for p in l["points"]],
    } for l in legs]
    out_transitions = []
    for i, t in enumerate(transitions):
        a, b = nodes[t["from"]], nodes[t["to"]]
        out_transitions.append({
            "kind": t["kind"], "floors": t["floors"], "after_leg": i,
            "from": {"view": a["view"], "x": a["x"], "y": a["y"]},
            "to": {"view": b["view"], "x": b["x"], "y": b["y"]},
            "badge": None,
        })
    # attach the badge of the matching transition step (step.leg == leg that follows the transition)
    for s in steps:
        if s.get("badge"):
            out_transitions[s["leg"] - 1]["badge"] = s["badge"]
    return {
        "ok": True,
        "from": locs.public(start) if start["search"] else _pub(start, views),
        "to": locs.public(end) if end["search"] else _pub(end, views),
        "summary": summary, "legs": out_legs, "transitions": out_transitions, "steps": steps,
    }


def _pub(node, views):
    return {"id": node["id"], "name": node["name"], "view": node["view"], "x": node["x"], "y": node["y"],
            "group": node["group"], "category": node["category"], "floor": views[node["view"]]["short"]}


def compute_route(graph, locs, start_id, end_id, accessible=False, emergency=False):
    if start_id not in graph or end_id not in graph:
        raise RouteError("That location is not on the map.", "unknown_location")
    if start_id == end_id:
        raise RouteError("You are already there - choose a different destination.", "same_location")
    node_ids, edges, _cost = graph.shortest_path(start_id, end_id, blocked_rule(accessible, emergency))
    if not node_ids:
        raise RouteError("No walkable route was found between these two places.", "no_route")
    return _assemble(locs, node_ids, edges, accessible, emergency)


def compute_emergency(graph, locs, start_id, kind="exit"):
    if start_id not in graph:
        raise RouteError("Your current location is not on the map.", "unknown_location")
    targets = EMERGENCY_MEDICAL_TARGETS if kind == "medical" else EMERGENCY_EXIT_TARGETS
    if start_id in targets:
        raise RouteError("You are already at " + locs.name(start_id) + ".", "already_there")
    target, node_ids, edges, _cost = graph.nearest(start_id, targets, blocked_rule(False, True))
    if not target:
        raise RouteError("No emergency route is available from here.", "no_route")
    result = _assemble(locs, node_ids, edges, False, True)
    result["summary"]["emergency_kind"] = kind
    return result
