import os

import flask
from flask import request

from src.engine import main

__all__ = ["main"]

app = flask.Flask(__name__)
PORT = int(os.environ.get("PORT", 5000))


@app.route("/", methods=["POST"])
def make_test():
    return main(request)


@app.route("/ping", methods=["GET"])
def index():
    return "<h1>Engine working fine</h1>"


if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=PORT, debug=True)
