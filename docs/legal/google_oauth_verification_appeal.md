# Google OAuth App Verification Request & Justification Letter

**To:** Google Trust & Safety / OAuth Application Verification Team  
**Subject:** OAuth App Verification Appeal & Scope Justification — Deadliner (`vkatsel.github.io`)  
**Applicant:** Vadym Katsel (`vkatsel@kse.org.ua`)  
**Project:** Deadliner — Academic Hub & Calendar Sync  
**Application URL:** [https://vkatsel.github.io/deadliner/](https://vkatsel.github.io/deadliner/)  
**GitHub Repository:** [https://github.com/vkatsel/deadliner](https://github.com/vkatsel/deadliner)  
**Privacy Policy:** [https://vkatsel.github.io/deadliner/privacy.html](https://vkatsel.github.io/deadliner/privacy.html)  
**Terms of Service:** [https://vkatsel.github.io/deadliner/terms.html](https://vkatsel.github.io/deadliner/terms.html)  

---

## 1. Executive Summary & Student Project Context

Dear Google Trust & Safety Team,

My name is Vadym Katsel. I am an undergraduate Software Engineering student at the **Kyiv School of Economics (KSE)** in Ukraine. 

I am submitting this appeal regarding the OAuth verification of **Deadliner**, an open-source, non-commercial student utility developed to solve a widespread problem in our university community: fragmented academic deadlines spread across university Moodle portals and Google Classroom courses.

Deadliner is an educational pet-project created by students, for students. It has **zero commercial intent**, **no monetization**, and operates under the permissive **MIT License**.

---

## 2. Authorized Domain & GitHub Pages (`github.io`) Context

During automated verification in Google Cloud Console, domain verification for `github.io` is often flagged because individual repository owners cannot add global DNS TXT records to GitHub’s shared root domain (`github.io`).

We kindly request verification approval based on the following:
1. **Repository Ownership:** The official project documentation and legal privacy policies are hosted directly via GitHub Pages at `https://vkatsel.github.io/deadliner/`, which is directly bound to the verified GitHub account `vkatsel` and open-source repository `https://github.com/vkatsel/deadliner`.
2. **HTML Verification Tag:** We have embedded the Google Site Verification meta tag directly in the `<head>` of our application landing page:
   ```html
   <meta name="google-site-verification" content="aEbnSVAT5-mh2hJIc8EtZsvRGz0whY2GfawaGZKs8vk" />
   ```
3. **Institutional Affiliation:** The project developer email (`vkatsel@kse.org.ua`) is an official institutional Google Workspace account issued by Kyiv School of Economics.

---

## 3. Local-First & Zero-Knowledge Architecture

Deadliner was designed with strict privacy principles to ensure that student data is never compromised:

- **100% Client-Side:** Deadliner runs entirely as a local open-source Python CLI on the student's personal computer.
- **Zero Remote Servers & Databases:** There is **no Deadliner backend server, proxy, cloud database, or telemetry service**.
- **Local Storage:** All authentication tokens (Google OAuth refresh tokens, Moodle tokens, KSE tokens) are stored strictly locally in the user's home directory (`~/.deadliner.json`).
- **Direct Communication:** Data flows directly and exclusively between the student's local machine and official Google/university APIs over HTTPS.

---

## 4. Scope-by-Scope Justification

Deadliner requests only the minimal necessary permissions strictly required to provide its academic reminder functionality:

### A. `https://www.googleapis.com/auth/calendar.events` (Sensitive)
- **Why it is needed:** To create, update, and remove deadline reminders in the student's personal Google Calendar.
- **How it is used:**
  - Deadliner converts upcoming assignment deadlines into concise, 15-minute calendar events (tagged Tomato Red) pointing to the exact cutoff moment (e.g. 23:59).
  - Deadliner tags all managed events with a private metadata property (`extendedProperties.private.deadliner_id`).
  - **Deadliner NEVER reads, modifies, or deletes the user's personal calendar events.** It only interacts with events created by Deadliner itself.
  - When an assignment due date is updated or cancelled by a professor, Deadliner updates or prunes only that specific event.

### B. `https://www.googleapis.com/auth/classroom.coursework.me.readonly` (Sensitive)
- **Why it is needed:** To read the student's active coursework assignments, descriptions, and submission due dates.
- **How it is used:** Deadliner fetches assignment titles, course titles, and due timestamps so they can be transformed into calendar events. It has read-only access and cannot alter any coursework.

### C. `https://www.googleapis.com/auth/classroom.courses.readonly` (Non-sensitive)
- **Why it is needed:** To look up course names and short codes corresponding to enrolled student classes.
- **How it is used:** Prefixes event summaries with friendly course titles (e.g., `[Linear Algebra] Homework 3`).

---

## 5. Google API Services User Data Policy Certification

We explicitly certify that:
1. Deadliner complies fully with the **Google API Services User Data Policy**, including the **Limited Use** requirements.
2. User data obtained through Google APIs is **never sold, leased, or transferred** to any third parties, advertisers, or data brokers.
3. User data is **never used to train machine learning or artificial intelligence models**.
4. Human review of user data does not occur, as no user data is ever transmitted to the developer or any external server.

---

## 6. Demonstration Video & Walkthrough

A demonstration video showcasing the complete OAuth consent flow, client ID visibility in the URL address bar, and end-to-end functionality is available at:

- **Demo Video URL (YouTube):** `[INSERT UNLISTED YOUTUBE DEMO LINK HERE]`
- **Video Timestamp Breakdown:**
  - `00:00 - 00:30`: Project introduction and terminal command launch (`deadliner login google`).
  - `00:30 - 01:10`: Display of the OAuth consent screen with visible Client ID in the browser URL bar.
  - `01:10 - 01:45`: Granting calendar and classroom permissions.
  - `01:45 - 02:30`: Execution of `deadliner sync`, displaying newly created red deadline events in Google Calendar and private event property isolation.

---

## 7. Contact Information

If the review team requires any further clarifications, code audits, or adjustments, please contact:

- **Developer / Student Maintainer:** Vadym Katsel  
- **Email:** `vkatsel@kse.org.ua`  
- **Alternative Email:** `vadymkatsel@gmail.com`  
- **Institution:** Kyiv School of Economics, Kyiv, Ukraine  
- **Repository:** `https://github.com/vkatsel/deadliner`  

Thank you for your time, consideration, and support for student-driven open-source innovation!

Sincerely,  
**Vadym Katsel**  
*Student & Maintainer of Deadliner*
