/* Deadliner Desktop Workspace Controller (EN / UA Bilingual + PyWebView Bridge) */

(function () {
  "use strict";

  const I18N = {
    en: {
      brand_sub: "Academic Workspace",
      status_ready: "Ready",
      status_fetching: "Fetching data...",
      status_syncing: "Syncing calendar...",
      status_working: "Working...",
      btn_refresh_all: "Refresh Data",
      btn_sync_all: "Sync All to Calendar",
      btn_dismiss: "Dismiss",
      btn_go_connections: "Open Connections →",
      nav_group_workspace: "Workspace",
      nav_deadlines: "Deadlines",
      nav_schedule: "KSE Schedule",
      nav_analytics: "Analytics & DB",
      nav_group_system: "System",
      nav_sync: "Sync & Logs",
      nav_connections: "Connections",
      legend_title: "Color Semantics",
      legend_deadline: "Deadline / Cutoff",
      legend_lecture: "Lecture / Submitted",
      legend_practice: "Practice / Seminar",
      deadlines_heading: "Academic Deadlines & Submissions",
      deadlines_subheading: "Aggregated coursework from Moodle and Google Classroom",
      btn_fetch_deadlines: "Fetch Deadlines",
      btn_sync_deadlines: "Sync Deadlines",
      kpi_pending: "Pending Deadlines",
      kpi_pending_sub: "Active unsubmitted tasks",
      kpi_critical: "Due within 24h / Overdue",
      kpi_critical_sub: "High-priority cutoffs",
      kpi_submitted: "Submitted",
      kpi_submitted_sub: "Verified via Moodle & Classroom",
      kpi_classes: "Upcoming Classes",
      filter_all: "All",
      filter_pending: "Pending",
      filter_critical: "Critical (<24h)",
      filter_midnight: "Midnight (00:00)",
      filter_submitted: "Submitted",
      search_placeholder: "Search by course or title...",
      th_status: "Status",
      th_course: "Course",
      th_assignment: "Assignment",
      th_due: "Due Date",
      th_remaining: "Remaining",
      th_link: "Portal",
      schedule_heading: "KSE University Class Schedule",
      schedule_subheading: "Live lectures, seminars, rooms, and shelter locations from schedule.kse.ua",
      btn_fetch_schedule: "Fetch Schedule",
      btn_sync_schedule: "Sync Schedule",
      filter_all_classes: "All Classes",
      filter_lectures: "Lectures",
      filter_practices: "Practices",
      schedule_search_placeholder: "Search by course, room, or teacher...",
      analytics_heading: "Workload Overview & Local Storage Architecture",
      analytics_subheading: "Session metrics and extensible repository interface",
      analytics_course_load: "Course Load Breakdown",
      analytics_session_metrics: "Session Snapshot",
      stat_completion_rate: "Completion Ratio",
      stat_completion_sub: "Submitted vs Total",
      stat_sync_runs: "Session Sync Runs",
      analytics_privacy_note:
        "All metrics are computed locally in memory via the DataStore repository protocol (src/deadliner/storage.py). No external analytics or remote servers are contacted.",
      blueprint_title: "Local SQLite Persistence & Velocity Engine (~/.deadliner/cache.db)",
      blueprint_desc:
        "The current MVP runs statelessly in memory. The repository contract is ready so plugging in SQLiteStore will unlock historical tracking below without changing UI or CLI logic:",
      bp_slot_1: "Tracks average hours before deadline cutoff each assignment is turned in across the trimester.",
      bp_slot_2: "Relational audit log of professor deadline changes (old due date ➜ new due date) and room updates.",
      bp_slot_3: "0 ms startup rendering when offline or during university portal maintenance windows.",
      sync_heading: "Synchronization & Execution Logs",
      sync_subheading: "Google Calendar reconciliation and daily background scheduler",
      cron_card_title: "Daily 24h Background Auto-Sync",
      cron_card_desc:
        "Runs silently in the background via Windows Task Scheduler (pythonw.exe) or UNIX crontab every day at your chosen time.",
      cron_time_label: "Daily run time (24h HH:MM)",
      btn_enable_cron: "Enable / Update",
      btn_disable_cron: "Disable",
      sync_diff_title: "Last Sync Report",
      sync_report_empty:
        'No calendar sync executed in this session yet. Click "Sync All to Calendar" to reconcile events.',
      btn_refresh_logs: "Refresh Logs",
      conn_heading: "Service Connections & Configuration",
      conn_subheading: "Credentials are stored strictly locally on your machine in ~/.deadliner.json",
      moodle_user_label: "Username or KSE Email",
      moodle_pass_label: "Moodle Password (local password, not Google SSO)",
      btn_connect_moodle: "Authenticate & Save",
      google_card_desc:
        "Used to create color-coded Google Calendar events and fetch Google Classroom coursework.",
      classroom_toggle_label: "Fetch Google Classroom Deadlines",
      google_secrets_label: "Optional: Paste client_secret.json content",
      btn_google_guide: "Open Setup Guide",
      btn_connect_google: "Sign in with Google",
      kse_card_desc:
        "Sign in via the native WebView window with automatic token refresh, or paste a token payload below.",
      btn_kse_webview: "Sign in via KSE WebView",
      btn_kse_clean: "Fresh Session (--clean)",
      kse_paste_label: "Fallback: Paste KSE JWT token or JSON",
      btn_save_kse_token: "Verify & Save Token",
      sys_card_title: "4. Local Environment & System PATH",
      sys_config_file: "Local configuration file",
      sys_storage_layer: "Storage repository layer",
      btn_configure_path: "Add Deadliner to System PATH",
      empty_deadlines: "No matching deadlines in the current view.",
      empty_schedule: "No KSE classes found for the selected filter and range.",
      tag_submitted: "✓ Submitted",
      tag_overdue: "Overdue",
      tag_critical: "Urgent (<24h)",
      tag_soon: "Due soon",
      tag_upcoming: "Upcoming",
      tag_midnight: "00:00 Cutoff",
      tag_shifted: "Rescheduled",
      open_link: "Open ↗",
      room_prefix: "Room",
      shelter_prefix: "Shelter",
      subgroup_prefix: "Group",
      period_prefix: "Period",
      classes_count_suffix: "classes",
    },
    ua: {
      brand_sub: "Академічний простір",
      status_ready: "Готово",
      status_fetching: "Оновлення даних...",
      status_syncing: "Синхронізація календаря...",
      status_working: "Виконання...",
      btn_refresh_all: "Оновити дані",
      btn_sync_all: "Синхронізувати все",
      btn_dismiss: "Закрити",
      btn_go_connections: "Перейти до підключень →",
      nav_group_workspace: "Робочий простір",
      nav_deadlines: "Дедлайни",
      nav_schedule: "Розклад KSE",
      nav_analytics: "Аналітика та БД",
      nav_group_system: "Система",
      nav_sync: "Синхронізація і логи",
      nav_connections: "Підключення",
      legend_title: "Кольорова семантика",
      legend_deadline: "Дедлайн / Опівніч",
      legend_lecture: "Лекція / Здано",
      legend_practice: "Практика / Семінар",
      deadlines_heading: "Академічні дедлайни та здачі",
      deadlines_subheading: "Зведені завдання з Moodle та Google Classroom",
      btn_fetch_deadlines: "Оновити дедлайни",
      btn_sync_deadlines: "Синхр. дедлайни",
      kpi_pending: "Активні дедлайни",
      kpi_pending_sub: "Нездані завдання з курсів",
      kpi_critical: "Менше 24 год / Прострочені",
      kpi_critical_sub: "Потребують першочергової уваги",
      kpi_submitted: "Здано",
      kpi_submitted_sub: "Перевірено через Moodle і Classroom",
      kpi_classes: "Заняття у розкладі",
      filter_all: "Усі",
      filter_pending: "Нездані",
      filter_critical: "Критичні (<24г)",
      filter_midnight: "Опівніч (00:00)",
      filter_submitted: "Здані",
      search_placeholder: "Пошук за курсом або назвою...",
      th_status: "Статус",
      th_course: "Курс",
      th_assignment: "Завдання",
      th_due: "Дата здачі",
      th_remaining: "Залишилось",
      th_link: "Портал",
      schedule_heading: "Розклад занять університету KSE",
      schedule_subheading: "Актуальні лекції, практики, аудиторії та укриття з schedule.kse.ua",
      btn_fetch_schedule: "Оновити розклад",
      btn_sync_schedule: "Синхр. розклад",
      filter_all_classes: "Усі заняття",
      filter_lectures: "Лекції",
      filter_practices: "Практики",
      schedule_search_placeholder: "Пошук за дисципліною, ауд. або викладачем...",
      analytics_heading: "Огляд навантаження та архітектура локальної БД",
      analytics_subheading: "Метрики поточної сесії та розширюваний інтерфейс збереження",
      analytics_course_load: "Навантаження по курсах",
      analytics_session_metrics: "Зріз поточної сесії",
      stat_completion_rate: "Частка виконаних",
      stat_completion_sub: "Здані проти всіх завдань",
      stat_sync_runs: "Синхронізацій за сесію",
      analytics_privacy_note:
        "Усі метрики обчислюються локально в оперативній пам'яті через протокол DataStore (src/deadliner/storage.py). Жодної зовнішньої телеметрії чи віддалених серверів.",
      blueprint_title: "Локальна історична БД SQLite та аналіз динаміки (~/.deadliner/cache.db)",
      blueprint_desc:
        "Поточний MVP працює в оперативній пам'яті. Контракт репозиторію вже готовий, тому підключення SQLiteStore відкриє історичну статистику без змін у коді інтерфейсу:",
      bp_slot_1: "Відстежує, за скільки годин до дедлайну в середньому здаються роботи протягом триместру.",
      bp_slot_2: "Історія перенесень дедлайнів викладачами (стара дата ➜ нова дата) та змін аудиторій.",
      bp_slot_3: "Миттєвий запуск (0 мс) без інтернету або під час технічних робіт на порталах.",
      sync_heading: "Синхронізація та системні логи",
      sync_subheading: "Звірка подій з Google Calendar та щоденний фоновий планувальник",
      cron_card_title: "Щоденна фонова авто-синхронізація (24г)",
      cron_card_desc:
        "Виконується без вікон у фоні через Планувальник завдань Windows (pythonw.exe) або UNIX crontab щодня у вибраний час.",
      cron_time_label: "Час щоденного запуску (24г ГГ:ХХ)",
      btn_enable_cron: "Увімкнути / Оновити",
      btn_disable_cron: "Вимкнути",
      sync_diff_title: "Звіт останньої синхронізації",
      sync_report_empty:
        "У цій сесії синхронізація ще не запускалась. Натисніть «Синхронізувати все».",
      btn_refresh_logs: "Оновити логи",
      conn_heading: "Підключення сервісів та налаштування",
      conn_subheading: "Токени зберігаються виключно локально на вашому комп'ютері у ~/.deadliner.json",
      moodle_user_label: "Логін або KSE Email",
      moodle_pass_label: "Пароль Moodle (локальний пароль, не Google SSO)",
      btn_connect_moodle: "Авторизувати та зберегти",
      google_card_desc:
        "Використовується для створення кольорових подій у Google Calendar та отримання дедлайнів Google Classroom.",
      classroom_toggle_label: "Підтягувати дедлайни з Google Classroom",
      google_secrets_label: "Опційно: вставте вміст client_secret.json",
      btn_google_guide: "Відкрити інструкцію",
      btn_connect_google: "Увійти через Google",
      kse_card_desc:
        "Вхід через нативне WebView-вікно з автооновленням токена або пряма вставка токена нижче.",
      btn_kse_webview: "Увійти через KSE WebView",
      btn_kse_clean: "Чиста сесія (--clean)",
      kse_paste_label: "Резервний метод: вставте JWT токен або JSON",
      btn_save_kse_token: "Перевірити та зберегти",
      sys_card_title: "4. Локальне середовище та системний PATH",
      sys_config_file: "Локальний файл конфігурації",
      sys_storage_layer: "Шар зберігання даних",
      btn_configure_path: "Додати Deadliner у системний PATH",
      empty_deadlines: "Немає дедлайнів для вибраного фільтра.",
      empty_schedule: "Занять KSE за вибраним фільтром та періодом не знайдено.",
      tag_submitted: "✓ Здано",
      tag_overdue: "Прострочено",
      tag_critical: "Критично (<24г)",
      tag_soon: "Скоро",
      tag_upcoming: "Активно",
      tag_midnight: "00:00 Опівніч",
      tag_shifted: "Перенесено",
      open_link: "Відкрити ↗",
      room_prefix: "Ауд.",
      shelter_prefix: "Укриття",
      subgroup_prefix: "Група",
      period_prefix: "Пара",
      classes_count_suffix: "занять",
    },
  };

  const state = {
    lang: "en",
    activeView: "deadlines",
    deadlineFilter: "all",
    deadlineSearch: "",
    scheduleDays: 7,
    scheduleTypeFilter: "all",
    scheduleSearch: "",
    deadlines: [],
    schedule: [],
    analytics: {
      total_deadlines: 0,
      submitted_count: 0,
      pending_count: 0,
      urgent_24h_count: 0,
      overdue_count: 0,
      completion_rate: 0,
      total_classes: 0,
      lectures_count: 0,
      practices_count: 0,
      courses_breakdown: [],
      sync_runs_session: 0,
      last_sync_utc: null,
    },
    connections: {
      moodle: { connected: false, base_url: "https://teaching.kse.org.ua" },
      google: { connected: false, classroom_enabled: true },
      kse: { connected: false },
    },
    scheduler: { enabled: false, start_time: "08:00", next_run: "" },
    system: { on_path: false, config_path: "~/.deadliner.json" },
  };

  let bannerTimer = null;

  function t(key) {
    return (I18N[state.lang] && I18N[state.lang][key]) || I18N.en[key] || key;
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function getApi() {
    if (window.pywebview && window.pywebview.api) {
      return window.pywebview.api;
    }
    return null;
  }

  function setBusy(isBusy, labelKey) {
    const ind = document.getElementById("activityIndicator");
    const txt = document.getElementById("activityText");
    if (!ind || !txt) return;
    if (isBusy) {
      ind.classList.add("busy");
      txt.textContent = t(labelKey || "status_working");
    } else {
      ind.classList.remove("busy");
      txt.textContent = t("status_ready");
    }
  }

  function clearFieldValidation() {
    document.querySelectorAll(".input-invalid").forEach((el) => {
      el.classList.remove("input-invalid");
    });
  }

  function markFieldInvalid(fieldId) {
    if (!fieldId) return;
    const el = document.getElementById(fieldId);
    if (!el) return;
    el.classList.remove("input-invalid");
    // Force reflow to replay shake animation
    void el.offsetWidth;
    el.classList.add("input-invalid");
    el.focus();
  }

  function showBanner(message, level, options) {
    const opts = options || {};
    const box = document.getElementById("globalBanner");
    const titleEl = document.getElementById("globalBannerTitle");
    const hintEl = document.getElementById("globalBannerHint");
    const actionBtn = document.getElementById("btnBannerAction");
    if (!box || !titleEl || !hintEl || !actionBtn) return;

    if (bannerTimer) {
      clearTimeout(bannerTimer);
      bannerTimer = null;
    }

    box.className = "banner-box show " + (level || "info");
    titleEl.textContent = message || "";
    hintEl.textContent = opts.hint || "";
    hintEl.style.display = opts.hint ? "block" : "none";

    if (opts.actionView) {
      actionBtn.style.display = "inline-flex";
      actionBtn.textContent = t("btn_go_connections");
      actionBtn.onclick = () => {
        switchView(opts.actionView);
        hideBanner();
      };
    } else {
      actionBtn.style.display = "none";
      actionBtn.onclick = null;
    }

    if (opts.field) {
      markFieldInvalid(opts.field);
    }

    if (level === "success") {
      bannerTimer = setTimeout(() => {
        hideBanner();
      }, 6000);
    }
  }

  function showApiError(res, fallbackMsg) {
    if (!res) {
      showBanner(fallbackMsg || "Operation failed.", "error");
      return;
    }
    showBanner(res.error || fallbackMsg || "Operation failed.", "error", {
      hint: res.hint || "",
      actionView: res.action_view || null,
      field: res.field || null,
    });
  }

  function hideBanner() {
    const box = document.getElementById("globalBanner");
    if (box) box.className = "banner-box";
  }

  function applyLanguage(lang) {
    state.lang = lang === "ua" ? "ua" : "en";
    document.querySelectorAll(".lang-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-lang") === state.lang);
    });
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (key) el.textContent = t(key);
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      if (key) el.setAttribute("placeholder", t(key));
    });
    renderAll();
  }

  function switchView(viewName) {
    state.activeView = viewName;
    document.querySelectorAll(".nav-item[data-view]").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-view") === viewName);
    });
    document.querySelectorAll(".view-pane").forEach((pane) => {
      pane.classList.toggle("active", pane.id === "view-" + viewName);
    });
    if (viewName === "sync") {
      refreshLogs();
    }
  }

  function renderStatusAndConnections() {
    const mConn = !!(state.connections.moodle && state.connections.moodle.connected);
    const gConn = !!(state.connections.google && state.connections.google.connected);
    const kConn = !!(state.connections.kse && state.connections.kse.connected);
    const connectedCount = (mConn ? 1 : 0) + (gConn ? 1 : 0) + (kConn ? 1 : 0);

    const navConn = document.getElementById("navConnCount");
    if (navConn) navConn.textContent = connectedCount + "/3";

    const onlineLabel = state.lang === "ua" ? "Підключено" : "Connected";
    const offlineLabel = state.lang === "ua" ? "Не підключено" : "Disconnected";

    const setSb = (dotId, textId, badgeId, isOnline) => {
      const d = document.getElementById(dotId);
      const tx = document.getElementById(textId);
      const b = document.getElementById(badgeId);
      if (d) d.className = "dot " + (isOnline ? "dot-sage" : "dot-muted");
      if (tx) tx.textContent = isOnline ? onlineLabel : offlineLabel;
      if (b) {
        b.className = "tag " + (isOnline ? "tag-sage" : "");
        b.textContent = isOnline ? onlineLabel : offlineLabel;
      }
    };

    setSb("sbDotMoodle", "sbTextMoodle", "connMoodleBadge", mConn);
    setSb("sbDotGoogle", "sbTextGoogle", "connGoogleBadge", gConn);
    setSb("sbDotKse", "sbTextKse", "connKseBadge", kConn);

    const moodleUrlInput = document.getElementById("moodleUrlInput");
    if (moodleUrlInput && state.connections.moodle && state.connections.moodle.base_url) {
      if (!moodleUrlInput.dataset.dirty) {
        moodleUrlInput.value = state.connections.moodle.base_url;
      }
    }

    const crBtn = document.getElementById("btnToggleClassroom");
    const crEnabled = !!(state.connections.google && state.connections.google.classroom_enabled);
    if (crBtn) {
      crBtn.textContent =
        state.lang === "ua"
          ? crEnabled
            ? "Увімкнено"
            : "Вимкнено"
          : crEnabled
          ? "Enabled"
          : "Disabled";
      crBtn.className = "btn " + (crEnabled ? "btn-sage" : "");
    }

    // Scheduler
    const cronEnabled = !!(state.scheduler && state.scheduler.enabled);
    const cronTime = (state.scheduler && state.scheduler.start_time) || "08:00";
    const navCron = document.getElementById("navCronBadge");
    if (navCron) {
      navCron.textContent = cronEnabled ? cronTime : "Off";
    }
    const cronStatusTag = document.getElementById("cronStatusTag");
    if (cronStatusTag) {
      cronStatusTag.textContent = cronEnabled ? `Active @ ${cronTime}` : "Disabled";
      cronStatusTag.className = "tag " + (cronEnabled ? "tag-sage" : "");
    }
    const sbTextCron = document.getElementById("sbTextCron");
    if (sbTextCron) {
      sbTextCron.textContent = cronEnabled ? cronTime : "Off";
    }
    const cronNextRunText = document.getElementById("cronNextRunText");
    if (cronNextRunText) {
      cronNextRunText.textContent =
        (state.lang === "ua" ? "Наступний запуск: " : "Next scheduled run: ") +
        ((state.scheduler && state.scheduler.next_run) || "—");
    }

    // System PATH
    const pathBadge = document.getElementById("connPathBadge");
    if (pathBadge) {
      const onPath = !!(state.system && state.system.on_path);
      pathBadge.textContent = onPath
        ? state.lang === "ua"
          ? "У системному PATH"
          : "In System PATH"
        : state.lang === "ua"
        ? "Не у PATH"
        : "Not in PATH";
      pathBadge.className = "tag " + (onPath ? "tag-sage" : "tag-amber");
    }
    const sysCfg = document.getElementById("sysConfigPath");
    if (sysCfg && state.system && state.system.config_path) {
      sysCfg.textContent = state.system.config_path;
    }
  }

  function renderKpisAndAnalytics() {
    const a = state.analytics || {};
    const pending = a.pending_count || 0;
    const critical = (a.urgent_24h_count || 0) + (a.overdue_count || 0);
    const submitted = a.submitted_count || 0;
    const totalClasses = a.total_classes || 0;

    const setEl = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = String(val);
    };

    setEl("kpiPending", pending);
    setEl("kpiCritical", critical);
    setEl("kpiSubmitted", submitted);
    setEl("kpiClasses", totalClasses);

    const kpiClassesSub = document.getElementById("kpiClassesSub");
    if (kpiClassesSub) {
      kpiClassesSub.textContent =
        state.lang === "ua"
          ? `${a.lectures_count || 0} лекцій • ${a.practices_count || 0} практик`
          : `${a.lectures_count || 0} Lectures • ${a.practices_count || 0} Practices`;
    }

    const navDeadlines = document.getElementById("navCountDeadlines");
    if (navDeadlines) {
      navDeadlines.textContent = String(pending);
      navDeadlines.classList.toggle("alert", critical > 0);
    }
    setEl("navCountSchedule", totalClasses);

    // Analytics view
    const rate = a.completion_rate || 0;
    setEl(
      "analyticsCompletionBadge",
      state.lang === "ua" ? `${rate}% Виконано` : `${rate}% Completed`
    );
    setEl("statCompletionRate", rate + "%");
    setEl("statSyncRuns", a.sync_runs_session || 0);

    const listEl = document.getElementById("courseBreakdownList");
    if (listEl) {
      const courses = a.courses_breakdown || [];
      if (!courses.length) {
        listEl.innerHTML = `<div class="empty-state-code">${escapeHtml(t("empty_deadlines"))}</div>`;
      } else {
        listEl.innerHTML = courses
          .map((c) => {
            const tot = Math.max(1, c.total);
            const subPct = Math.round((c.submitted / tot) * 100);
            const pendPct = 100 - subPct;
            return `
              <div class="course-bar-item">
                <div class="course-bar-top">
                  <span>${escapeHtml(c.course)}</span>
                  <span class="tabular" style="color:var(--text-secondary);">${c.submitted}/${c.total} ✓ &bull; ${c.pending} pending</span>
                </div>
                <div class="course-bar-track">
                  <div class="course-bar-fill-submitted" style="width:${subPct}%"></div>
                  <div class="course-bar-fill-pending" style="width:${pendPct}%"></div>
                </div>
              </div>
            `;
          })
          .join("");
      }
    }
  }

  function renderDeadlinesTable() {
    const tbody = document.getElementById("deadlinesTableBody");
    if (!tbody) return;

    const query = (state.deadlineSearch || "").trim().toLowerCase();
    const filtered = state.deadlines.filter((item) => {
      if (state.deadlineFilter === "pending" && item.is_submitted) return false;
      if (
        state.deadlineFilter === "critical" &&
        (item.is_submitted || (item.urgency !== "critical" && item.urgency !== "overdue"))
      ) {
        return false;
      }
      if (state.deadlineFilter === "midnight" && !item.is_midnight_cutoff) return false;
      if (state.deadlineFilter === "submitted" && !item.is_submitted) return false;

      if (query) {
        const hay = `${item.course} ${item.title} ${item.platform}`.toLowerCase();
        if (!hay.includes(query)) return false;
      }
      return true;
    });

    if (!filtered.length) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6">
            <div class="empty-state">
              <span>${escapeHtml(t("empty_deadlines"))}</span>
            </div>
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = filtered
      .map((item, idx) => {
        let statusTag = "";
        if (item.is_submitted) {
          statusTag = `<span class="tag tag-sage"><span class="dot dot-sage"></span>${escapeHtml(t("tag_submitted"))}</span>`;
        } else if (item.urgency === "overdue") {
          statusTag = `<span class="tag tag-tomato"><span class="dot dot-tomato"></span>${escapeHtml(t("tag_overdue"))}</span>`;
        } else if (item.urgency === "critical") {
          statusTag = `<span class="tag tag-tomato"><span class="dot dot-tomato"></span>${escapeHtml(t("tag_critical"))}</span>`;
        } else if (item.urgency === "soon") {
          statusTag = `<span class="tag tag-amber"><span class="dot dot-amber"></span>${escapeHtml(t("tag_soon"))}</span>`;
        } else {
          statusTag = `<span class="tag"><span class="dot dot-tomato"></span>${escapeHtml(t("tag_upcoming"))}</span>`;
        }

        const midnightTag = item.is_midnight_cutoff
          ? ` <span class="tag tag-tomato" title="Midnight Cutoff (00:00)">${escapeHtml(t("tag_midnight"))}</span>`
          : "";

        const countdownStr = state.lang === "ua" ? item.countdown_ua : item.countdown_en;
        const countdownClass = item.is_submitted
          ? "color:var(--sage-bright);"
          : item.urgency === "overdue" || item.urgency === "critical"
          ? "color:var(--tomato-bright); font-weight:600;"
          : "";

        const portalBtn = item.url
          ? `<button type="button" class="link-btn" data-open-url="${escapeHtml(item.url)}">${escapeHtml(t("open_link"))}</button>`
          : `<span style="color:var(--text-muted);">—</span>`;

        const delayMs = Math.min(idx * 22, 220);

        return `
          <tr class="${item.is_submitted ? "row-submitted" : ""}" style="animation-delay:${delayMs}ms">
            <td>${statusTag}</td>
            <td>
              <span class="course-code selectable">${escapeHtml(item.course)}</span>
              <span class="platform-label">${escapeHtml(item.platform)}</span>
            </td>
            <td>
              <span class="item-title selectable">${escapeHtml(item.title)}</span>
              ${midnightTag}
            </td>
            <td class="tabular">${escapeHtml(item.due_day_str)} &bull; <strong class="mono">${escapeHtml(item.due_time_str)}</strong></td>
            <td class="mono" style="${countdownClass}">${escapeHtml(countdownStr)}</td>
            <td style="text-align:right;">${portalBtn}</td>
          </tr>
        `;
      })
      .join("");
  }

  function renderScheduleList() {
    const container = document.getElementById("scheduleContainer");
    if (!container) return;

    const query = (state.scheduleSearch || "").trim().toLowerCase();
    const filtered = state.schedule.filter((ev) => {
      if (state.scheduleTypeFilter !== "all" && ev.event_type !== state.scheduleTypeFilter) {
        return false;
      }
      if (query) {
        const hay = `${ev.discipline} ${ev.course_name} ${ev.room} ${ev.teacher}`.toLowerCase();
        if (!hay.includes(query)) return false;
      }
      return true;
    });

    if (!filtered.length) {
      container.innerHTML = `
        <div class="table-panel">
          <div class="empty-state">
            <span>${escapeHtml(t("empty_schedule"))}</span>
          </div>
        </div>
      `;
      return;
    }

    // Group by date
    const groups = new Map();
    for (const ev of filtered) {
      if (!groups.has(ev.date)) {
        groups.set(ev.date, { date: ev.date, header: ev.day_header_en, items: [] });
      }
      groups.get(ev.date).items.push(ev);
    }

    container.innerHTML = Array.from(groups.values())
      .map((grp, grpIdx) => {
        const rowsHtml = grp.items
          .map((ev) => {
            const badgeClass =
              ev.semantic_color === "sage"
                ? "tag-sage"
                : ev.semantic_color === "peacock"
                ? "tag-peacock"
                : "";
            const dotClass =
              ev.semantic_color === "sage"
                ? "dot-sage"
                : ev.semantic_color === "peacock"
                ? "dot-peacock"
                : "dot-muted";
            const typeLabel = state.lang === "ua" ? ev.type_label_ua : ev.type_label_en;

            const subgroupBadge =
              ev.subgroup !== null && ev.subgroup !== undefined
                ? `<span class="tag">${escapeHtml(t("subgroup_prefix"))} ${escapeHtml(ev.subgroup)}</span>`
                : "";
            const shiftedBadge = ev.is_shifted
              ? `<span class="tag tag-amber">${escapeHtml(t("tag_shifted"))}</span>`
              : "";

            const metaParts = [];
            if (ev.discipline) metaParts.push(`<span style="color:var(--peacock-bright); font-weight:500;">${escapeHtml(ev.discipline)}</span>`);
            if (ev.room) metaParts.push(`<span>${escapeHtml(t("room_prefix"))} <strong>${escapeHtml(ev.room)}</strong></span>`);
            if (ev.shelter) metaParts.push(`<span>${escapeHtml(t("shelter_prefix"))} <strong>${escapeHtml(ev.shelter)}</strong></span>`);
            if (ev.teacher) metaParts.push(`<span>${escapeHtml(ev.teacher)}</span>`);

            const actionBtn = ev.zoom_url
              ? `<button type="button" class="link-btn" data-open-url="${escapeHtml(ev.zoom_url)}">Zoom ↗</button>`
              : "";

            return `
              <div class="class-row">
                <div class="class-time-col">
                  <span class="class-time">${escapeHtml(ev.time_range)}</span>
                  <span class="class-period">${escapeHtml(t("period_prefix"))} ${escapeHtml(ev.period)}</span>
                </div>
                <div>
                  <span class="tag ${badgeClass}"><span class="dot ${dotClass}"></span>${escapeHtml(typeLabel)}</span>
                </div>
                <div class="class-main-col">
                  <div class="class-title-line">
                    <span class="item-title selectable">${escapeHtml(ev.course_name)}</span>
                    ${subgroupBadge}
                    ${shiftedBadge}
                  </div>
                  <div class="class-meta-line selectable">${metaParts.join(" &bull; ")}</div>
                </div>
                <div>${actionBtn}</div>
              </div>
            `;
          })
          .join("");

        const delayMs = Math.min(grpIdx * 35, 220);

        return `
          <div class="day-card" style="animation-delay:${delayMs}ms">
            <div class="day-card-header">
              <span>${escapeHtml(grp.header)}</span>
              <span class="day-card-count">${grp.items.length} ${escapeHtml(t("classes_count_suffix"))}</span>
            </div>
            <div>${rowsHtml}</div>
          </div>
        `;
      })
      .join("");
  }

  function renderAll() {
    renderStatusAndConnections();
    renderKpisAndAnalytics();
    renderDeadlinesTable();
    renderScheduleList();
  }

  function ingestStatePayload(payload) {
    if (!payload) return;
    if (payload.connections) state.connections = payload.connections;
    if (payload.scheduler) state.scheduler = payload.scheduler;
    if (payload.system) state.system = payload.system;
    if (Array.isArray(payload.deadlines)) state.deadlines = payload.deadlines;
    if (Array.isArray(payload.schedule)) state.schedule = payload.schedule;
    if (payload.analytics) state.analytics = payload.analytics;
    renderAll();
  }

  async function doFetchDeadlines(silentBanner) {
    const api = getApi();
    if (!api) return;
    setBusy(true, "status_fetching");
    try {
      const res = await api.fetch_deadlines();
      if (res.analytics) state.analytics = res.analytics;
      if (res.ok) {
        state.deadlines = res.deadlines || [];
        const sb = document.getElementById("sbLastUpdated");
        if (sb && res.fetched_at) sb.textContent = "Last fetch: " + res.fetched_at;
        if (res.warnings && res.warnings.length && !silentBanner) {
          showBanner(res.warnings.join(" | "), "warning", {
            hint: "Some sources could not be reached. Check your credentials in Connections if the issue persists.",
            actionView: "connections",
          });
        }
      } else if (!silentBanner) {
        showApiError(res, "Failed to fetch deadlines.");
      }
      renderAll();
    } catch (err) {
      if (!silentBanner) showBanner(String(err), "error");
    } finally {
      setBusy(false);
    }
  }

  async function doFetchSchedule(silentBanner) {
    const api = getApi();
    if (!api) return;
    setBusy(true, "status_fetching");
    try {
      const res = await api.fetch_schedule(state.scheduleDays);
      if (res.analytics) state.analytics = res.analytics;
      if (res.ok) {
        state.schedule = res.schedule || [];
        const sb = document.getElementById("sbLastUpdated");
        if (sb && res.fetched_at) sb.textContent = "Last fetch: " + res.fetched_at;
      } else if (!silentBanner) {
        showApiError(res, "Failed to fetch KSE schedule.");
      }
      renderAll();
    } catch (err) {
      if (!silentBanner) showBanner(String(err), "error");
    } finally {
      setBusy(false);
    }
  }

  async function doFetchAll(silentBanner) {
    await doFetchDeadlines(silentBanner);
    await doFetchSchedule(silentBanner);
  }

  function renderSyncReport(lines, syncedAt) {
    const cont = document.getElementById("syncReportContainer");
    const badge = document.getElementById("lastSyncTimeBadge");
    if (badge && syncedAt) badge.textContent = syncedAt;
    if (!cont) return;
    cont.innerHTML = lines
      .map((l) => `<div class="log-line ${escapeHtml(l.level || "")}">${escapeHtml(l.text)}</div>`)
      .join("");
  }

  async function doSyncDeadlines() {
    const api = getApi();
    if (!api) return;
    setBusy(true, "status_syncing");
    try {
      const res = await api.sync_deadlines();
      if (!res.ok) {
        showApiError(res, "Deadlines sync failed.");
        return;
      }
      if (res.deadlines) state.deadlines = res.deadlines;
      if (res.analytics) state.analytics = res.analytics;
      renderAll();

      const lines = [
        {
          level: "success",
          text: `[Deadlines Sync] Created: ${res.created} | Updated: ${res.updated} | Skipped: ${res.skipped}`,
        },
      ];
      (res.details || []).forEach((d) => {
        lines.push({
          level: d.status === "created" || d.status === "submitted" ? "success" : "info",
          text: `  [${d.status}] [${d.course}] ${d.title} (${d.due_local})`,
        });
      });
      renderSyncReport(lines, res.synced_at);
      showBanner(
        `Deadlines synced to Google Calendar (+${res.created} created, ~${res.updated} updated, =${res.skipped} up-to-date).`,
        "success"
      );
    } catch (err) {
      showBanner(String(err), "error");
    } finally {
      setBusy(false);
    }
  }

  async function doSyncSchedule() {
    const api = getApi();
    if (!api) return;
    setBusy(true, "status_syncing");
    try {
      const res = await api.sync_schedule(state.scheduleDays);
      if (!res.ok) {
        showApiError(res, "Schedule sync failed.");
        return;
      }
      if (res.schedule) state.schedule = res.schedule;
      if (res.analytics) state.analytics = res.analytics;
      renderAll();

      const lines = [
        {
          level: "success",
          text: `[KSE Schedule Sync] Created: ${res.created} | Updated: ${res.updated} | Skipped: ${res.skipped} | Removed: ${res.deleted || 0}`,
        },
      ];
      (res.details || []).forEach((d) => {
        lines.push({
          level: d.status === "deleted" ? "error" : d.status === "created" ? "success" : "info",
          text: `  [${d.status}] [${d.course}] ${d.title} (${d.time})`,
        });
      });
      renderSyncReport(lines, res.synced_at);
      showBanner(
        `KSE Schedule synced (+${res.created} created, ~${res.updated} updated, -${res.deleted || 0} removed).`,
        "success"
      );
    } catch (err) {
      showBanner(String(err), "error");
    } finally {
      setBusy(false);
    }
  }

  async function doSyncAll() {
    const api = getApi();
    if (!api) return;
    setBusy(true, "status_syncing");
    try {
      const res = await api.sync_all(state.scheduleDays);
      if (res.analytics) state.analytics = res.analytics;
      const d = res.deadlines_sync || {};
      const s = res.schedule_sync || {};
      if (Array.isArray(d.deadlines)) state.deadlines = d.deadlines;
      if (Array.isArray(s.schedule)) state.schedule = s.schedule;
      renderAll();

      const lines = [];
      if (d.ok) {
        lines.push({
          level: "success",
          text: `[Deadlines] +${d.created || 0} created, ~${d.updated || 0} updated, =${d.skipped || 0} skipped`,
        });
      } else if (d.error) {
        lines.push({ level: "error", text: `[Deadlines Error] ${d.error}` });
      }
      if (s.ok) {
        lines.push({
          level: "success",
          text: `[KSE Schedule] +${s.created || 0} created, ~${s.updated || 0} updated, -${s.deleted || 0} removed`,
        });
      } else if (s.error) {
        lines.push({ level: "error", text: `[KSE Schedule Error] ${s.error}` });
      }
      renderSyncReport(lines, d.synced_at || s.synced_at || "Now");
      await refreshLogs();

      if (res.ok) {
        showBanner("All deadlines and KSE classes synchronized to Google Calendar!", "success");
      } else {
        showApiError(res, d.error || s.error || "Sync completed with warnings/errors.");
      }
    } catch (err) {
      showBanner(String(err), "error");
    } finally {
      setBusy(false);
    }
  }

  async function refreshLogs() {
    const api = getApi();
    const viewer = document.getElementById("syncLogViewer");
    if (!api || !viewer) return;
    try {
      const res = await api.get_logs(50);
      const entries = res.entries || [];
      if (!entries.length) {
        viewer.innerHTML = `<div class="log-line">No sync logs recorded yet in ~/.deadliner/sync.log.</div>`;
      } else {
        viewer.innerHTML = entries
          .map((e) => `<div class="log-line ${escapeHtml(e.level)}">${escapeHtml(e.raw)}</div>`)
          .join("");
      }
    } catch (err) {
      viewer.innerHTML = `<div class="log-line error">${escapeHtml(String(err))}</div>`;
    }
  }

  function bindEvents() {
    // Clear validation styles on input
    document.querySelectorAll(".input-field, .textarea-field").forEach((el) => {
      el.addEventListener("input", () => el.classList.remove("input-invalid"));
    });

    // Language switcher
    document.querySelectorAll(".lang-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        applyLanguage(btn.getAttribute("data-lang"));
      });
    });

    // Sidebar navigation
    document.querySelectorAll(".nav-item[data-view]").forEach((btn) => {
      btn.addEventListener("click", () => {
        switchView(btn.getAttribute("data-view"));
      });
    });

    // Banner dismiss
    const closeBannerBtn = document.getElementById("btnCloseBanner");
    if (closeBannerBtn) closeBannerBtn.addEventListener("click", hideBanner);

    // Topbar actions
    document.getElementById("btnFetchAll")?.addEventListener("click", () => doFetchAll(false));
    document.getElementById("btnSyncAllTop")?.addEventListener("click", doSyncAll);
    document.getElementById("btnSyncAllPane")?.addEventListener("click", doSyncAll);

    // Deadlines controls
    document.getElementById("btnFetchDeadlines")?.addEventListener("click", () => doFetchDeadlines(false));
    document.getElementById("btnSyncDeadlines")?.addEventListener("click", doSyncDeadlines);

    document.querySelectorAll("#deadlineFilterGroup .seg-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll("#deadlineFilterGroup .seg-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        state.deadlineFilter = btn.getAttribute("data-filter") || "all";
        renderDeadlinesTable();
      });
    });

    document.getElementById("deadlineSearchInput")?.addEventListener("input", (e) => {
      state.deadlineSearch = e.target.value || "";
      renderDeadlinesTable();
    });

    // Schedule controls
    document.getElementById("btnFetchSchedule")?.addEventListener("click", () => doFetchSchedule(false));
    document.getElementById("btnSyncSchedule")?.addEventListener("click", doSyncSchedule);

    document.querySelectorAll("#scheduleDaysGroup .seg-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll("#scheduleDaysGroup .seg-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        state.scheduleDays = parseInt(btn.getAttribute("data-days") || "7", 10);
        doFetchSchedule(false);
      });
    });

    document.querySelectorAll("#scheduleTypeFilterGroup .seg-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll("#scheduleTypeFilterGroup .seg-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        state.scheduleTypeFilter = btn.getAttribute("data-type") || "all";
        renderScheduleList();
      });
    });

    document.getElementById("scheduleSearchInput")?.addEventListener("input", (e) => {
      state.scheduleSearch = e.target.value || "";
      renderScheduleList();
    });

    // Delegated external link opener
    document.body.addEventListener("click", async (e) => {
      const target = e.target.closest("[data-open-url]");
      if (!target) return;
      const url = target.getAttribute("data-open-url");
      if (!url) return;
      const api = getApi();
      if (api) {
        const res = await api.open_external_url(url);
        if (res && !res.ok) showApiError(res);
      } else {
        window.open(url, "_blank", "noopener,noreferrer");
      }
    });

    // Cron controls
    document.getElementById("btnEnableCron")?.addEventListener("click", async () => {
      const api = getApi();
      if (!api) return;
      clearFieldValidation();
      const timeVal = document.getElementById("cronTimeInput")?.value || "08:00";
      setBusy(true);
      try {
        const res = await api.configure_scheduler(true, timeVal);
        if (res.state) ingestStatePayload(res.state);
        if (res.ok) {
          showBanner(res.message || "Daily auto-sync enabled.", "success");
        } else {
          showApiError(res, "Could not update schedule.");
        }
      } finally {
        setBusy(false);
      }
    });

    document.getElementById("btnDisableCron")?.addEventListener("click", async () => {
      const api = getApi();
      if (!api) return;
      setBusy(true);
      try {
        const res = await api.configure_scheduler(false);
        if (res.state) ingestStatePayload(res.state);
        if (res.ok) {
          showBanner(res.message || "Daily auto-sync disabled.", "success");
        } else {
          showApiError(res, "Could not disable schedule.");
        }
      } finally {
        setBusy(false);
      }
    });

    document.getElementById("btnRefreshLogs")?.addEventListener("click", refreshLogs);

    // Connections: Moodle
    const moodleUrlInput = document.getElementById("moodleUrlInput");
    moodleUrlInput?.addEventListener("input", () => {
      moodleUrlInput.dataset.dirty = "1";
    });

    document.getElementById("btnConnectMoodle")?.addEventListener("click", async () => {
      const api = getApi();
      if (!api) return;
      clearFieldValidation();
      const url = document.getElementById("moodleUrlInput")?.value || "";
      const user = document.getElementById("moodleUserInput")?.value || "";
      const pass = document.getElementById("moodlePassInput")?.value || "";
      setBusy(true);
      try {
        const res = await api.connect_moodle(url, user, pass);
        if (res.ok) {
          if (res.state) ingestStatePayload(res.state);
          const passEl = document.getElementById("moodlePassInput");
          if (passEl) passEl.value = "";
          showBanner("Moodle connected and token saved!", "success");
          await doFetchDeadlines(true);
        } else {
          showApiError(res, "Moodle authentication failed.");
        }
      } finally {
        setBusy(false);
      }
    });

    // Connections: Google
    document.getElementById("btnToggleClassroom")?.addEventListener("click", async () => {
      const api = getApi();
      if (!api) return;
      const cur = !!(state.connections.google && state.connections.google.classroom_enabled);
      const res = await api.set_classroom_enabled(!cur);
      if (res.state) ingestStatePayload(res.state);
    });

    document.getElementById("btnOpenGoogleGuide")?.addEventListener("click", async () => {
      const api = getApi();
      const guideUrl = "https://vkatsel.github.io/deadliner/google_setup_guide.html";
      if (api) await api.open_external_url(guideUrl);
      else window.open(guideUrl, "_blank");
    });

    document.getElementById("btnConnectGoogle")?.addEventListener("click", async () => {
      const api = getApi();
      if (!api) return;
      clearFieldValidation();
      const rawJson = document.getElementById("googleSecretsTextarea")?.value || "";
      setBusy(true);
      try {
        const res = await api.connect_google("", "", rawJson);
        if (res.ok) {
          if (res.state) ingestStatePayload(res.state);
          showBanner("Google OAuth completed and token saved!", "success");
          await doFetchDeadlines(true);
        } else {
          showApiError(res, "Google authentication failed.");
        }
      } finally {
        setBusy(false);
      }
    });

    // Connections: KSE
    const handleKseWebview = async (clean) => {
      const api = getApi();
      if (!api) return;
      setBusy(true);
      try {
        const res = await api.connect_kse(clean);
        if (res.ok) {
          if (res.state) ingestStatePayload(res.state);
          showBanner("KSE Schedule connected successfully!", "success");
          await doFetchSchedule(true);
        } else {
          showApiError(res, "KSE login cancelled or failed.");
        }
      } finally {
        setBusy(false);
      }
    };

    document.getElementById("btnConnectKseWebview")?.addEventListener("click", () => handleKseWebview(false));
    document.getElementById("btnConnectKseClean")?.addEventListener("click", () => handleKseWebview(true));

    document.getElementById("btnSaveKseToken")?.addEventListener("click", async () => {
      const api = getApi();
      if (!api) return;
      clearFieldValidation();
      const raw = document.getElementById("kseTokenTextarea")?.value || "";
      setBusy(true);
      try {
        const res = await api.save_kse_token(raw);
        if (res.ok) {
          if (res.state) ingestStatePayload(res.state);
          const area = document.getElementById("kseTokenTextarea");
          if (area) area.value = "";
          showBanner("KSE token verified and saved!", "success");
          await doFetchSchedule(true);
        } else {
          showApiError(res, "Invalid KSE token.");
        }
      } finally {
        setBusy(false);
      }
    });

    // System PATH
    document.getElementById("btnConfigurePath")?.addEventListener("click", async () => {
      const api = getApi();
      if (!api) return;
      setBusy(true);
      try {
        const res = await api.configure_path();
        if (res.state) ingestStatePayload(res.state);
        if (res.ok) {
          showBanner(res.message, "success");
        } else {
          showApiError(res, "Failed to update system PATH.");
        }
      } finally {
        setBusy(false);
      }
    });
  }

  async function bootstrapFromPywebview() {
    const api = getApi();
    if (!api) return;
    try {
      const initial = await api.get_initial_state();
      ingestStatePayload(initial);

      // Auto-fetch in background on startup for connected sources
      const mConn = !!(state.connections.moodle && state.connections.moodle.connected);
      const gConn = !!(state.connections.google && state.connections.google.connected);
      const kConn = !!(state.connections.kse && state.connections.kse.connected);

      if (mConn || gConn) {
        await doFetchDeadlines(true);
      }
      if (kConn) {
        await doFetchSchedule(true);
      }
    } catch (err) {
      showBanner("Initialization error: " + String(err), "error");
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    bindEvents();
    renderAll();

    if (window.pywebview && window.pywebview.api) {
      bootstrapFromPywebview();
    } else {
      window.addEventListener("pywebviewready", () => {
        bootstrapFromPywebview();
      });
    }
  });
})();
