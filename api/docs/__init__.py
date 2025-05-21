# api/docs/__init__.py
from flask import Blueprint, render_template

docs_blueprint = Blueprint(
    "docs", __name__, url_prefix="/docs", template_folder="templates"
)


@docs_blueprint.route("/")
def index():
    return render_template("docs/index.html")


@docs_blueprint.route("/reference")
def reference():
    return render_template("docs/reference.html")


@docs_blueprint.route("/examples")
def examples():
    return render_template("docs/examples.html")
