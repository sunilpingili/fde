# FDE Week 1 Setup

This project follows the Testleaf FDE Week 1 setup playbook. It provides a small Python readiness script, a sample CSV for file/data handling practice, and a FastAPI health endpoint.

Use Python 3.13.x for the course so everyone follows the same runtime line.

## Project layout

```text
FDEBABU_1/
├── data/
│   └── sample.csv
├── src/
│   ├── app.py
│   └── hello.py
├── .gitignore
└── requirements.txt
```

The virtual environment is created locally as `.venv/` and is excluded from version control.

## Before starting

Install these tools yourself using their official instructions:

- [VS Code Insiders](https://code.visualstudio.com/insiders/)
- [Python 3.13 for Windows](https://www.python.org/downloads/windows/) or [Python 3.13 for macOS](https://www.python.org/downloads/macos/)
- VS Code extensions:
  - Python (Microsoft)
  - Pylance (Microsoft; recommended)
  - Claude Code (Anthropic)
  - Jupyter (optional)

Claude Code in VS Code requires an eligible Anthropic account, such as a supported paid Claude subscription or Claude Console account. Sign in through the Claude Code extension; do not put account credentials in this project.

## Windows setup

Open this project folder in VS Code Insiders, then open a terminal in the project root.

Verify Python 3.13 is installed:

```powershell
py -3.13 --version
```

Create and activate the virtual environment in PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Or activate it from Command Prompt:

```bat
py -3.13 -m venv .venv
.venv\Scripts\activate.bat
```

If PowerShell blocks activation, use Command Prompt or select the `.venv` interpreter in VS Code instead. Do not change system-wide security settings just to activate the environment.

## macOS setup

Open this project folder in VS Code Insiders, then open a terminal in the project root.

Verify Python 3.13 is installed:

```sh
python3.13 --version
```

Create and activate the virtual environment:

```sh
python3.13 -m venv .venv
source .venv/bin/activate
```

After activation, `which python` should point inside this project’s `.venv/` directory. Use the course Python installation rather than relying on a system-provided Python.

## Install packages and configure VS Code

Run these commands from the project root after activating `.venv`:

```sh
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -c "import requests, fastapi, uvicorn; print('Week 1 packages OK')"
```

In VS Code Insiders, open the Command Palette (`Ctrl+Shift+P` on Windows or `Cmd+Shift+P` on macOS), run **Python: Select Interpreter**, and select the interpreter inside `.venv`:

- Windows: `.venv\Scripts\python.exe`
- macOS: `.venv/bin/python`

## Pre-flight checks

### Python

With `.venv` active, run:

```sh
python src/hello.py
```

Expected output:

```text
FDE Learner is getting ready for Python
FDE Learner is getting ready for APIs
FDE Learner is getting ready for AI
```

### FastAPI

From the project root, start the API:

```sh
uvicorn src.app:app --reload
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs), expand `GET /health`, and choose **Try it out** → **Execute**. The response should be:

```json
{
  "status": "ready",
  "week": 1
}
```

If port 8000 is already in use, start the API on port 8001 instead:

```sh
uvicorn src.app:app --reload --port 8001
```

Then open [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs).

## Ready-for-class checklist

- [ ] VS Code Insiders launches.
- [ ] Python 3.13.x is installed.
- [ ] This project folder is open in VS Code Insiders.
- [ ] `.venv` is created and selected as the VS Code interpreter.
- [ ] `requests`, FastAPI, and Uvicorn are installed in `.venv`.
- [ ] `src/hello.py` prints all three lines.
- [ ] FastAPI Swagger UI opens and `GET /health` returns the expected JSON.
- [ ] Claude Code is installed and signed in with an eligible account.

## Troubleshooting

| Issue | What to try |
| --- | --- |
| `python` / `py` not found | Close and reopen VS Code after installing Python. On Windows, try `py -3.13`; on macOS, try `python3.13`. |
| Wrong interpreter | Run **Python: Select Interpreter** from the Command Palette and select the interpreter inside `.venv`. |
| Packages install globally | Activate `.venv` first, then use `python -m pip install ...`. Confirm `python` resolves to the `.venv` interpreter. |
| PowerShell activation is blocked | Use Command Prompt activation or select the `.venv` interpreter directly in VS Code. |
| Port 8000 is already in use | Start Uvicorn with `--port 8001` and open the corresponding `/docs` URL. |
| Claude Code panel is not visible | Restart VS Code Insiders or run **Developer: Reload Window**; search for “Claude Code” in the Command Palette. |
