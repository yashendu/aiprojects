import json, os, glob
from datetime import datetime, timezone


def save_run(runs_dir, benchmark_result):
    os.makedirs(runs_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    models_tested = list(benchmark_result.keys())
    metadata = {
        "run_id": ts,
        "timestamp": ts,
        "models_tested": models_tested,
        "result": benchmark_result,
    }
    path = os.path.join(runs_dir, f"{ts}.json")
    with open(path, "w") as f:
        json.dump(metadata, f, indent=2)
    return ts


def list_runs(runs_dir):
    if not os.path.isdir(runs_dir):
        return []
    files = sorted(glob.glob(os.path.join(runs_dir, "*.json")), reverse=True)
    runs = []
    for f in files:
        try:
            with open(f) as fh:
                data = json.load(fh)
            runs.append({
                "run_id": data.get("run_id", os.path.splitext(os.path.basename(f))[0]),
                "timestamp": data.get("timestamp", ""),
                "models_tested": data.get("models_tested", []),
            })
        except Exception:
            pass
    return runs


def load_run(runs_dir, run_id):
    path = os.path.join(runs_dir, f"{run_id}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)
