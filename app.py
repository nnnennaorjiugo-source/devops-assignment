from flask import Flask, redirect, jsonify
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

from prometheus_flask_exporter import PrometheusMetrics
metrics = PrometheusMetrics(app)


@app.route("/sergei", methods=["GET"])
def sergei_route():
    logger.info("sergei route hit")
    return "Sergei Fixed It!"


@app.route("/raditya", methods=["GET"])
def raditya_route():
    logger.info("raditya route hit")
    return "Raditya Is Batman!"


@app.route("/", methods=["GET"])
def root_route():
    return redirect(random.choice(["/raditya", "/sergei"]), code=302)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/ready", methods=["GET"])
def ready():
    return jsonify({"status": "ready"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
