# GPU Cluster Health Triage

Role fit: AI infrastructure, GPU systems, performance engineering, SRE-adjacent backend, ML infrastructure, and NVIDIA/Cohere-style systems roles.

This project analyzes synthetic GPU cluster telemetry and turns noisy node metrics into triage priorities. It is not CUDA development, but it demonstrates practical systems thinking around utilization, memory pressure, error counts, temperature, job failures, and reliability signals.

## Features

- Reads GPU node telemetry from CSV.
- Scores health risk from temperature, ECC errors, memory pressure, utilization, and job failures.
- Produces ranked triage recommendations.
- Writes JSON and Markdown reports.

## Run

```bash
python app.py --input samples/gpu_nodes.csv --out report
```

## Resume Bullets

- Built a Python GPU cluster triage tool that ranks nodes by health risk using utilization, memory pressure, temperature, ECC errors, and job-failure signals.
- Implemented scoring and recommendation logic to convert noisy infrastructure telemetry into prioritized debugging actions.
- Generated JSON and Markdown reports for AI infrastructure review workflows.
