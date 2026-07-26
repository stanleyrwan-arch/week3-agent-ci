# Guardrails and Blast-Radius Limits

## Purpose

The remediation agent assists with one narrowly defined CI failure while preserving human control. It is not a general-purpose autonomous coding agent.

## Supported Failure Class

The only supported failure is:

    ModuleNotFoundError

The intended case is a Python module importing a package that is missing from `requirements.txt`.

Unsupported failures include:

- Assertion failures
- Logic defects
- Syntax errors
- Security findings
- Infrastructure failures
- Deployment failures
- Environment-variable failures
- Network failures

For unsupported failures, the agent must stop without changing the repository.

## Allowed Modification

The agent may modify only:

    requirements.txt

It may add exactly one approved dependency.

It must not modify:

- Files under `src/`
- Files under `tests/`
- GitHub Actions workflows
- Jenkinsfiles
- Dockerfiles
- Infrastructure-as-code files
- Deployment configuration
- Secret configuration
- Environment variables
- Branch-protection settings
- Existing dependency versions

## Dependency Allowlist

The deterministic allowlist is:

    APPROVED_DEPENDENCIES = {
        "humanize": "humanize",
    }

An LLM recommendation is rejected unless:

1. The build log contains a matching `ModuleNotFoundError`.
2. The missing module is extracted deterministically.
3. The LLM reports the same missing module.
4. The recommended package matches the allowlist.
5. The agent marks the proposal as safe.
6. Only one dependency is proposed.

The LLM cannot expand the allowlist.

## Test-Selection Safety

Tests are skipped only when all changed files are recognized as documentation or workflow-only changes.

Known source files map to specific tests.

Unknown source-code changes trigger the full suite.

Shared configuration and dependency changes also trigger the full suite.

This design favors running too many tests over accidentally skipping a relevant test.

## Repository Permissions

The workflow declares:

    permissions:
      contents: write
      pull-requests: write
      actions: read

These permissions allow the workflow to:

- Create a remediation branch
- Commit the approved `requirements.txt` change
- Open a pull request
- Read workflow artifacts

The agent does not receive repository-administration permissions.

## Pull-Request Restrictions

The agent may:

- Create a bot branch
- Commit the single approved change
- Open a pull request
- Describe the root cause and proposed fix

The agent may not:

- Push directly to `main`
- Merge the pull request
- Approve its own pull request
- Modify branch protection
- Bypass required checks
- Trigger production deployment

## Human Approval Gate

The workflow uses the GitHub Environment:

    agent-proposed

The `human-approval` job cannot begin until a human reviewer explicitly chooses:

    Approve and deploy

The reviewer may instead reject the workflow.

There is no automatic approval after a timeout. Without human approval, the workflow remains blocked.

## Reviewer Checklist

Before approval, the reviewer verifies:

- The build log contains `ModuleNotFoundError`.
- The identified missing module is correct.
- The proposed package matches the import.
- The package is allowlisted.
- Only `requirements.txt` changed.
- No dependency was removed or upgraded.
- No source, test, CI, deployment, or secret files changed.
- The PR description accurately explains the root cause.
- Tests will be rerun after the remediation is merged.

## Logging and Auditability

The workflow records:

- Changed files
- Selected test targets
- Test exit code
- Build log artifact
- Failure class
- Root-cause description
- Fix description
- Proposed dependency
- Pull-request commit and diff
- Human approval event

These records provide an audit trail for both the agent decision and the human approval.

## Safe Failure Behavior

The workflow stops when:

- No supported error is found
- The build log is missing
- The proposal is ambiguous
- The dependency is not allowlisted
- The LLM output conflicts with deterministic parsing
- Authentication is missing
- Repository permissions are insufficient
- PR creation fails
- Human approval is not provided

No failure condition results in an automatic merge.

## Credential Handling

Secrets are provided through GitHub Actions environment variables and are not committed to the repository.

The workflow must not print token values.

Credentials should be:

- Minimally scoped
- Rotated when exposed or invalid
- Stored only in approved secret storage
- Validated for empty or malformed values
- Never embedded in repository URLs

## Production Improvements

For production use, additional controls should include:

- Branch protection requiring independent review
- CODEOWNERS review for dependency changes
- Dependency vulnerability scanning
- Package-name and supply-chain verification
- Version pinning
- Lockfile regeneration and review
- Full test-suite execution on the remediation PR
- LLM cost and rate limits
- Centralized audit logs
- Automated rollback procedures
- Separation of development and production credentials

## Core Principle

The agent may diagnose and propose, but deterministic policy and a human reviewer decide whether the change proceeds.

Removing the human reviewer must leave the workflow unable to merge or deploy the change.
