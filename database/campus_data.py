"""
Campus graph definition  (single source of truth).

Every location is a *node* that sits on one of the map drawings
(`VIEWS`).  Coordinates are in **native pixels of the PNG drawings**
(2480 x 1753), so the route line is drawn exactly where the node is on the
picture.  The numbers were measured from the drawings themselves
(wall lines, door openings, road centre-lines).

Edges are walkable connections.  A *walk* edge stays on one drawing and
may carry `via` way-points so that the route follows corridors / roads
instead of cutting through walls.  A *transition* edge (door, stairs,
lift, exit_door) jumps from one drawing to another -- this is what makes the
map switch from Campus -> 1st Floor -> 2nd Floor and so on.

If you move or rename something, only this file needs to change.
`database/campus_db.py` turns it into the SQLite database on start-up.
"""

from math import hypot

IMAGE_W, IMAGE_H = 2480, 1753

# Campus drawing was traced on a 1308 px wide preview; D() converts to native px.
_S = 2480 / 1308.0


def D(x, y):
    return (round(x * _S, 1), round(y * _S, 1))


FLOOR_NAMES = {1: "1st Floor", 2: "2nd Floor", 3: "3rd Floor"}

# px_per_m: pixels on the drawing that equal one metre (from each drawing's scale / dimension line)
VIEWS = {
    "campus": {
        "title": "Campus Site Plan", "short": "Campus", "building": None,
        "image": "maps/campus.png", "px_per_m": 4.74, "floor": 0,
    },
    "floor_1": {
        "title": "Main Building \u00b7 1st Floor", "short": "1st Floor",
        "building": "Main College Building", "image": "maps/floor_1.png",
        "px_per_m": 14.76, "floor": 1,
    },
    "floor_2": {
        "title": "Main Building \u00b7 2nd Floor", "short": "2nd Floor",
        "building": "Main College Building", "image": "maps/floor_2.png",
        "px_per_m": 14.76, "floor": 2,
    },
    "floor_3": {
        "title": "Main Building \u00b7 3rd Floor", "short": "3rd Floor",
        "building": "Main College Building", "image": "maps/floor_3.png",
        "px_per_m": 14.76, "floor": 3,
    },
    "lab": {
        "title": "Lab Block \u00b7 Ground Floor", "short": "Lab Block",
        "building": "Lab Block", "image": "maps/lab_ground.png",
        "px_per_m": 23.75, "floor": 1,
    },
    "admin": {
        "title": "Admin Block \u00b7 Ground Floor", "short": "Admin Block",
        "building": "Admin Block", "image": "maps/admin_ground.png",
        "px_per_m": 29.7, "floor": 1,
    },
}

# Section drawing (no graph nodes): bands that highlight the floor the user is on.
SECTION = {
    "title": "Main Building \u00b7 Cross Section",
    "short": "Section",
    "image": "maps/02_Main_Building_Elevation_Section.png",
    "bands": {
        1: {"x": 489, "y": 1182, "w": 1005, "h": 122},
        2: {"x": 489, "y": 1040, "w": 1005, "h": 126},
        3: {"x": 489, "y": 898, "w": 1005, "h": 126},
    },
}

# Seconds for each transition (also converted to a path "cost" in metres-equivalent)
WALK_SPEED = 1.25
TRANSITION_COST = {"door": 5 * WALK_SPEED, "exit_door": 5 * WALK_SPEED,
                   "stairs": 20 * WALK_SPEED, "lift": 40 * WALK_SPEED}
TRANSITION_KINDS = ("door", "exit_door", "stairs", "lift")

NODES = []
EDGES = []
_ids = set()


def add_node(nid, name, view, xy, kind="junction", *, search=False, category="",
             group="", aliases=(), label=None, ref=None, attach=None):
    """kind: room | poi | door | junction | corridor | stairs | lift"""
    if nid in _ids:
        raise ValueError(f"duplicate node id {nid}")
    _ids.add(nid)
    NODES.append({
        "id": nid, "name": name or label or nid, "view": view,
        "x": float(xy[0]), "y": float(xy[1]), "kind": kind,
        "search": 1 if search else 0, "category": category, "group": group,
        "aliases": list(aliases), "label": label, "ref": ref, "attach": attach,
    })


