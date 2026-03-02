# Windows PowerShell Execution Rules

This repository heavily uses local terminal execution for microservices and data scripts. To prevent common 'CommandNotFoundException' errors on Windows PowerShell (often triggering redirects to the Microsoft Store), always adhere to the following execution standards:

## 1. Python Execution

**DO NOT** use `python`.
**ALWAYS** use the Python Launcher for Windows: `py`.
Example: `py worker.py`

## 2. Pip Execution

**DO NOT** use `pip install`.
**ALWAYS** use the Python Launcher to invoke the pip module: `py -m pip install`.
Example: `py -m pip install pydantic`

## 3. Process Management

When killing a background process programmatically from PowerShell, do not rely on standard Linux commands or incomplete process kill logic. Use `Get-WmiObject` or `Get-Process` piped to `Stop-Process`.

**Example:** Killing any process matching a script name:

```powershell
Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -match "worker.py" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```
