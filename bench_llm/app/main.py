import os, threading
from flask import Flask, jsonify, render_template, request
from .benchmark_agent import run_benchmark
from .storage import save_run, list_runs, load_run
from . import test_suites

app = Flask(__name__)
CONFIG_PATH = "/app/config.yaml"


def load_config():
    import yaml
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


CONFIG = load_config()
RUNS_DIR = CONFIG["benchmark"]["runs_dir"]
RUNNING = threading.Event()


@app.route("/")
def index():
    runs = list_runs(RUNS_DIR)
    latest_run_id = runs[0]["run_id"] if runs else None
    latest = load_run(RUNS_DIR, latest_run_id) if latest_run_id else None
    return render_template("index.html",
                           runs=runs,
                           latest=latest,
                           metrics=test_suites.METRICS,
                           models=CONFIG["models"],
                           apps=CONFIG["apps"],
                           running=RUNNING.is_set())


@app.route("/api/benchmark", methods=["POST"])
def trigger_benchmark():
    if RUNNING.is_set():
        return jsonify({"error": "A benchmark is already running."}), 409
    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"status": "started"})


def _run():
    RUNNING.set()
    try:
        result = run_benchmark(CONFIG)
        save_run(RUNS_DIR, result)
    finally:
        RUNNING.clear()


@app.route("/api/status")
def status():
    return jsonify({"running": RUNNING.is_set()})


@app.route("/api/runs")
def api_runs():
    runs = list_runs(RUNS_DIR)
    return jsonify({"runs": runs})


@app.route("/api/runs/<run_id>")
def api_run_detail(run_id):
    data = load_run(RUNS_DIR, run_id)
    if not data:
        return jsonify({"error": "Run not found"}), 404
    return jsonify(data)


@app.route("/api/metrics")
def api_metrics():
    return jsonify({k: {"label": v["label"], "description": v["description"]} for k, v in test_suites.METRICS.items()})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
