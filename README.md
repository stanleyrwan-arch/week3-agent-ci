# Week 3 Assignment — Agent-Optimized CI Pipeline

**Student:** ZIZE WAN  
**Course:** CSE636 DevOps  
**Repository:** `week3-agent-ci`

## Overview

This project implements an agent-optimized CI pipeline with two automation capabilities:

1. Test-impact analysis that selects only tests relevant to changed files.
2. Scoped remediation for `ModuleNotFoundError` caused by a missing dependency in `requirements.txt`.

The pipeline uses GitHub Actions, Python, pytest, Anthropic Claude, and PyGithub. The AI agent may propose a narrowly scoped pull request, but it cannot merge its own change. A human approval gate is required before the workflow completes.

## Project Structure

    .
    ├── .github/workflows/ci-agent.yml
    ├── docs/guardrails.md
    ├── scripts/remediation_agent.py
    ├── scripts/select_tests.py
    ├── src/calculator.py
    ├── src/http_utils.py
    ├── src/text_utils.py
    ├── tests/
    └── requirements.txt

## CI Pipeline

The GitHub Actions workflow contains four jobs:

    select-tests
    → test
    → remediation
    → human-approval

## Test Selection

`scripts/select_tests.py` compares changed files between two Git references and selects the minimum relevant test set.

| Changed file | Selected tests |
|---|---|
| `src/calculator.py` | `tests/test_calculator.py` |
| `src/text_utils.py` | `tests/test_text_utils.py` |
| `src/http_utils.py` | `tests/test_http_utils.py` |
| A specific test file | That test file |
| Shared configuration or dependencies | Full test suite |
| Documentation/workflow-only changes | Skip application tests |
| Unknown source-code changes | Full test suite |

The selector uses a safety-first fallback. If it cannot confidently determine test impact, it runs the full suite.

### Demonstrated Results

A workflow-only change produced:

    TEST_MODE=skip
    SELECTED_TESTS=
    No relevant code changes; tests may be skipped.

A change to `src/http_utils.py` selected only:

    tests/test_http_utils.py

This demonstrated that the pipeline skips irrelevant work and narrows relevant test execution.

## Scoped Remediation Agent

The remediation agent handles exactly one failure class:

    ModuleNotFoundError

The demo application imports `humanize`, while `humanize` is intentionally absent from `requirements.txt`. In GitHub Actions, test collection failed with:

    ModuleNotFoundError: No module named 'humanize'

The agent correctly reported:

    Failure class: ModuleNotFoundError
    Package: humanize

It proposed adding only:

    humanize

to `requirements.txt`.

## Deterministic Validation

The LLM response is not trusted by itself. The remediation script also verifies that:

- The failure class is exactly `ModuleNotFoundError`.
- The missing module matches the build log.
- The agent marks the proposal as safe.
- The recommended package matches the missing import.
- The package appears in an explicit allowlist.
- Only one dependency is added.
- Existing dependencies are not removed or upgraded.

The current allowlist is:

    APPROVED_DEPENDENCIES = {
        "humanize": "humanize",
    }

If the failure is ambiguous or the dependency is not allowlisted, the agent refuses to create a PR.

## Pull Request and Human Approval

The agent created a bot branch and a pull request containing one change:

    +humanize

The PR documented:

- Root cause
- Proposed fix
- Deterministic allowlist validation
- File-scope restrictions
- Human-review requirement

The workflow then paused at the `agent-proposed` GitHub Environment. A human reviewer had to choose either:

    Reject
    Approve and deploy

The agent could not approve or merge the PR automatically.

## Guardrails

The main safeguards are:

- One supported failure class
- Explicit dependency allowlist
- One-file modification limit
- No source-code or test modification
- No workflow or infrastructure modification
- No automatic merge
- Required environment approval
- Logged root cause and fix description
- Full-suite fallback when test impact is uncertain

Detailed controls are documented in `docs/guardrails.md`.

## Results

The implementation demonstrated both required automation tasks.

### Test optimization

- Documentation and workflow-only changes skipped application tests.
- A change to `src/http_utils.py` selected only `tests/test_http_utils.py`.
- Unknown or shared changes fall back to the full suite.

### Auto-remediation

- CI detected the missing `humanize` dependency.
- The agent correctly classified the failure.
- The proposal passed deterministic allowlist validation.
- The agent changed only `requirements.txt`.
- A pull request was created successfully.
- The workflow paused for human approval.

## Failure and Unexpected Behavior

The agent identified the missing dependency correctly, but PR creation exposed several operational failure modes.

First, `ANTHROPIC_API_KEY` was missing from the workflow. Next, `GH_TOKEN` was empty. A copied token then contained an invisible Unicode line-separator character, which caused an HTTP header encoding error. After that was corrected, the personal access token returned `403 Forbidden` because it lacked permission to create a Git reference.

The final workflow used the GitHub Actions-provided token with explicit permissions:

    permissions:
      contents: write
      pull-requests: write
      actions: read

This showed that model accuracy is only one part of a production agent workflow. Credential handling, permission scope, API behavior, and auditability are equally important.

## Prompt Design

The system prompt instructs the agent to:

- Handle only `ModuleNotFoundError`
- Propose exactly one dependency
- Never modify source code
- Never modify tests
- Never modify workflows or infrastructure
- Never alter secrets or environment variables
- Refuse ambiguous failures
- Avoid unrelated changes

This keeps the blast radius narrow and makes the proposal easy to review.

## AI Tool Disclosure

Anthropic Claude was used inside the remediation pipeline to classify the build failure and propose the missing dependency.

ChatGPT was used during implementation to help design the pipeline, create scripts, diagnose CI and credential failures, and prepare documentation.

All generated code and recommendations were reviewed, tested, and revised by the student before submission. The agent-created pull request was reviewed through the required human approval gate.

## Conclusion

This assignment demonstrated that an AI agent can improve CI efficiency and help remediate a narrowly defined failure, but only when deterministic checks and human approval remain in control.

The test selector reduces unnecessary work, while the remediation agent proposes a minimal change. The agent cannot merge its own PR, preserving human accountability.
