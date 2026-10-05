"""JSON API used by the web front-end."""

from flask import Blueprint, current_app, jsonify, request

from navigation.router import RouteError, compute_emergency, compute_route

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _svc():
    return current_app.config["LOCATION_SERVICE"], current_app.config["CAMPUS_GRAPH"]


def _flag(name):
    return request.args.get(name, "").lower() in ("1", "true", "yes", "on")


@api_bp.errorhandler(RouteError)
def _route_error(err):
    status = 404 if err.code == "unknown_location" else 400
    return jsonify({"ok": False, "error": err.message, "code": err.code}), status


@api_bp.get("/health")
def health():
    locs, graph = _svc()
    return jsonify({"ok": True, "locations": len(locs.locations), "nodes": len(graph.adj),
                    "version": current_app.config["APP_VERSION"]})


@api_bp.get("/locations")
def locations():
    locs, _ = _svc()
    return jsonify(locs.all_public())


@api_bp.get("/search")
def search():
    locs, _ = _svc()
    return jsonify(locs.search(request.args.get("q", ""), limit=int(request.args.get("limit", 12))))


@api_bp.get("/route")
def route():
    locs, graph = _svc()
    src_raw = request.args.get("from", "").strip()
    dst_raw = request.args.get("to", "").strip()
    if not src_raw or not dst_raw:
        raise RouteError("Please choose both a starting point and a destination.", "missing_input")
    src, dst = locs.resolve(src_raw), locs.resolve(dst_raw)
    if not src:
        raise RouteError(f"We could not find the starting point '{src_raw}'.", "unknown_location")
    if not dst:
        raise RouteError(f"We could not find the destination '{dst_raw}'.", "unknown_location")
    return jsonify(compute_route(graph, locs, src, dst, accessible=_flag("accessible")))


@api_bp.get("/emergency")
def emergency():
    locs, graph = _svc()
    src_raw = request.args.get("from", "").strip()
    if not src_raw:
        raise RouteError("Tell us where you are first, then we can find the nearest help.", "missing_input")
    src = locs.resolve(src_raw)
    if not src:
        raise RouteError(f"We could not find your location '{src_raw}'.", "unknown_location")
    kind = "medical" if request.args.get("type") == "medical" else "exit"
    return jsonify(compute_emergency(graph, locs, src, kind))
