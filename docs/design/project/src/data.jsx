/* =========================================================================
   Sync Work — mock data + i18n
   Exposed on window: SW_DATA, SW_I18N, SW_HELP
   ========================================================================= */

/* ----------------------------- i18n ----------------------------------- */
const STRINGS = {
  uk: {
    app_name: "Sync Work",
    // nav
    nav_calendar: "Календар",
    nav_timecamp: "TimeCamp",
    nav_jira: "Jira",
    nav_tempo: "Tempo / Sync",
    nav_journal: "Журнал синку",
    nav_users: "Користувачі",
    nav_section_track: "Трекінг",
    nav_section_data: "Дані",
    nav_section_admin: "Адміністрування",
    // auth
    auth_subtitle: "Синхронізація робочого часу",
    auth_tagline: "TimeCamp → Jira · Tempo Timesheets",
    auth_email: "Логін або e-mail",
    auth_password: "Пароль",
    auth_signin: "Увійти",
    auth_google: "Увійти через Google",
    auth_or: "або",
    auth_remember: "Запам'ятати мене",
    auth_forgot: "Забули пароль?",
    auth_no_signup: "Реєстрація недоступна. Облікові записи створює адміністратор.",
    auth_hint: "demo: будь-який логін / пароль",
    // topbar
    today: "Сьогодні",
    week: "Тиждень",
    search: "Пошук…",
    sync_now: "Синхронізувати",
    syncing: "Синхронізація…",
    // calendar
    cal_filters: "Фільтри",
    cal_projects: "Проекти",
    cal_status: "Статус",
    cal_all: "Усі",
    cal_none: "Жоден",
    cal_workhours: "Робочі години",
    cal_variant: "Вигляд блоків",
    cal_variant_basic: "Базовий",
    cal_variant_soft: "М'який",
    cal_variant_bold: "Сміливий",
    cal_total: "Разом",
    cal_billable: "Білабл",
    // block states
    st_service: "Тільки з TimeCamp",
    st_tempo: "Є в Tempo",
    st_synced: "Синхронізовано",
    st_service_short: "Лише сервіс",
    st_tempo_short: "В Tempo",
    st_synced_short: "Синхр.",
    // block menu / detail
    blk_open: "Деталі",
    blk_sync: "Синхронізувати в Tempo",
    blk_edit_issue: "Змінити задачу…",
    blk_split: "Розділити",
    blk_duplicate: "Дублювати",
    blk_unlink: "Відв'язати",
    blk_delete: "Видалити",
    blk_project: "Проект",
    blk_issue: "Задача",
    blk_time: "Час",
    blk_duration: "Тривалість",
    blk_desc: "Опис",
    blk_billable: "Оплачуваний",
    blk_history: "Історія запису",
    blk_report: "Звіт",
    blk_save: "Зберегти",
    blk_cancel: "Скасувати",
    // tables
    tbl_sync_selected: "Синхронізувати вибрані",
    tbl_refresh: "Оновити з джерела",
    col_issue: "Задача",
    col_project: "Проект",
    col_desc: "Опис",
    col_date: "Дата",
    col_duration: "Час",
    col_status: "Статус",
    col_target: "Tempo ID",
    col_worker: "Працівник",
    col_entries: "Записів",
    col_issues: "Задач",
    col_name: "Назва",
    col_key: "Ключ",
    col_mapping: "Маппінг",
    col_sync_on: "У синку",
    col_watched: "Відстеж.",
    col_archived: "Архів",
    col_role: "Роль",
    col_email: "E-mail",
    col_last_seen: "Активність",
    tc_title: "TimeCamp — проекти та записи",
    tc_desc: "Джерело таймер-записів. Увімкніть проекти, що потрапляють у синхронізацію.",
    jr_title: "Jira — проекти та задачі",
    jr_desc: "Джерело задач і проектів. Відстежувані проекти підвантажуються першими.",
    tempo_title: "Tempo / Worklog Sync Tasks",
    tempo_desc: "Конвеєр синхронізації worklog-ів: pre_create → create → created.",
    tab_projects: "Проекти",
    tab_entries: "Записи",
    tab_issues: "Задачі",
    tab_worklogs: "Worklog-задачі",
    tab_untracked: "Незіставлені",
    // journal
    jr_journal_title: "Журнал синхронізацій",
    jr_journal_desc: "Кожен запуск синку логується. Крок needs_verification вимагає підтвердження.",
    job_trigger: "Тригер",
    job_started: "Старт",
    job_finished: "Фініш",
    job_by: "Запустив",
    job_verify: "Підтвердити",
    job_verified_by: "Підтвердив",
    job_view: "Деталі",
    job_payload: "Параметри",
    job_result: "Результат",
    job_error: "Помилка",
    // users
    users_title: "Користувачі",
    users_desc: "Облікові записи створює адміністратор. Самостійної реєстрації немає.",
    users_add: "Додати користувача",
    users_invite: "Запросити",
    user_full_name: "Ім'я",
    user_worker_key: "Jira key",
    user_role_admin: "Адмін",
    user_role_member: "Працівник",
    user_role_viewer: "Спостерігач",
    user_active: "Активний",
    user_disabled: "Вимкнено",
    // statuses (worklog sync task)
    s_pre_create: "Готується",
    s_create: "У черзі",
    s_created: "Створено",
    s_failed: "Помилка",
    s_needs_verification: "Потребує перевірки",
    s_running: "Виконується",
    s_verified: "Підтверджено",
    // misc
    empty: "Порожньо",
    rows: "рядків",
    selected: "вибрано",
    logout: "Вийти",
    settings: "Налаштування",
    profile: "Профіль",
    mon: "Пн", tue: "Вт", wed: "Ср", thu: "Чт", fri: "Пт", sat: "Сб", sun: "Нд",
  },
  en: {
    app_name: "Sync Work",
    nav_calendar: "Calendar",
    nav_timecamp: "TimeCamp",
    nav_jira: "Jira",
    nav_tempo: "Tempo / Sync",
    nav_journal: "Sync journal",
    nav_users: "Users",
    nav_section_track: "Track",
    nav_section_data: "Data",
    nav_section_admin: "Admin",
    auth_subtitle: "Work-time synchronization",
    auth_tagline: "TimeCamp → Jira · Tempo Timesheets",
    auth_email: "Login or e-mail",
    auth_password: "Password",
    auth_signin: "Sign in",
    auth_google: "Continue with Google",
    auth_or: "or",
    auth_remember: "Remember me",
    auth_forgot: "Forgot password?",
    auth_no_signup: "Sign-up is disabled. Accounts are created by an administrator.",
    auth_hint: "demo: any login / password",
    today: "Today",
    week: "Week",
    search: "Search…",
    sync_now: "Sync now",
    syncing: "Syncing…",
    cal_filters: "Filters",
    cal_projects: "Projects",
    cal_status: "Status",
    cal_all: "All",
    cal_none: "None",
    cal_workhours: "Work hours",
    cal_variant: "Block style",
    cal_variant_basic: "Basic",
    cal_variant_soft: "Soft",
    cal_variant_bold: "Bold",
    cal_total: "Total",
    cal_billable: "Billable",
    st_service: "From TimeCamp only",
    st_tempo: "In Tempo",
    st_synced: "Synced",
    st_service_short: "Service only",
    st_tempo_short: "In Tempo",
    st_synced_short: "Synced",
    blk_open: "Details",
    blk_sync: "Sync to Tempo",
    blk_edit_issue: "Change issue…",
    blk_split: "Split",
    blk_duplicate: "Duplicate",
    blk_unlink: "Unlink",
    blk_delete: "Delete",
    blk_project: "Project",
    blk_issue: "Issue",
    blk_time: "Time",
    blk_duration: "Duration",
    blk_desc: "Description",
    blk_billable: "Billable",
    blk_history: "Entry history",
    blk_report: "Report",
    blk_save: "Save",
    blk_cancel: "Cancel",
    tbl_sync_selected: "Sync selected",
    tbl_refresh: "Refresh from source",
    col_issue: "Issue",
    col_project: "Project",
    col_desc: "Description",
    col_date: "Date",
    col_duration: "Time",
    col_status: "Status",
    col_target: "Tempo ID",
    col_worker: "Worker",
    col_entries: "Entries",
    col_issues: "Issues",
    col_name: "Name",
    col_key: "Key",
    col_mapping: "Mapping",
    col_sync_on: "In sync",
    col_watched: "Watched",
    col_archived: "Archived",
    col_role: "Role",
    col_email: "E-mail",
    col_last_seen: "Last seen",
    tc_title: "TimeCamp — projects & entries",
    tc_desc: "Source of timer entries. Toggle which projects flow into sync.",
    jr_title: "Jira — projects & issues",
    jr_desc: "Source of issues and projects. Watched projects load first.",
    tempo_title: "Tempo / Worklog Sync Tasks",
    tempo_desc: "Worklog sync pipeline: pre_create → create → created.",
    tab_projects: "Projects",
    tab_entries: "Entries",
    tab_issues: "Issues",
    tab_worklogs: "Worklog tasks",
    tab_untracked: "Untracked",
    jr_journal_title: "Sync journal",
    jr_journal_desc: "Every sync run is logged. The needs_verification step requires confirmation.",
    job_trigger: "Trigger",
    job_started: "Started",
    job_finished: "Finished",
    job_by: "By",
    job_verify: "Verify",
    job_verified_by: "Verified by",
    job_view: "Details",
    job_payload: "Payload",
    job_result: "Result",
    job_error: "Error",
    users_title: "Users",
    users_desc: "Accounts are created by an administrator. There is no self sign-up.",
    users_add: "Add user",
    users_invite: "Invite",
    user_full_name: "Name",
    user_worker_key: "Jira key",
    user_role_admin: "Admin",
    user_role_member: "Member",
    user_role_viewer: "Viewer",
    user_active: "Active",
    user_disabled: "Disabled",
    s_pre_create: "Preparing",
    s_create: "Queued",
    s_created: "Created",
    s_failed: "Failed",
    s_needs_verification: "Needs verification",
    s_running: "Running",
    s_verified: "Verified",
    empty: "Empty",
    rows: "rows",
    selected: "selected",
    logout: "Log out",
    settings: "Settings",
    profile: "Profile",
    mon: "Mon", tue: "Tue", wed: "Wed", thu: "Thu", fri: "Fri", sat: "Sat", sun: "Sun",
  },
};

