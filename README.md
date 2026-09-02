# Deadliner

Deadliner is a CLI tool that fetches upcoming assignments from your Moodle and Google Classroom courses and displays them in your local timezone, sorted by deadline. You can also sync these deadlines directly to your Google Calendar.

## Quickstart (Under 5 minutes)

### 1. Installation

Clone the repository and install dependencies (requires Python 3.12+):

```bash
git clone https://github.com/CS460-SEP-2026/greenfield.git
cd greenfield
python -m pip install -r requirements.txt
```

### 2. Configuration & Login

**Log in to Moodle:**
```bash
PYTHONPATH=src python -m deadliner login moodle
```
*(This will ask for your Moodle URL, username, and password, and safely save your API token to `~/.deadliner.json`)*

**Log in to Google (Classroom & Calendar):**
Because this app is entirely local, you must provide your own Google Cloud credentials:
1. Create a project in the [Google Cloud Console](https://console.cloud.google.com/).
2. Enable both the **Google Classroom API** and the **Google Calendar API**.
3. Create an OAuth Client ID (Type: Desktop App) and download the `client_secret.json` file.
4. Place `client_secret.json` in the root of this project.

Then, run:
```bash
PYTHONPATH=src python -m deadliner login google
```
**Log in to KSE Schedule:**
```bash
PYTHONPATH=src python -m deadliner login kse
```
*(Prompts for your KSE token from `schedule.kse.ua` and enables schedule syncing)*

### 3. Interactive Menu (Recommended)

Simply run Deadliner with no arguments (or `deadliner menu`) to open the interactive workflow interface:

```bash
PYTHONPATH=src python -m deadliner
```

### 4. Fetch Deadlines & KSE Schedule

**Fetch Assignments:**
```bash
PYTHONPATH=src python -m deadliner fetch
```

**Fetch KSE Classes (Next 7 days by default):**
```bash
PYTHONPATH=src python -m deadliner schedule fetch
```

*(Optional: specify `--from 2026-09-01 --till 2026-09-08` or `--days 14`)*

### 5. Sync to Google Calendar

**Sync Deadlines (Red events):**
```bash
PYTHONPATH=src python -m deadliner sync
```

**Sync KSE Classes (Peacock blue events):**
```bash
PYTHONPATH=src python -m deadliner schedule sync
```

### 6. Run Tests

Run the full test suite with one command:
```bash
pytest -v tests/
```

