# WSL/Linux Execution Rules

This repository uses WSL/Linux as the canonical local execution environment.

## Rules

1. Use Bash-compatible commands in repository documentation, runbooks, and agent workflows.
2. Use forward-slash paths and placeholders such as `<project-root>` in public documentation.
3. Use `python3`, `python3 -m pip`, `python3 -m pytest`, and `docker compose` for local command examples.
4. Keep Windows-native command syntax and machine-local paths out of tracked documentation.