/* --------------------------- project palette -------------------------- */
/* one hue per project — fixed L/C, varying H, harmonious */
const PROJECTS = [
  { id: "OCT",  name: "Octopus",     cat: "Product",   key: "OCT",  hue: 205 },
  { id: "MGR",  name: "Manager",     cat: "Internal",  key: "SUPP", hue: 28  },
  { id: "BNM",  name: "Binom",       cat: "Direction", key: "BNM",  hue: 262 },
  { id: "AIT",  name: "AI Tools",    cat: "R&D",       key: "AIT",  hue: 168 },
  { id: "SEC",  name: "Security",    cat: "Direction", key: "SEC",  hue: 12  },
  { id: "AIA",  name: "AI Agents",   cat: "Direction", key: "AIA",  hue: 300 },
];
const projColor = (hue, l, c) => `oklch(${l} ${c} ${hue})`;
function projectColors(hue) {
  return {
    base: projColor(hue, 0.62, 0.13),
    strong: projColor(hue, 0.55, 0.15),
    soft: projColor(hue, 0.95, 0.035),
    softDark: projColor(hue, 0.28, 0.05),
    ink: projColor(hue, 0.42, 0.13),
    inkLight: projColor(hue, 0.80, 0.11),
  };
}

/* ------------------------ calendar blocks (week) ---------------------- */
/* status: service | tempo | synced ; day 0=Mon..6=Sun ; times in minutes */
const t = (h, m = 0) => h * 60 + m;
const BLOCKS = [
  // Monday
  { id: "b1", proj: "MGR", day: 0, start: t(9, 5),  end: t(11, 30), title: "Standup + grooming", issue: "SUPP-446", status: "synced", billable: true },
  { id: "b2", proj: "OCT", day: 0, start: t(12, 0), end: t(13, 0),  title: "Code review", issue: "OCT-740", status: "synced", billable: true },
  { id: "b3", proj: "BNM", day: 0, start: t(14, 0), end: t(15, 15), title: "Tracker debug", issue: "BNM-118", status: "tempo", billable: true },
  { id: "b4", proj: "AIA", day: 0, start: t(15, 20), end: t(17, 40), title: "Agent prompt tuning", issue: "AIA-31", status: "service", billable: false },
  // Tuesday
  { id: "b5", proj: "SEC", day: 1, start: t(9, 30), end: t(10, 30), title: "Security review", issue: "SEC-12", status: "synced", billable: true },
  { id: "b6", proj: "OCT", day: 1, start: t(10, 40), end: t(13, 0), title: "Product: checkout flow", issue: "OCT-759", status: "tempo", billable: true },
  { id: "b7", proj: "OCT", day: 1, start: t(14, 0), end: t(15, 10), title: "Product: bugfix", issue: "OCT-761", status: "service", billable: true },
  { id: "b8", proj: "OCT", day: 1, start: t(15, 20), end: t(18, 0), title: "Product: refactor cart", issue: "OCT-762", status: "service", billable: true },
  // Wednesday
  { id: "b9", proj: "MGR", day: 2, start: t(9, 0), end: t(10, 20), title: "1:1s", issue: "SUPP-450", status: "synced", billable: false },
  { id: "b10", proj: "OCT", day: 2, start: t(13, 30), end: t(17, 12), title: "Task — manager view", issue: "OCT-759", status: "tempo", billable: true },
  { id: "b11", proj: "AIT", day: 2, start: t(17, 21), end: t(18, 40), title: "AI tools spike", issue: "AIT-7", status: "service", billable: false },
  { id: "b12", proj: "OCT", day: 2, start: t(18, 45), end: t(20, 8), title: "Task — followup", issue: "OCT-759", status: "service", billable: true },
  // Thursday
  { id: "b13", proj: "OCT", day: 3, start: t(11, 0), end: t(13, 0), title: "Product sync", issue: "OCT-759", status: "synced", billable: true },
  { id: "b14", proj: "OCT", day: 3, start: t(16, 0), end: t(17, 30), title: "Manager — OCT-761", issue: "OCT-761", status: "tempo", billable: true },
  { id: "b15", proj: "BNM", day: 3, start: t(17, 40), end: t(19, 0), title: "Binom integration", issue: "BNM-120", status: "service", billable: true },
  // Friday
  { id: "b16", proj: "AIT", day: 4, start: t(9, 30), end: t(12, 0), title: "AI tools — eval harness", issue: "AIT-9", status: "synced", billable: false },
  { id: "b17", proj: "OCT", day: 4, start: t(13, 0), end: t(15, 0), title: "Octopus — release prep", issue: "OCT-770", status: "service", billable: true },
];

