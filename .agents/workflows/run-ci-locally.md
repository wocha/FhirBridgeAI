---
description: how to run the full CI quality pipeline locally (black, ruff, mypy, pytest)
---

# Run CI Locally

Execute the same checks that run in the GitHub Actions CI pipeline on your local machine.

## Prerequisites

```bash
cd <project-root>
python3 -m pip install -e ".[dev]"
```

## Steps

### 1. Format Check (Black)

// turbo

```bash
cd <project-root>
python3 -m black --check src/ tests/
```

If formatting issues are found, auto-fix with:

```bash
python3 -m black src/ tests/
```

### 2. Lint (Ruff)

// turbo

```bash
cd <project-root>
python3 -m ruff check src/ tests/
```

Auto-fix safe issues:

```bash
python3 -m ruff check --fix src/ tests/
```

### 3. Type Check (mypy)

// turbo

```bash
cd <project-root>
python3 -m mypy src/
```

### 4. Tests (pytest)

// turbo

```bash
cd <project-root>
python3 -m pytest tests/ -v
```

## All-in-One

// turbo

```bash
cd <project-root>
python3 -m black --check src/ tests/ && python3 -m ruff check src/ tests/ && python3 -m mypy src/ && python3 -m pytest tests/ -v
```
