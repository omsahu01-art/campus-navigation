"""HTML pages."""

from flask import Blueprint, current_app, redirect, render_template, request, url_for

from database import campus_data

pages_bp = Blueprint("pages", __name__)


def _boot_data():
    locs = current_app.config["LOCATION_SERVICE"]
    views = {}
    for key, v in current_app.config["CAMPUS_VIEWS"].items():
        views[key] = {**v, "image": url_for("static", filename=v["image"]),
                      "width": campus_data.IMAGE_W, "height": campus_data.IMAGE_H}
    section = {**campus_data.SECTION, "image": url_for("static", filename=campus_data.SECTION["image"]),
               "width": campus_data.IMAGE_W, "height": campus_data.IMAGE_H}
    return {"views": views, "section": section, "locations": locs.all_public()}


@pages_bp.get("/")
def home():
    return render_template("index.html", boot=_boot_data())


# ---- links from the old version keep working -------------------------
@pages_bp.get("/search")
def old_search():
    return redirect(url_for("pages.home"))


@pages_bp.get("/route")
def old_route():
    locs = current_app.config["LOCATION_SERVICE"]
    src = locs.resolve(request.args.get("current", ""))
    dst = locs.resolve(request.args.get("destination", ""))
    return redirect(url_for("pages.home", **{k: v for k, v in (("from", src), ("to", dst)) if v}))


@pages_bp.get("/emergency")
def old_emergency():
    locs = current_app.config["LOCATION_SERVICE"]
    src = locs.resolve(request.args.get("current", ""))
    args = {"emergency": "exit"}
    if src:
        args["from"] = src
    return redirect(url_for("pages.home", **args))