/* --------------------------- TimeCamp data ---------------------------- */
const TC_PROJECTS = [
  { id: 8801, name: "Octopus / Product", is_sync: true, issue_key: "OCT", is_archived: false, entries_count: 142 },
  { id: 8802, name: "Manager / Task", is_sync: true, issue_key: "SUPP", is_archived: false, entries_count: 88 },
  { id: 8803, name: "Binom / Direction", is_sync: true, issue_key: "BNM", is_archived: false, entries_count: 41 },
  { id: 8804, name: "AI Tools", is_sync: true, issue_key: "AIT", is_archived: false, entries_count: 23 },
  { id: 8805, name: "Security / Direction", is_sync: false, issue_key: null, is_archived: false, entries_count: 12 },
  { id: 8806, name: "Portuguese / Home", is_sync: false, issue_key: null, is_archived: false, entries_count: 9 },
  { id: 8807, name: "AI Agents / Direction", is_sync: true, issue_key: "AIA", is_archived: false, entries_count: 17 },
  { id: 8808, name: "Old marketing", is_sync: false, issue_key: null, is_archived: true, entries_count: 4 },
];
const TC_UNTRACKED = [
  { id: 99001, description: "octopus checkout", start_at: "2026-06-02 14:00", end_at: "2026-06-02 15:10", tc_project_id: 8801, tc_project_name: "Octopus / Product" },
  { id: 99002, description: "ai agents tuning", start_at: "2026-06-01 15:20", end_at: "2026-06-01 17:40", tc_project_id: 8807, tc_project_name: "AI Agents / Direction" },
  { id: 99003, description: "spike", start_at: "2026-06-03 17:21", end_at: "2026-06-03 18:40", tc_project_id: 8804, tc_project_name: "AI Tools" },
  { id: 99004, description: "binom integration work", start_at: "2026-06-04 17:40", end_at: "2026-06-04 19:00", tc_project_id: 8803, tc_project_name: "Binom / Direction" },
];

