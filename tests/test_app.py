from app import score_node


def test_score_node_marks_high_risk_gpu_as_p1():
    result = score_node({
        "node": "gpu-a02",
        "gpu_model": "A100",
        "gpu_util_pct": "8",
        "memory_used_pct": "35",
        "temperature_c": "84",
        "ecc_errors_24h": "1",
        "job_failures_24h": "4",
    })

    assert result["priority"] == "P1"
    assert result["risk_score"] == 70
    assert "high temperature" in result["reasons"]
    assert "ECC errors" in result["reasons"]
    assert "repeated job failures" in result["reasons"]


def test_score_node_marks_healthy_gpu_ok():
    result = score_node({
        "node": "gpu-a01",
        "gpu_model": "A100",
        "gpu_util_pct": "91",
        "memory_used_pct": "88",
        "temperature_c": "76",
        "ecc_errors_24h": "0",
        "job_failures_24h": "0",
    })

    assert result["priority"] == "OK"
    assert result["risk_score"] == 0
