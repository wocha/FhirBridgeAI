---
description: how to run the full CI quality pipeline locally (black, ruff, mypy, pytest)
---

# Run CI Locally

Execute the same checks that run in the GitHub Actions CI pipeline on your local machine.

## Prerequisites

```powershell
cd c:\Projects\FhirBridgeAi
pip install -e ".[dev]"
```

## Steps

### 1. Format Check (Black)

// turbo

```powershell
cd c:\Projects\FhirBridgeAi
python -m black --check src/ tests/
```

If formatting issues are found, auto-fix with:

```powershell
python -m black src/ tests/
```

### 2. Lint (Ruff)

// turbo

```powershell
cd c:\Projects\FhirBridgeAi
python -m ruff check src/ tests/
```

Auto-fix safe issues:

```powershell
python -m ruff check --fix src/ tests/
```

### 3. Type Check (mypy)

// turbo

```powershell
cd c:\Projects\FhirBridgeAi
python -m mypy src/
```

### 4. Tests (pytest)

// turbo

```powershell
cd c:\Projects\FhirBridgeAi
python -m pytest tests/ -v
```

## All-in-One

// turbo

```powershell
cd c:\Projects\FhirBridgeAi
python -m black --check src/ tests/ && python -m ruff check src/ tests/ && python -m mypy src/ && python -m pytest tests/ -v
```