/* ----------------------------- Jira data ------------------------------ */
const JR_PROJECTS = [
  { id: 1, key: "OCT", name: "Octopus", is_archived: false, is_watched: true, issues_count: 318 },
  { id: 2, key: "SUPP", name: "Support / Manager", is_archived: false, is_watched: true, issues_count: 204 },
  { id: 3, key: "BNM", name: "Binom", is_archived: false, is_watched: false, issues_count: 96 },
  { id: 4, key: "AIT", name: "AI Tools", is_archived: false, is_watched: true, issues_count: 47 },
  { id: 5, key: "SEC", name: "Security", is_archived: false, is_watched: false, issues_count: 33 },
  { id: 6, key: "AIA", name: "AI Agents", is_archived: false, is_watched: false, issues_count: 28 },
  { id: 7, key: "LGCY", name: "Legacy CRM", is_archived: true, is_watched: false, issues_count: 510 },
];
const JR_ISSUES = [
  { key: "OCT-759", project: "OCT", summary: "Checkout flow — manager view", status: "In Progress", worklogs: 6 },
  { key: "OCT-761", project: "OCT", summary: "Bugfix: cart total rounding", status: "In Review", worklogs: 3 },
  { key: "OCT-762", project: "OCT", summary: "Refactor cart service", status: "In Progress", worklogs: 2 },
  { key: "OCT-770", project: "OCT", summary: "Release 2.4 prep", status: "To Do", worklogs: 0 },
  { key: "SUPP-446", project: "SUPP", summary: "Grooming + standup notes", status: "Done", worklogs: 12 },
  { key: "SUPP-450", project: "SUPP", summary: "1:1 tracking", status: "In Progress", worklogs: 4 },
  { key: "BNM-118", project: "BNM", summary: "Tracker debug session", status: "In Progress", worklogs: 5 },
  { key: "BNM-120", project: "BNM", summary: "Binom → DWH integration", status: "To Do", worklogs: 1 },
  { key: "AIT-7", project: "AIT", summary: "AI tools spike", status: "In Progress", worklogs: 2 },
  { key: "AIT-9", project: "AIT", summary: "Eval harness", status: "In Review", worklogs: 3 },
  { key: "SEC-12", project: "SEC", summary: "Quarterly security review", status: "Done", worklogs: 8 },
  { key: "AIA-31", project: "AIA", summary: "Agent prompt tuning", status: "In Progress", worklogs: 1 },
];

