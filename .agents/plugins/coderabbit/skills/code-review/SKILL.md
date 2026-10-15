---
name: code-review
description: "Run automated code reviews, inspect git diffs, audit code quality, detect security vulnerabilities (SQL injection, XSS, input sanitization), and evaluate edge cases."
license: MIT
---

# Code Review Skill

Conduct a thorough review of modified code before phase completion.

## Review Workflow
1. Inspect git status and changed files.
2. Verify security constraints: parameterization, boundary checks, input escaping.
3. Verify test coverage: ensure new logic has corresponding test verification.
4. Report findings categorized by severity (Critical, Major, Minor, Info).
5. Address all Critical and Major findings before sign-off.