def add_edge(a, b, way="", via=(), kind="walk", emergency_only=False):
    EDGES.append({"a": a, "b": b, "way": way, "via": [list(map(float, p)) for p in via],
                  "kind": kind, "emergency_only": 1 if emergency_only else 0})


def _chain(ids, way):
    for a, b in zip(ids, ids[1:]):
        add_edge(a, b, way=way)


# =====================================================================
# CAMPUS (outdoor site plan)
# =====================================================================
def _campus():
    v, G = "campus", "Campus"

    # ---- roads / junctions -------------------------------------------------
    add_node("c_gate", "Main College Gate", v, D(522, 672), "poi", search=True,
             category="entrance", group=G, aliases=["Main Gate", "Gate", "College Gate"])
    add_node("c_j_sec", "Security junction", v, D(522, 630), label="the junction near the Security Gate")
    add_node("c_j_mid", "Cross-path junction", v, D(522, 540), label="the cross-path junction")
    add_node("c_j_main", "Main Road junction", v, D(522, 418), label="the Main Road junction")
    add_node("c_j_student", "Student path junction", v, D(204, 418), label="the Student Facilities path")
    add_node("c_j_admin", "Admin path junction", v, D(249, 418), label="the Admin Block path")
    add_node("c_j_mbw", "West exit path", v, D(407, 418), label="the west exit path")
    add_node("c_j_mbe", "East exit path", v, D(639, 418), label="the east exit path")
    add_node("c_j_lab", "Lab path junction", v, D(809, 418), label="the Lab Block path")

    add_node("c_fire_exit", "Fire Exit", v, D(114, 418), "poi", search=True,
             category="exit", group=G, aliases=["Fire Gate", "Emergency Gate West"])
    add_node("c_emergency_exit", "Emergency Exit", v, D(932, 418), "poi", search=True,
             category="exit", group=G, aliases=["Emergency Gate", "Emergency Gate East"])

    # ---- building doors ----------------------------------------------------
    add_node("c_mb_door", "Main College Building", v, D(522, 338), "door", search=True,
             category="building", group=G, label="the main entrance",
             aliases=["Main Building", "College Building", "Academic Block"])
    add_node("c_admin_door", "Admin Block", v, D(249, 338), "door", search=True,
             category="building", group=G, label="the Admin Block entrance",
             aliases=["Administration", "Administration Block"])
    add_node("c_lab_door", "Lab Block", v, D(809, 340), "door", search=True,
             category="building", group=G, label="the Lab Block entrance",
             aliases=["Laboratories", "Labs"])
    add_node("c_exit_l", "Main Building west exit", v, D(407, 340), label="the building's west exit")
    add_node("c_exit_r", "Main Building east exit", v, D(639, 340), label="the building's east exit")

    # ---- gate area -----------------------------------------------------------
    add_node("c_security_gate", "Security Gate", v, D(562, 630), "poi", search=True,
             category="security", group=G, aliases=["Security"])
    add_node("c_security_office", "Security Office", v, D(588, 630), "poi", search=True,
             category="security", group=G)
    add_node("c_visitor", "Visitor Waiting Area", v, D(415, 630), "poi", search=True,
             category="facility", group=G, aliases=["Visitor Area", "Waiting Area"])
    add_node("c_parking", "Parking Area", v, D(209, 625), "poi", search=True,
             category="parking", group=G, aliases=["Parking", "Car Parking"])
    add_node("c_bicycle", "Bicycle Parking", v, D(682, 630), "poi", search=True,
             category="parking", group=G, aliases=["Cycle Stand", "Cycle Parking"])

    # ---- student facilities / canteen ---------------------------------------
    add_node("c_canteen", "Canteen", v, D(346, 540), "poi", search=True,
             category="food", group=G, aliases=["Cafeteria", "Food Court", "Mess"])
    add_node("c_sf_in", "Student Facilities", v, D(204, 508), label="the Student Facilities building")
    add_node("c_common_room", "Student Common Room", v, D(180, 495), "poi", search=True,
             category="facility", group=G, aliases=["Common Room"])
    add_node("c_medical_room", "Medical Room", v, D(228, 495), "poi", search=True,
             category="medical", group=G, aliases=["Medical", "First Aid", "Clinic", "Health Centre"])
    add_node("c_boys_wash", "Boys Washroom", v, D(172, 523), "poi", search=True,
             category="washroom", group=G, aliases=["Boys Toilet", "Gents Toilet", "Washroom"])
    add_node("c_girls_wash", "Girls Washroom", v, D(204, 523), "poi", search=True,
             category="washroom", group=G, aliases=["Girls Toilet", "Ladies Toilet", "Washroom"])
    add_node("c_water", "Drinking Water", v, D(236, 523), "poi", search=True,
             category="facility", group=G, aliases=["Water", "Water Cooler", "RO Water"])

    # ---- sports ------------------------------------------------------------
    add_node("c_playground", "Playground", v, D(672, 512), "poi", search=True,
             category="sports", group=G, aliases=["Ground", "Sports Ground", "Field"])
    add_node("c_sz_hub", "Sports Zone entrance", v, D(775, 527), label="the Sports Zone entrance")
    add_node("c_basketball", "Basketball Court", v, D(816, 501), "poi", search=True,
             category="sports", group=G, aliases=["Basketball"])
    add_node("c_volleyball", "Volleyball Court", v, D(889, 508), "poi", search=True,
             category="sports", group=G, aliases=["Volleyball"])
    add_node("c_gym", "Gym", v, D(803, 556), "poi", search=True,
             category="sports", group=G, aliases=["Gymnasium", "Sports Complex", "Fitness"])
    add_node("c_sports_office", "Sports Office", v, D(827, 556), "poi", search=True,
             category="office", group=G, aliases=["Sports Department", "PT Office"])

    # ---- walkable network ------------------------------------------------------
    _chain(["c_gate", "c_j_sec", "c_j_mid", "c_j_main"], "Approach Road")
    _chain(["c_fire_exit", "c_j_student", "c_j_admin", "c_j_mbw", "c_j_main",
            "c_j_mbe", "c_j_lab", "c_emergency_exit"], "Main Road")

    add_edge("c_j_main", "c_mb_door", "footpath")
    add_edge("c_j_admin", "c_admin_door", "footpath")
    add_edge("c_j_lab", "c_lab_door", "footpath")
    add_edge("c_j_mbw", "c_exit_l", "footpath")
    add_edge("c_j_mbe", "c_exit_r", "footpath")

    add_edge("c_j_sec", "c_security_gate", "footpath")
    add_edge("c_security_gate", "c_security_office", "footpath")
    add_edge("c_j_sec", "c_visitor", "footpath")
    add_edge("c_parking", "c_j_sec", "footpath", via=[D(209, 664), D(522, 664)])
    add_edge("c_bicycle", "c_j_sec", "footpath", via=[D(682, 664), D(522, 664)])

    add_edge("c_j_mid", "c_canteen", "footpath")
    add_edge("c_canteen", "c_sf_in", "footpath", via=[D(346, 508)])
    add_edge("c_sf_in", "c_j_student", "footpath")
    add_edge("c_sf_in", "c_common_room", "footpath", via=[D(180, 508)])
    add_edge("c_sf_in", "c_medical_room", "footpath", via=[D(228, 508)])
    add_edge("c_sf_in", "c_boys_wash", "footpath", via=[D(172, 508)])
    add_edge("c_sf_in", "c_girls_wash", "footpath", via=[D(204, 508)])
    add_edge("c_sf_in", "c_water", "footpath", via=[D(236, 508)])

    add_edge("c_j_mid", "c_playground", "footpath", via=[D(672, 540)])
    add_edge("c_playground", "c_sz_hub", "footpath", via=[D(672, 527)])
    add_edge("c_sz_hub", "c_basketball", "footpath", via=[D(775, 501)])
    add_edge("c_sz_hub", "c_volleyball", "footpath", via=[D(889, 527)])
    add_edge("c_sz_hub", "c_gym", "footpath", via=[D(803, 527)])
    add_edge("c_gym", "c_sports_office", "footpath")


