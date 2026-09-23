# Deadliner — Terms of Service

**Last Revised:** September 18, 2026  
**Application Name:** Deadliner  
**Maintainer:** Vladyslav Katsel ([vkatsel@kse.org.ua](mailto:vkatsel@kse.org.ua))  
**Repository:** [https://github.com/vkatsel/deadliner](https://github.com/vkatsel/deadliner)  

---

## Important Academic Disclaimer

> **Deadliner is an auxiliary productivity utility.** It is designed to assist students with deadline visibility and calendar synchronization, but it is **not** an official academic grading or scheduling system.
> 
> You remain solely responsible for verifying all course assignments, syllabus requirements, and examination schedules on your official university portals (e.g. Moodle and Google Classroom). In no event shall Deadliner or its contributors be held liable for missed submissions, schedule discrepancies, or academic penalties.

---

## 1. Acceptance of Terms

By installing, configuring, running, or accessing the Deadliner software ("Deadliner", "the Software"), you agree to be bound by these Terms of Service. If you do not agree, do not install or use the application.

---

## 2. Description of the Software

Deadliner is an open-source, local-first command-line tool developed to help students manage academic deadlines and class timetables. Deadliner connects directly to university LMS endpoints (Moodle), university schedule APIs (KSE Schedule), and Google Classroom, providing terminal displays and automated Google Calendar synchronization.

Deadliner executes entirely on your personal machine and does not offer or operate any cloud backend or hosted services.

---

## 3. Open-Source License (MIT)

Deadliner is licensed under the terms of the **MIT License**:

```
Copyright (c) 2026 Deadliner Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 4. User Responsibilities & Acceptable Use

By using Deadliner, you agree to:
1. **Safeguard Local Tokens:** Maintain appropriate file security for local configuration files (`~/.deadliner.json` and `~/.deadliner_google_token.json`).
2. **Institutional Compliance:** Comply with your academic institution's Acceptable Use Policy, Code of Conduct, and academic integrity regulations.
3. **No Abusive Polling:** Do not configure automated synchronization or background jobs in a manner that creates abusive traffic, denial-of-service, or rate limit exhaustion against institutional or Google servers.
4. **Lawful Purpose:** Refrain from using Deadliner to scrape or distribute data in violation of third-party terms or privacy rights.

---

## 5. Third-Party Services & API Changes

Deadliner interfaces with third-party APIs (Google LLC, Kyiv School of Economics). These external services may modify their endpoints, rate limits, authentication flows, or service availability at any time. The maintainers do not guarantee continuous or uninterrupted operation of third-party integrations.

---

## 6. Disclaimer of Warranties

THE SOFTWARE IS PROVIDED "AS IS" AND "AS AVAILABLE", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE, AND NON-INFRINGEMENT. THE ENTIRE RISK AS TO THE QUALITY, ACCURACY, AND PERFORMANCE OF THE SOFTWARE RESTS WITH THE USER.

---

## 7. Limitation of Liability

TO THE MAXIMUM EXTENT PERMITTED BY LAW, IN NO EVENT SHALL THE AUTHORS, COPYRIGHT HOLDERS, CONTRIBUTORS, OR AFFILIATED UNIVERSITIES BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY (INCLUDING DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES, INCLUDING LOSS OF DATA, MISSED DEADLINES, ACADEMIC PENALTIES, OR GRADE LOSS) ARISING OUT OF OR IN CONNECTION WITH THE USE OF OR INABILITY TO USE THE SOFTWARE.

---

## 8. Termination

You may terminate this agreement at any time by deleting the software and removing the local configuration files:
- `~/.deadliner.json`
- `~/.deadliner_google_token.json`

---

## 9. Contact Information

For questions regarding these Terms:
- **Maintainer:** Vladyslav Katsel
- **Email:** [vkatsel@kse.org.ua](mailto:vkatsel@kse.org.ua)
- **Institution:** Kyiv School of Economics (KSE)
- **Repository:** [https://github.com/vkatsel/deadliner](https://github.com/vkatsel/deadliner)
