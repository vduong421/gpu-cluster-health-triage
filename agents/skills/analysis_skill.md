# Validation Analysis Skill

## When Used

Use this skill when the user asks about validation quality, failure clusters, flaky tests, root cause, or release readiness.

## Input

- validation summary
- failed test rows
- flaky test list
- failure breakdown by subsystem and error type

## Output

Return:

- answer
- evidence
- next_action
- recommendation
- decision

## Rules

- Mention exact deterministic metrics.
- Prioritize repeated failures over isolated failures.
- If release risk exists, clearly say whether to hold or proceed.