# =====================================================================
# MAIN BUILDING  (3 floors, one long corridor each, stairs + lift at both ends)
# =====================================================================
CORR_Y, NORTH_Y, SOUTH_Y = 685, 612, 758
X0, X1 = 254, 1730            # inner faces of the two stair towers
HUB_L, HUB_R = 195, 1789      # centre of the left / right tower
STAIRS_Y, LIFT_Y = 572, 780


def _room(n, rid, name, x, y, category, aliases, attach_x=None):
    view, group = f"floor_{n}", f"Main Building \u00b7 {FLOOR_NAMES[n]}"
    add_node(rid, name, view, (x, y), "room", search=True, category=category,
             group=group, aliases=aliases)
    cid = f"{rid}__door"
    numbered = name.startswith("Room ")
    add_node(cid, f"Corridor at {name}", view, (attach_x or x, CORR_Y), "corridor",
             label=f"the door of {name}" if numbered else "the corridor", attach=name)
    add_edge(rid, cid, "room")
    return cid, (attach_x or x)


def _floor(n, north, south):
    view = f"floor_{n}"
    corr = []
    for spec_list, y, side in ((north, NORTH_Y, "N"), (south, SOUTH_Y, "S")):
        w = (X1 - X0) / len(spec_list)
        for i, spec in enumerate(spec_list):
            rid, name, category, aliases = spec
            x = round(X0 + w * (i + 0.5), 1)
            cid, cx = _room(n, rid, name, x, y, category, aliases)
            corr.append((cx, cid))
    corr.sort()
    # towers (left & right): hub -> stairs / lift
    for side, hx, tag in (("l", HUB_L, "left"), ("r", HUB_R, "right")):
        add_node(f"f{n}_hub_{side}", f"{tag.title()} stair & lift lobby", view, (hx, CORR_Y),
                 label=f"the {tag} stair and lift lobby")
        add_node(f"f{n}_stairs_{side}", f"Stairs ({tag.title()})", view, (hx, STAIRS_Y), "stairs",
                 label=f"the {tag} staircase", ref=f"the {tag} staircase")
        add_node(f"f{n}_lift_{side}", f"Lift ({tag.title()})", view, (hx, LIFT_Y), "lift",
                 label=f"the {tag} lift", ref=f"the {tag} lift")
        add_edge(f"f{n}_hub_{side}", f"f{n}_stairs_{side}", "stairwell")
        add_edge(f"f{n}_hub_{side}", f"f{n}_lift_{side}", "stairwell")
    ids = [f"f{n}_hub_l"] + [c for _, c in corr] + [f"f{n}_hub_r"]
    _chain(ids, "corridor")