/* --------------------- Worklog sync tasks (Tempo) --------------------- */
const WST = [
  { id: 5001, status: "created", source_id: 771201, target_id: 880431, worker_key: "i.petrenko", issue_key: "SUPP-446", issue_id: 44012, content: "Standup + grooming", started_at: "2026-06-01 09:05", time_spent: 8700 },
  { id: 5002, status: "created", source_id: 771202, target_id: 880432, worker_key: "i.petrenko", issue_key: "OCT-740", issue_id: 44190, content: "Code review", started_at: "2026-06-01 12:00", time_spent: 3600 },
  { id: 5003, status: "create", source_id: 771203, target_id: null, worker_key: "i.petrenko", issue_key: "BNM-118", issue_id: 44210, content: "Tracker debug", started_at: "2026-06-01 14:00", time_spent: 4500 },
  { id: 5004, status: "pre_create", source_id: 771204, target_id: null, worker_key: "i.petrenko", issue_key: "AIA-31", issue_id: null, content: "Agent prompt tuning", started_at: "2026-06-01 15:20", time_spent: 8400 },
  { id: 5005, status: "created", source_id: 771205, target_id: 880455, worker_key: "i.petrenko", issue_key: "SEC-12", issue_id: 44230, content: "Security review", started_at: "2026-06-02 09:30", time_spent: 3600 },
  { id: 5006, status: "create", source_id: 771206, target_id: null, worker_key: "i.petrenko", issue_key: "OCT-759", issue_id: 44012, content: "Checkout flow", started_at: "2026-06-02 10:40", time_spent: 8400 },
  { id: 5007, status: "pre_create", source_id: 771207, target_id: null, worker_key: "i.petrenko", issue_key: "OCT-761", issue_id: null, content: "Bugfix", started_at: "2026-06-02 14:00", time_spent: 4200 },
  { id: 5008, status: "failed", source_id: 771208, target_id: null, worker_key: "i.petrenko", issue_key: "OCT-762", issue_id: null, content: "Refactor cart — issue not found", started_at: "2026-06-02 15:20", time_spent: 9600 },
  { id: 5009, status: "created", source_id: 771209, target_id: 880470, worker_key: "i.petrenko", issue_key: "OCT-759", issue_id: 44012, content: "Task — manager view", started_at: "2026-06-03 13:30", time_spent: 13320 },
  { id: 5010, status: "pre_create", source_id: 771210, target_id: null, worker_key: "i.petrenko", issue_key: "AIT-7", issue_id: null, content: "AI tools spike", started_at: "2026-06-03 17:21", time_spent: 4740 },
];

