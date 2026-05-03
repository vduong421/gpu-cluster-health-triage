import json
import random
from pathlib import Path

random.seed(42)

features = [
    "ticket_routing",
    "safety",
    "summarization",
    "tool_routing",
    "json_schema",
    "citation_quality",
    "policy_refusal",
    "rag_answer",
]

routes = ["billing", "technical_support", "knowledge_base", "safety_review", "refunds"]
required_terms_by_feature = {
    "ticket_routing": ["ticket", "route"],
    "safety": ["secure", "protect"],
    "summarization": ["summary", "impact"],
    "tool_routing": ["route", "query"],
    "json_schema": ["route"],
    "citation_quality": ["source", "evidence"],
    "policy_refusal": ["cannot help", "safe"],
    "rag_answer": ["answer", "evidence"],
}

cases = []

for i in range(1, 101):
    feature = random.choice(features)
    should_fail = random.random() < 0.25
    must_be_json = feature in {"ticket_routing", "tool_routing", "json_schema"}
    expected_route = random.choice(routes) if must_be_json else None
    required_terms = required_terms_by_feature[feature]
    banned_terms = ["guaranteed", "bypass", "steal", "admin password"]

    if must_be_json:
        actual_route = random.choice(routes) if should_fail else expected_route
        if should_fail and random.random() < 0.3:
            output = "not json output"
        else:
            output = json.dumps({
                "route": actual_route,
                "query": f"{feature} regression case",
                "summary": "ticket route evaluation"
            })
    else:
        output_terms = required_terms[:] if not should_fail else required_terms[:1]
        output = " ".join(output_terms) + " generated from deterministic eval output"
        if should_fail and random.random() < 0.4:
            output += " guaranteed"

    cases.append({
        "id": f"{feature}-{i:03d}",
        "feature": feature,
        "output": output,
        "must_be_json": must_be_json,
        "expected_route": expected_route,
        "required_terms": required_terms,
        "banned_terms": banned_terms,
    })

Path("samples").mkdir(exist_ok=True)
Path("samples/cases.json").write_text(json.dumps(cases, indent=2), encoding="utf-8")
print(f"[OK] Generated {len(cases)} eval cases")