def _main_building():
    R = lambda num, cat="classroom": (f"r{num}", f"Room {num}", cat, [num])
    # ---------------- 1st floor ----------------
    _floor(1,
           north=[("exit_1_left", "Exit (1st Floor, Left)", "exit", ["Left Exit", "West Exit"]),
                  R("115"), R("113"), R("111"), R("100"),
                  ("main_office", "Main Office", "office", ["Office", "Administration Office"]),
                  R("104"), R("106"),
                  ("auditorium_1", "Auditorium (1st Floor)", "hall", ["Auditorium", "Main Auditorium"]),
                  R("108"),
                  ("nurse", "Nurse Room", "medical", ["Nurse", "Medical", "First Aid", "Sick Room"]),
                  R("110"), R("114"),
                  ("exit_1_right", "Exit (1st Floor, Right)", "exit", ["Right Exit", "East Exit"])],
           south=[R("117"), R("117A"), R("119"), R("121"), R("123"), R("125"),
                  ("front_entrance", "Front Entrance", "facility", ["Entrance", "Main Entrance"]),
                  ("lobby", "Lobby / Reception", "facility", ["Lobby", "Reception"]),
                  R("101"), R("103"), R("105"), R("107"),
                  ("girls_gym", "Girls Gym", "sports", ["Ladies Gym"]),
                  R("116"), R("120")])
    # ---------------- 2nd floor ----------------
    _floor(2,
           north=[R("209"), R("211"), R("213"), R("202"), R("204"), R("206"), R("208"),
                  ("auditorium_2", "Auditorium (2nd Floor)", "hall", ["Auditorium Upper", "Auditorium"]),
                  R("210"), R("212"), R("214")],
           south=[R("215"), R("215A"), R("217"), R("219"), R("221"), R("223"),
                  ("library", "Library / Media Center", "academic", ["Library", "Media Center", "Media Centre"]),
                  R("201"), R("203"), R("205"), R("207"), R("224"), R("222"), R("220"),
                  ("room_tl", "Room TL", "classroom", ["TL"]),
                  ("room_tb", "Room TB", "classroom", ["TB"]),
                  R("216")])
    # ---------------- 3rd floor ----------------
    _floor(3,
           north=[R("303A"), R("305"), R("307"), R("309"), R("311"), R("311A"), R("302"),
                  R("304"), R("306"), R("308"), R("310"), R("312"), R("314A")],
           south=[R("313"), R("315"), R("317"), R("319"), R("321"),
                  ("choir_room", "Choir Room (Room 300)", "academic", ["Room 300", "Choir", "300"]),
                  R("301"), R("303"),
                  ("auditorium_balcony", "Auditorium Balcony (3rd Floor)", "hall",
                   ["Balcony", "Auditorium Balcony"]),
                  R("314"), R("316"), R("318"), R("320")])

    # vertical connections (stairs and lifts, both towers)
    for side in ("l", "r"):
        for n in (1, 2):
            add_edge(f"f{n}_stairs_{side}", f"f{n+1}_stairs_{side}", "stairs", kind="stairs")
            add_edge(f"f{n}_lift_{side}", f"f{n+1}_lift_{side}", "lift", kind="lift")

    # main entrance: campus <-> 1st floor
    add_node("f1_entrance", "Main entrance", "floor_1", (893.6, 915), "door",
             label="the main entrance", group="Main Building \u00b7 1st Floor")
    add_edge("f1_entrance", "front_entrance", "room")
    add_edge("c_mb_door", "f1_entrance", "door", kind="door")
    # emergency-only exit doors (1st floor left / right exit rooms -> campus)
    add_edge("c_exit_l", "exit_1_left", "door", kind="exit_door", emergency_only=True)
    add_edge("c_exit_r", "exit_1_right", "door", kind="exit_door", emergency_only=True)