/* --------------------------- API jobs (journal) ----------------------- */
const API_JOBS = [
  { id: "j-1041", trigger_name: "sync/worklog-tasks/push-to-tempo", status: "needs_verification", created_by: "i.petrenko", verified_by: null, started_at: "2026-06-05 18:02:11", finished_at: "2026-06-05 18:02:39", verified_at: null, payload: { start: "2026-06-01", end: "2026-06-07", count: 6 }, result: { created: 4, skipped: 1, pending_verify: 1 }, error: null },
  { id: "j-1040", trigger_name: "sync/jira/issues", status: "verified", created_by: "i.petrenko", verified_by: "i.petrenko", started_at: "2026-06-05 18:01:50", finished_at: "2026-06-05 18:02:04", verified_at: "2026-06-05 18:05:00", payload: { keys: ["OCT-759", "OCT-761", "BNM-118"] }, result: { upserted: 3 }, error: null },
  { id: "j-1039", trigger_name: "sync/timecamp/entries", status: "verified", created_by: "i.petrenko", verified_by: "i.petrenko", started_at: "2026-06-05 18:01:20", finished_at: "2026-06-05 18:01:41", verified_at: "2026-06-05 18:04:30", payload: { start: "2026-06-01", end: "2026-06-07" }, result: { upserted: 41, new: 7 }, error: null },
  { id: "j-1038", trigger_name: "sync/worklog-tasks/resolve-issues", status: "failed", created_by: "i.petrenko", verified_by: null, started_at: "2026-06-05 17:40:02", finished_at: "2026-06-05 17:40:10", verified_at: null, payload: { keys: ["OCT-762"] }, result: null, error: "Issue OCT-762 not found in Jira (404)" },
  { id: "j-1037", trigger_name: "sync/timecamp/projects", status: "verified", created_by: "i.petrenko", verified_by: "i.petrenko", started_at: "2026-06-05 17:39:50", finished_at: "2026-06-05 17:39:55", verified_at: "2026-06-05 17:42:00", payload: {}, result: { upserted: 8 }, error: null },
  { id: "j-1036", trigger_name: "sync/jira/projects", status: "verified", created_by: "i.petrenko", verified_by: "i.petrenko", started_at: "2026-06-05 17:39:30", finished_at: "2026-06-05 17:39:38", verified_at: "2026-06-05 17:41:30", payload: {}, result: { upserted: 7 }, error: null },
  { id: "j-1035", trigger_name: "sync/worklog-tasks/prepare", status: "running", created_by: "i.petrenko", verified_by: null, started_at: "2026-06-05 17:38:00", finished_at: null, verified_at: null, payload: { start: "2026-06-01", end: "2026-06-07" }, result: null, error: null },
];

