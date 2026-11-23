# ADR-005: Mandatory Human Approval Gate for Browser Automation

## Status
Accepted

## Context
Automated form filling and application submission can carry significant consequences for student careers (e.g. incorrect submissions, duplicate applications, violating terms of service).

## Decision
Enforce a hard stop in the Playwright execution agent: every automated application preparation must generate a dry-run screenshot and wait for explicit student confirmation before submitting. The engine will never bypass CAPTCHA.

## Consequences
- **Positive:** Absolute safety, user trust, ethical compliance, and complete auditability.
- **Negative:** Requires an interactive student prompt step instead of zero-touch execution.
