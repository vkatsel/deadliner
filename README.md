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
*(This opens a browser for you to grant permission)*

### 3. Fetch Deadlines

Fetch and display your upcoming deadlines from all configured platforms:

**Windows (PowerShell):**
```powershell
$env:PYTHONPATH="src"; python -m deadliner fetch
```

**Linux / macOS:**
```bash
PYTHONPATH=src python -m deadliner fetch
```

### 4. Sync to Google Calendar

Push all upcoming deadlines to your Google Calendar as 15-minute events:

**Windows (PowerShell):**
```powershell
$env:PYTHONPATH="src"; python -m deadliner sync
```

**Linux / macOS:**
```bash
PYTHONPATH=src python -m deadliner sync
```

### 5. Run Tests

Run the full test suite with one command:
```bash
pytest -v tests/
```