/* ------------------------------ Users --------------------------------- */
const USERS = [
  { id: 1, name: "Ivan Petrenko", email: "i.petrenko@leadsdoit.io", worker_key: "i.petrenko", role: "admin", active: true, last_seen: "щойно", initials: "IP", hue: 205 },
  { id: 2, name: "Olena Koval", email: "o.koval@leadsdoit.io", worker_key: "o.koval", role: "member", active: true, last_seen: "2 год тому", initials: "OK", hue: 28 },
  { id: 3, name: "Dmytro Savchuk", email: "d.savchuk@leadsdoit.io", worker_key: "d.savchuk", role: "member", active: true, last_seen: "вчора", initials: "DS", hue: 168 },
  { id: 4, name: "Maria Tkachenko", email: "m.tkachenko@leadsdoit.io", worker_key: "m.tkachenko", role: "viewer", active: false, last_seen: "3 дні тому", initials: "MT", hue: 300 },
];

/* ---------------------------- helpers --------------------------------- */
function fmtMin(min) {
  const h = Math.floor(min / 60), m = Math.round(min % 60);
  return m === 0 ? `${h}:00` : `${h}:${String(m).padStart(2, "0")}`;
}
function fmtDur(min) {
  const h = Math.floor(min / 60), m = Math.round(min % 60);
  if (h === 0) return `${m}m`;
  return m === 0 ? `${h}h` : `${h}h ${m}m`;
}
function fmtSpan(start, end) {
  const f = (x) => `${String(Math.floor(x / 60)).padStart(2, "0")}:${String(x % 60).padStart(2, "0")}`;
  return `${f(start)} – ${f(end)}`;
}
function secToHm(sec) {
  const h = Math.floor(sec / 3600), m = Math.round((sec % 3600) / 60);
  return m === 0 ? `${h}h` : `${h}h ${m}m`;
}

window.SW_I18N = STRINGS;
window.SW_DATA = {
  PROJECTS, BLOCKS, TC_PROJECTS, TC_UNTRACKED, JR_PROJECTS, JR_ISSUES,
  WST, API_JOBS, USERS,
};
window.SW_HELP = { projectColors, projColor, fmtMin, fmtDur, fmtSpan, secToHm,
  projById: (id) => PROJECTS.find((p) => p.id === id) };
