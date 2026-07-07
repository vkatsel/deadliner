# Deadliner

Deadliner is a CLI tool that fetches upcoming assignments from your Moodle courses and displays them in your local timezone, sorted by deadline.

## Quickstart (Under 5 minutes)

### 1. Installation

Clone the repository and install dependencies (requires Python 3.12+):

```bash
git clone https://github.com/CS460-SEP-2026/greenfield.git
cd greenfield
python -m pip install -r requirements.txt
```

### 2. Configuration & Login

Log in to your Moodle account interactively to automatically save your credentials:

**Windows (PowerShell):**
```powershell
$env:PYTHONPATH="src"; python -m deadliner.cli login moodle
```

**Linux / macOS:**
```bash
PYTHONPATH=src python -m deadliner.cli login moodle
```

*(This will ask for your Moodle URL, username, and password, and safely save your API token to `~/.deadliner.json`)*

Alternatively, you can manually set `DEADLINER_MOODLE_URL` and `DEADLINER_MOODLE_TOKEN` environment variables, or provide a Google Classroom token via `DEADLINER_GOOGLE_TOKEN`.

### 3. Run the App

Fetch and display your upcoming deadlines:

**Windows (PowerShell):**
```powershell
$env:PYTHONPATH="src"; python -m deadliner.cli fetch
```

**Linux / macOS:**
```bash
PYTHONPATH=src python -m deadliner.cli fetch
```

### 4. Run Tests

Run the full test suite with one command:
```bash
pytest -v tests/
```