# =====================================================================
# ADMIN BLOCK (ground floor)
# =====================================================================
def _admin():
    v, G, cy = "admin", "Admin Block", 855
    add_node("ad_entrance", "Admin Block entrance", v, (1050, 1262), "door", label="the Admin Block entrance", group=G)
    # (id, name, centre_x, centre_y, door_x, category, aliases)
    rooms = [
        ("ad_principal", "Principal Office", 578.5, 635, 528, "office", ["Principal", "Principal's Office"]),
        ("ad_vp", "Vice Principal Office", 903.5, 635, 903, "office", ["Vice Principal", "VP Office"]),
        ("ad_conference", "Conference Room", 1316.5, 635, 1375, "hall", ["Meeting Room", "Conference"]),
        ("ad_helpdesk", "Student Help Desk", 534, 1075, 528, "office", ["Help Desk", "Student Desk"]),
        ("ad_admission", "Admission Office", 800, 1075, 794, "office", ["Admission", "Admissions"]),
        ("ad_lobby", "Admin Entrance Lobby", 1051, 1075, 1050, "facility", ["Admin Lobby"]),
        ("ad_accounts", "Accounts Office", 1272.5, 1075, 1272, "office", ["Accounts", "Fee Office", "Fees"]),
        ("ad_exam", "Examination Cell", 1479, 1075, 1472, "office", ["Exam Cell", "Examination", "Exam Section"]),
    ]
    corr = []
    for rid, name, x, y, dx, cat, al in rooms:
        add_node(rid, name, v, (x, y), "room", search=True, category=cat, group=G, aliases=al)
        cid = f"{rid}__door"
        add_node(cid, f"Corridor at {name}", v, (dx, cy), "corridor", label=f"the door of the {name}", attach=name)
        via = [(dx, y)] if abs(dx - x) > 1 else []
        add_edge(rid, cid, "room", via=via)
        corr.append((dx, cid))
    corr.sort()
    _chain([c for _, c in corr], "corridor")
    add_edge("ad_entrance", "ad_lobby", "room")
    add_edge("c_admin_door", "ad_entrance", "door", kind="door")


