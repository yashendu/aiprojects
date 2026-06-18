import time, sys, traceback
from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage, SystemMessage

from . import test_suites
from .evaluator import build_judge, evaluate_speed, evaluate_quality


def log(msg):
    print(f"[benchmark] {msg}", flush=True)


def _compute_app_suggestions(config, model_results):
    suggestions = {}
    for app in config.get("apps", []):
        app_name = app["name"]
        app_label = app["label"]
        weights = app.get("metric_weights", {})
        candidates = []
        for mname, mr in model_results.items():
            if "error" in mr:
                continue
            metrics = mr.get("metrics", {})
            if not weights:
                total = sum(m["score"] for m in metrics.values())
                count = len(metrics)
                wscore = total / count if count else 0
            else:
                num = den = 0
                for mk, mw in weights.items():
                    ms = metrics.get(mk, {})
                    num += ms.get("score", 0) * mw
                    den += mw
                wscore = num / den if den else 0
            candidates.append((mname, wscore, mr["label"], mr["metrics"].get("response_speed", {}).get("avg_time_s", 999)))
        if candidates:
            best = max(candidates, key=lambda x: (x[1], -x[3]))
            suggestions[app_name] = {
                "label": app_label,
                "best_model": best[0],
                "best_model_label": best[2],
                "best_weighted_score": round(best[1], 2),
                "all_weighted_scores": {m: round(s, 2) for m, s, _, _ in candidates},
                "all_models": sorted([{"name": m, "label": l, "score": round(s, 2)} for m, s, l, _ in candidates], key=lambda x: -x["score"]),
            }
    return suggestions


def run_benchmark(config):
    host = config["ollama"]["host"]
    models = config["models"]
    judge_cfg = config["benchmark"]
    runs_dir = judge_cfg["runs_dir"]

    log("Initializing judge model ...")
    judge = build_judge(host, judge_cfg["judge_model"], judge_cfg["judge_temperature"])
    metrics = test_suites.METRICS
    results = {}

    for mod in models:
        if mod["type"] != "generation":
            continue
        mname = mod["name"]
        log(f"Benchmarking {mname} ({mod['label']}) ...")
        try:
            llm = ChatOllama(model=mname, base_url=host, temperature=0.1, num_predict=256, timeout=120)
            # Quick warm-up call to verify model exists
            log(f"  Warming up {mname} ...")
            try:
                llm.invoke([HumanMessage(content="Hello")])
            except Exception as e:
                log(f"  Warm-up failed for {mname}: {e}")
                results[mname] = {"label": mod["label"], "error": str(e), "metrics": {}}
                continue

            model_result = {"label": mod["label"], "metrics": {}}

            for mkey, mdef in metrics.items():
                log(f"  Metric: {mkey} ({mdef['label']}) ...")
                scores = []
                reasons = []
                times = []
                for qi, q in enumerate(mdef["questions"]):
                    context = None
                    prompt = q
                    if isinstance(q, dict):
                        context = q.get("context", "")
                        prompt = f"Context: {context}\n\nQuestion: {q['question']}\n\nAnswer based only on the context provided."
                    else:
                        prompt = q

                    start = time.time()
                    try:
                        resp = llm.invoke([HumanMessage(content=prompt)])
                        elapsed = time.time() - start
                    except Exception as e:
                        resp = type("R", (), {"content": f"Error: {e}"})()
                        elapsed = 999

                    if mkey == "response_speed":
                        sc = evaluate_speed(elapsed)
                        reas = f"Took {elapsed:.1f}s"
                    else:
                        sc, reas = evaluate_quality(judge, mkey, q if not isinstance(q, dict) else q["question"], resp.content, context)

                    scores.append(sc)
                    reasons.append(reas)
                    times.append(elapsed)
                    log(f"    Q{qi+1}: score={sc}, time={elapsed:.1f}s")

                avg_score = sum(scores) / len(scores) if scores else 0
                avg_time = sum(times) / len(times) if times else 0
                model_result["metrics"][mkey] = {
                    "label": mdef["label"],
                    "description": mdef["description"],
                    "score": round(avg_score, 2),
                    "avg_time_s": round(avg_time, 2),
                    "per_question": [
                        {"q": q if not isinstance(q, dict) else q["question"], "score": s, "reason": r, "time_s": round(t, 2)}
                        for q, s, r, t in zip(mdef["questions"], scores, reasons, times)
                    ],
                }

            scores_list = [m["score"] for m in model_result["metrics"].values()]
            model_result["overall"] = round(sum(scores_list) / len(scores_list), 2)
            results[mname] = model_result
            log(f"  Done {mname}. Overall: {model_result['overall']}")

        except Exception as e:
            log(f"  Fatal error for {mname}: {traceback.format_exc()}")
            results[mname] = {"label": mod["label"], "error": str(e), "metrics": {}}

    suggestions = _compute_app_suggestions(config, results)
    log(f"Benchmark complete. Tested {len(results)} models.")
    return {"models": results, "app_suggestions": suggestions}
