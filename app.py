import argparse
import csv
import json
from pathlib import Path


def to_float(value):
    return float(value)


def score_node(row):
    score = 0
    reasons = []

    temp = to_float(row["temperature_c"])
    mem = to_float(row["memory_used_pct"])
    util = to_float(row["gpu_util_pct"])
    ecc = int(row["ecc_errors_24h"])
    failures = int(row["job_failures_24h"])

    if temp >= 82:
        score += 30
        reasons.append("high temperature")
    if mem >= 92:
        score += 20
        reasons.append("memory pressure")
    if ecc > 0:
        score += min(30, ecc * 10)
        reasons.append("ECC errors")
    if failures >= 3:
        score += 20
        reasons.append("repeated job failures")
    if util < 15 and failures > 0:
        score += 10
        reasons.append("low utilization with failures")

    if score >= 50:
        priority = "P1"
    elif score >= 25:
        priority = "P2"
    elif score > 0:
        priority = "P3"
    else:
        priority = "OK"

    return {
        "node": row["node"],
        "model": row["gpu_model"],
        "risk_score": score,
        "priority": priority,
        "reasons": reasons,
        "recommendation": recommend(priority, reasons),
    }


def recommend(priority, reasons):
    if priority == "P1":
        return "Drain node, preserve logs, inspect thermals/ECC counters, and rerun failed workload."
    if priority == "P2":
        return "Schedule validation rerun and compare telemetry against neighboring nodes."
    if priority == "P3":
        return "Monitor trend and include in next health review."
    return "No immediate action."


def write_markdown(path, ranked):
    lines = ["# GPU Cluster Health Triage", "", "## Ranked Nodes", ""]
    for item in ranked:
        reasons = ", ".join(item["reasons"]) if item["reasons"] else "none"
        lines.append(
            f"- {item['priority']} {item['node']} ({item['model']}): score={item['risk_score']}; reasons={reasons}; action={item['recommendation']}"
        )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", default="report")
    args = parser.parse_args()

    with Path(args.input).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    ranked = sorted((score_node(row) for row in rows), key=lambda item: item["risk_score"], reverse=True)
    summary = {
        "nodes": len(ranked),
        "p1": sum(1 for item in ranked if item["priority"] == "P1"),
        "p2": sum(1 for item in ranked if item["priority"] == "P2"),
        "ok": sum(1 for item in ranked if item["priority"] == "OK"),
    }
    Path(f"{args.out}.json").write_text(json.dumps({"summary": summary, "nodes": ranked}, indent=2), encoding="utf-8")
    write_markdown(f"{args.out}.md", ranked)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