# =====================================================================
# LAB BLOCK (ground floor)
# =====================================================================
def _lab():
    v, G, cy = "lab", "Lab Block", 837
    add_node("lab_entrance", "Lab Block entrance", v, (449, 1215), "door", label="the Lab Block entrance", group=G)
    add_node("lab_foyer", "Entrance Foyer", v, (448.5, 1030), label="the entrance foyer")
    rooms = [
        ("lab_computer", "Computer Lab", 495.5, 640, 496, ["Computer", "CS Lab", "IT Lab"]),
        ("lab_science", "Science Lab", 785, 640, 784, ["Science"]),
        ("lab_physics", "Physics Lab", 1033, 640, 1033, ["Physics"]),
        ("lab_chemistry", "Chemistry Lab", 1281.5, 640, 1280, ["Chemistry"]),
        ("lab_biology", "Biology Lab", 1529.5, 640, 1529, ["Biology", "Bio Lab"]),
        ("lab_seminar", "Seminar Hall", 897.5, 1030, 869, ["Seminar", "Seminar Room"]),
    ]
    corr = []
    for rid, name, x, y, dx, al in rooms:
        add_node(rid, name, v, (x, y), "room", search=True,
                 category="lab" if "Lab" in name else "hall", group=G, aliases=al)
        cid = f"{rid}__door"
        add_node(cid, f"Corridor at {name}", v, (dx, cy), "corridor", label=f"the door of the {name}", attach=name)
        add_edge(rid, cid, "room", via=[(dx, y)] if abs(dx - x) > 1 else [])
        corr.append((dx, cid))
    # foyer door
    add_node("lab_foyer__door", "Corridor at Entrance Foyer", v, (415, cy), "corridor",
             label="the corridor", attach="Entrance Foyer")
    corr.append((415, "lab_foyer__door"))
    corr.sort()
    _chain([c for _, c in corr], "corridor")
    add_edge("lab_foyer", "lab_foyer__door", "room", via=[(415, 1030)])
    add_edge("lab_entrance", "lab_foyer", "room")
    add_edge("c_lab_door", "lab_entrance", "door", kind="door")


def build():
    """Return (nodes, edges) with edge lengths / costs filled in."""
    by_id = {n["id"]: n for n in NODES}
    out = []
    for e in EDGES:
        a, b = by_id[e["a"]], by_id[e["b"]]
        item = dict(e)
        if e["kind"] in TRANSITION_KINDS:
            item["length_m"] = 0.0
            item["cost"] = TRANSITION_COST[e["kind"]]
        else:
            if a["view"] != b["view"]:
                raise ValueError(f"walk edge {a['id']}->{b['id']} crosses drawings")
            pts = [(a["x"], a["y"])] + [tuple(p) for p in e["via"]] + [(b["x"], b["y"])]
            px = sum(hypot(p[0] - q[0], p[1] - q[1]) for p, q in zip(pts, pts[1:]))
            item["length_m"] = round(px / VIEWS[a["view"]]["px_per_m"], 2)
            item["cost"] = item["length_m"]
        out.append(item)
    return NODES, out


_campus()
_main_building()
_admin()
_lab()
