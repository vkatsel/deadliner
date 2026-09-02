# Deadliner

Deadliner is an academic CLI hub that fetches upcoming assignments (Moodle, Google Classroom) and university class schedules (KSE Schedule) and displays them in your local timezone. You can also sync everything directly to your personal Google Calendar with automatic deduplication and color-coding.

---

## Quickstart

### 1. Installation

Clone the repository and install in editable mode (so `deadliner` is available anywhere in your terminal):

```bash
git clone https://github.com/CS460-SEP-2026/greenfield.git
cd greenfield
pip install -e .
```

---

### 2. Configuration & Login

**Log in to Moodle:**
```bash
deadliner login moodle
```
*(Prompts for your Moodle URL, username, and password, saving the token to `~/.deadliner.json`)*

**Log in to Google (Calendar & Classroom):**
1. Create a project in [Google Cloud Console](https://console.cloud.google.com/).
2. Enable **Google Calendar API** and **Google Classroom API**.
3. Create an OAuth Client ID (**Application Type: Desktop App**) and download `client_secret.json` into the root of this project.
4. Run:
```bash
deadliner login google
```

**Log in to KSE Schedule:**
```bash
deadliner login kse
```
*(Quick 1-step login using your browser session token from `schedule.kse.ua`. Token auto-refreshes seamlessly in the background!)*

---

### 3. Usage

#### Interactive Menu (Recommended)
Simply run `deadliner` with no arguments (or double-click `run_deadliner.bat` on Windows):
```bash
deadliner
```

#### Fetch Deadlines & Classes
- **Fetch Deadlines:**
  ```bash
  deadliner fetch
  ```
- **Fetch KSE Classes (Next 7 days):**
  ```bash
  deadliner schedule fetch
  ```
  *(Options: `--days 14`, `--from 2026-09-01 --till 2026-09-10`)*

#### Sync to Google Calendar
- **Sync Deadlines (Tomato Red):**
  ```bash
  deadliner sync
  ```
- **Sync KSE Classes (Autumn Orange):**
  ```bash
  deadliner schedule sync
  ```

---

### 4. Run Tests

Run the full test suite with one command:
```bash
pytest -v tests/
```


