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

### 2. Configuration

Set your Moodle credentials. You can either use environment variables:

**Windows (PowerShell):**
```powershell
$env:DEADLINER_MOODLE_URL="https://moodle.example.com"
$env:DEADLINER_MOODLE_TOKEN="your_moodle_token_here"
$env:DEADLINER_GOOGLE_TOKEN="your_google_access_token_here" # Optional
```

**Linux / macOS:**
```bash
export DEADLINER_MOODLE_URL="https://moodle.example.com"
export DEADLINER_MOODLE_TOKEN="your_moodle_token_here"
export DEADLINER_GOOGLE_TOKEN="your_google_access_token_here" # Optional
```

Or, alternatively, create a `~/.deadliner.json` file in your home directory:
```json
{
  "moodle_base_url": "https://moodle.example.com",
  "moodle_token": "your_moodle_token_here",
  "google_access_token": "your_google_access_token_here"
}
```

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
