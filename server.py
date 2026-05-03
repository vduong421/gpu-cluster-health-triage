import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from collections import Counter

from app import score_node

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
DATA = ROOT / "samples" / "gpu_nodes.csv"

try:
    from local_llm import chat_json
except:
    chat_json = None


def load_data():
    import csv
    rows = []
    with DATA.open() as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(score_node(r))
    return rows


nodes = load_data()


def enrich():
    global summary, ranked
    ranked = sorted(nodes, key=lambda x: x["risk_score"], reverse=True)
    summary = {
        "nodes": len(ranked),
        "p1": sum(1 for x in ranked if x["priority"] == "P1"),
        "p2": sum(1 for x in ranked if x["priority"] == "P2"),
        "ok": sum(1 for x in ranked if x["priority"] == "OK"),
    }

    counts = Counter(x["priority"] for x in ranked)

    return {
        "summary": summary,
        "nodes": ranked,
        "priority_counts": dict(counts),
        "top_risk": ranked[:5],
        "worst": [x for x in ranked if x["priority"] == "P1"]
    }


report = enrich()

def build_ai_analyst():
    top = report["top_risk"][:3]
    return {
        "result": f"{report['summary']['p1']} P1 nodes, {report['summary']['p2']} P2 nodes detected",
        "recommendation": "Prioritize draining P1 nodes and investigating ECC + thermal issues",
        "decision": "Block scheduling on P1 nodes",
        "risks": [
            "thermal instability",
            "ECC degradation",
            "repeated workload failure"
        ],
        "operator_actions": [
            "drain P1 nodes",
            "check ECC logs",
            "inspect cooling and rerun jobs"
        ],
        "summary": "Top risky nodes: " + ", ".join(n["node"] for n in top)
    }

ai_analyst = build_ai_analyst()


def fallback(q):
    ql = q.lower()
    top = report["top_risk"]
    p1 = report["summary"]["p1"]
    p2 = report["summary"]["p2"]

    if "risk" in ql:
        return {
            "answer": f"Top risky nodes: {', '.join(n['node'] for n in top[:5])}",
            "evidence": f"{p1} P1 nodes and {p2} P2 nodes detected",
            "next_action": "Investigate highest risk nodes first",
            "recommendation": "Focus on nodes with highest risk_score",
            "decision": "Block scheduling on top risk nodes",
            "risks": ["thermal", "ecc", "instability"],
            "operator_actions": ["drain nodes", "inspect hardware"]
        }

    elif "root" in ql or "cause" in ql:
        return {
            "answer": "Primary issues are thermal and ECC related failures",
            "evidence": ", ".join(n["node"] for n in top),
            "next_action": "Check ECC logs and cooling systems",
            "recommendation": "Group failures by subsystem and error pattern",
            "decision": "Fix root causes before scaling workloads",
            "risks": ["ecc", "thermal"],
            "operator_actions": ["check logs", "validate cooling"]
        }

    elif "fix" in ql or "action" in ql:
        return {
            "answer": "Immediate action required on P1 nodes",
            "evidence": f"{p1} critical nodes identified",
            "next_action": "Drain nodes and rerun validation",
            "recommendation": "Resolve ECC and thermal issues first",
            "decision": "Do not schedule workloads on unstable nodes",
            "risks": ["hardware degradation"],
            "operator_actions": ["drain nodes", "rerun jobs"]
        }

    elif "behavior" in ql or "system" in ql:
        return {
            "answer": f"Cluster has {p1} critical nodes affecting stability",
            "evidence": f"Total nodes: {report['summary']['nodes']}",
            "next_action": "Monitor failure propagation",
            "recommendation": "Improve system stability before scaling",
            "decision": "System not stable for production load",
            "risks": ["instability"],
            "operator_actions": ["monitor cluster", "analyze patterns"]
        }

    else:
        return {
            "answer": f"{p1} P1 nodes detected.",
            "evidence": ", ".join(n["node"] for n in top),
            "next_action": "Drain and inspect P1 nodes",
            "recommendation": "Fix thermal/ECC issues first",
            "decision": "Block scheduling on failing nodes",
            "risks": ["thermal", "ecc", "failures"],
            "operator_actions": ["drain nodes", "check logs"]
        }


def ask(q):
    if chat_json is None:
        return fallback(q)

    prompt = f"""
Use ONLY this GPU cluster report:
{json.dumps(report)}

Answer:
{q}

Return JSON:
answer, evidence, next_action, recommendation, decision, risks, operator_actions
"""
    try:
        return chat_json(prompt)
    except:
        return fallback(q)


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api":
            self._json({
                **report,
                "ai_analyst": ai_analyst
            })
            return

        p = "index.html" if self.path == "/" else self.path[1:]
        f = WEB / p

        if f.exists():
            self.send_response(200)
            self.end_headers()
            self.wfile.write(f.read_bytes())
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/ask":
            l = int(self.headers.get("Content-Length", 0))
            q = self.rfile.read(l).decode()
            self._json(ask(q))

    def _json(self, d):
        b = json.dumps(d).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)


HTTPServer(("127.0.0.1", 8020), H).serve_forever()