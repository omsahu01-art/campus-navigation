"""Run with:  python -m unittest discover -s tests -v"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import app  # noqa: E402
from navigation.router import RouteError, compute_emergency, compute_route  # noqa: E402

LOCS = app.config["LOCATION_SERVICE"]
GRAPH = app.config["CAMPUS_GRAPH"]


class RoutingTests(unittest.TestCase):
    def test_floor_change_creates_new_leg(self):
        r = compute_route(GRAPH, LOCS, "c_gate", "r213")
        self.assertEqual([l["view"] for l in r["legs"]], ["campus", "floor_1", "floor_2"])
        kinds = [s["kind"] for s in r["steps"]]
        self.assertIn("door_in", kinds)
        self.assertIn("stairs_up", kinds)
        self.assertEqual(r["steps"][-1]["kind"], "arrive")

    def test_building_to_building(self):
        r = compute_route(GRAPH, LOCS, "r316", "lab_physics")
        views = [l["view"] for l in r["legs"]]
        self.assertEqual(views, ["floor_3", "floor_1", "campus", "lab"])
        self.assertIn("door_out", [s["kind"] for s in r["steps"]])

    def test_accessible_uses_lift_only(self):
        r = compute_route(GRAPH, LOCS, "r125", "r301", accessible=True)
        self.assertEqual(r["summary"]["vertical"], "lift")
        self.assertNotIn("stairs_up", [s["kind"] for s in r["steps"]])

    def test_steps_point_at_valid_vertices(self):
        r = compute_route(GRAPH, LOCS, "r125", "ad_principal")
        for s in r["steps"]:
            leg = r["legs"][s["leg"]]
            self.assertLessEqual(s["to_idx"], len(leg["points"]) - 1)
            self.assertLessEqual(s["from_idx"], s["to_idx"])

    def test_same_location_rejected(self):
        with self.assertRaises(RouteError):
            compute_route(GRAPH, LOCS, "r125", "r125")

    def test_emergency_never_uses_lifts(self):
        r = compute_emergency(GRAPH, LOCS, "r316", "exit")
        self.assertNotIn("lift_down", [s["kind"] for s in r["steps"]])
        self.assertTrue(r["summary"]["emergency"])

    def test_emergency_doors_not_used_in_normal_routes(self):
        r = compute_route(GRAPH, LOCS, "exit_1_left", "c_gate")
        self.assertNotIn("exit_door", [t["kind"] for t in r["transitions"]])

    def test_every_location_reachable(self):
        ids = [l["id"] for l in LOCS.locations]
        for dst in ids:
            if dst != "c_gate":
                self.assertIsNotNone(GRAPH.shortest_path("c_gate", dst)[0], dst)


class SearchTests(unittest.TestCase):
    def test_alias_and_number(self):
        self.assertEqual(LOCS.resolve("library"), "library")
        self.assertEqual(LOCS.resolve("213"), "r213")
        self.assertEqual(LOCS.resolve("main gate"), "c_gate")
        self.assertEqual(LOCS.resolve("physics"), "lab_physics")

    def test_unknown(self):
        self.assertIsNone(LOCS.resolve("zzzzqqq"))


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.c = app.test_client()

    def test_home_page(self):
        r = self.c.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"CampusNav", r.data)

    def test_api(self):
        self.assertEqual(self.c.get("/api/health").get_json()["ok"], True)
        r = self.c.get("/api/route?from=c_gate&to=r213").get_json()
        self.assertTrue(r["ok"])
        self.assertEqual(self.c.get("/api/route?from=nope&to=r213").status_code, 404)
        self.assertEqual(self.c.get("/api/route?from=r213").status_code, 400)
        self.assertTrue(self.c.get("/api/emergency?from=r213").get_json()["ok"])

    def test_static_images(self):
        for v in app.config["CAMPUS_VIEWS"].values():
            self.assertEqual(self.c.get("/static/" + v["image"]).status_code, 200, v["image"])


if __name__ == "__main__":
    unittest.main()
