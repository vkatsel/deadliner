# Deadliner — Privacy Policy

**Effective Date:** September 18, 2026  
**Application Name:** Deadliner  
**Maintainer:** Vladyslav Katsel ([vkatsel@kse.org.ua](mailto:vkatsel@kse.org.ua))  
**Repository:** [https://github.com/vkatsel/deadliner](https://github.com/vkatsel/deadliner)  

---

## Google API Services User Data Policy Compliance

> **Deadliner's use and transfer to any other app of information received from Google APIs will adhere to the [Google API Services User Data Policy](https://developers.google.com/terms/api-services-user-data-policy), including the Limited Use requirements.**

Deadliner does **not** sell Google user data, does **not** transfer user data to third parties, does **not** use Google user data for advertising, and does **not** use user data to train generalized artificial intelligence or machine learning models.

---

## 1. Introduction & Overview

**Deadliner** is an open-source, local-first academic command-line interface (CLI) tool designed for university students, educators, and researchers. Deadliner aggregates assignments, coursework due dates, and university schedules from institutional portals (such as Moodle and KSE Schedule) and Google Classroom, synchronizing them directly into your personal Google Calendar.

Deadliner operates on a **Local-First & Zero-Knowledge** architectural model:
- **No Remote Servers:** Deadliner does not own, operate, or communicate with any cloud server, telemetry endpoint, analytics backend, or remote database.
- **Direct Client-to-API Communication:** All network requests travel directly from your local terminal to the official APIs (Google APIs, Moodle, KSE Schedule).
- **Zero Third-Party Telemetry:** We collect no usage metrics, crash telemetry, diagnostic logs, or behavioral analytics.

---

## 2. Google OAuth Scopes & Data Access

Deadliner requests only the minimal necessary OAuth 2.0 scopes from Google to perform calendar synchronization and Google Classroom coursework retrieval:

| Scope | Permission Level | Exact Purpose & Usage |
|---|---|---|
| `https://www.googleapis.com/auth/calendar.events` | Read / Write Events | Strictly used to create, update, and delete academic deadline reminders and university class schedules on your primary Google Calendar. Deadliner marks its events with a deterministic private extended property (`deadliner_id`). **Deadliner never reads, modifies, or deletes your personal, non-Deadliner calendar events.** |
| `https://www.googleapis.com/auth/classroom.courses.readonly` | Read-Only | Used to list the active academic courses in which you are enrolled as a student, so that Deadliner can inspect them for upcoming coursework. |
| `https://www.googleapis.com/auth/classroom.coursework.me.readonly` | Read-Only | Used to retrieve your personal course assignments, coursework details, and due dates from Google Classroom. |
| `https://www.googleapis.com/auth/classroom.coursework.students.readonly` | Read-Only | Used to read coursework metadata and submission deadlines across enrolled student classes. |

---

## 3. Credential Storage & Security

All configuration and credential tokens are stored exclusively on your local workstation in your user home directory:

- **`~/.deadliner_google_token.json`**: Contains your Google OAuth2 access and refresh tokens returned directly by Google's OAuth consent server. This allows your local CLI to execute scheduled synchronizations without re-prompting you on every run.
- **`~/.deadliner.json`**: Contains your configured Moodle URL, Moodle API token, and KSE Schedule session token.

These files are stored strictly on your local disk and are protected by your operating system's user permission model. They are never sent to external servers or accessible to the developers.

---

## 4. Data Retention, Revocation & Deletion

Because Deadliner maintains no remote database, we retain zero data about you on our end. You retain full control over your data:

### Deleting Local Data
You can permanently delete all stored credentials and configuration files by removing the local files:

```bash
# macOS / Linux
rm ~/.deadliner.json ~/.deadliner_google_token.json

# Windows (PowerShell)
Remove-Item "$HOME\.deadliner.json", "$HOME\.deadliner_google_token.json" -ErrorAction SilentlyContinue
```

### Revoking Google Account Permissions
You can revoke Deadliner's authorization at any time via your Google Account Security settings:
1. Navigate to [Google Account Permissions](https://myaccount.google.com/permissions).
2. Select **Deadliner** under *Third-party apps with account access*.
3. Click **Remove Access**. Google immediately revokes all tokens.

---

## 5. Third-Party Services

Deadliner communicates with external services on your behalf via official APIs:
- **Google LLC:** Google Calendar API and Google Classroom API ([Google Privacy Policy](https://policies.google.com/privacy)).
- **Kyiv School of Economics (KSE):** Moodle LMS ([teaching.kse.org.ua](https://teaching.kse.org.ua)) and KSE Schedule ([schedule.kse.ua](https://schedule.kse.ua)).

---

## 6. Children's & Educational Privacy

Deadliner is intended for university students, educators, and adult learners. We do not knowingly solicit or collect information from individuals under the age of 13.

---

## 7. Contact Information

For any questions or compliance inquiries regarding Deadliner, please contact:

- **Maintainer:** Vladyslav Katsel
- **Institution:** Kyiv School of Economics (KSE)
- **Email:** [vkatsel@kse.org.ua](mailto:vkatsel@kse.org.ua)
- **Repository:** [https://github.com/CS460-SEP-2026/greenfield](https://github.com/CS460-SEP-2026/greenfield)
