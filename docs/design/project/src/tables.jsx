/* =========================================================================
   Sync Work — data screens: shared scaffold + TimeCamp / Jira / Tempo
   Exposes: PageHeader, Tabs, DataTable, StatusBadge, SyncBtn,
            TimeCampScreen, JiraScreen, TempoScreen
   ========================================================================= */
const { useState: useStateT, useMemo: useMemoT } = React;

/* ---- worklog-sync-task / job status meta ---- */
const STATUS_META = {
  pre_create: { tone: "neutral", soft: true, icon: "cloudDown" },
  create: { tone: "accent", icon: "clock" },
  created: { tone: "green", icon: "check" },
  failed: { tone: "red", icon: "alert" },
  running: { tone: "accent", icon: "sync" },
  needs_verification: { tone: "amber", icon: "eye" },
  verified: { tone: "green", icon: "check" },
};
function StatusBadge({ status, t }) {
  const m = STATUS_META[status] || { tone: "neutral" };
  const label = t["s_" + status] || status;
  return <Badge tone={m.tone} soft={m.soft} icon={m.icon}>{label}</Badge>;
}

/* ---- page scaffold ---- */
function PageHeader({ title, desc, actions }) {
  return (
    <div className="page__head">
      <div className="page__titles">
        <h1>{title}</h1>
        {desc && <p>{desc}</p>}
      </div>
      {actions && <div className="page__actions">{actions}</div>}
    </div>
  );
}
function Tabs({ tabs, active, onChange }) {
  return (
    <div className="page__tabs">
      {tabs.map((tb) => (
        <button key={tb.id} className={`page__tab ${active === tb.id ? "is-active" : ""}`} onClick={() => onChange(tb.id)}>
          {tb.icon && <Icon name={tb.icon} size={15} />}
          {tb.label}
          {tb.count != null && <Badge tone="neutral" soft>{tb.count}</Badge>}
        </button>
      ))}
    </div>
  );
}

/* ---- a sync-trigger button that shows running → done ---- */
function SyncBtn({ label, icon = "sync", variant = "default", size = "sm", onDone }) {
  const [state, setState] = useStateT("idle");
  const run = () => {
    if (state === "running") return;
    setState("running");
    setTimeout(() => { setState("done"); onDone && onDone(); setTimeout(() => setState("idle"), 1600); }, 1300);
  };
  return (
    <Btn size={size} variant={state === "done" ? "soft" : variant} onClick={run}
      icon={state === "running" ? undefined : (state === "done" ? "check" : icon)}>
      {state === "running" && <Spinner size={14} />}
      {state === "running" ? "…" : label}
    </Btn>
  );
}

/* ---- generic table ---- */
function DataTable({ columns, rows, getId, selectable, selected, onSelected, onRowClick, empty }) {
  const allSel = selectable && rows.length > 0 && rows.every((r) => selected.has(getId(r)));
  const someSel = selectable && rows.some((r) => selected.has(getId(r)));
  const toggleAll = () => {
    const n = new Set(selected);
    if (allSel) rows.forEach((r) => n.delete(getId(r)));
    else rows.forEach((r) => n.add(getId(r)));
    onSelected(n);
  };
  const toggleOne = (id) => { const n = new Set(selected); n.has(id) ? n.delete(id) : n.add(id); onSelected(n); };
  return (
    <div className="dt-wrap">
      <table className="dt">
        <thead>
          <tr>
            {selectable && <th className="dt__sel"><Checkbox checked={allSel} indeterminate={someSel && !allSel} onChange={toggleAll} /></th>}
            {columns.map((c) => (
              <th key={c.key} style={{ width: c.width, textAlign: c.align }} className={c.align === "right" ? "is-right" : ""}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr><td colSpan={columns.length + (selectable ? 1 : 0)} className="dt__empty">{empty || "—"}</td></tr>
          )}
          {rows.map((r) => {
            const id = getId(r);
            return (
              <tr key={id} className={`${selected && selected.has(id) ? "is-sel" : ""} ${onRowClick ? "is-click" : ""}`}
                onClick={() => onRowClick && onRowClick(r)}>
                {selectable && <td className="dt__sel" onClick={(e) => e.stopPropagation()}><Checkbox checked={selected.has(id)} onChange={() => toggleOne(id)} /></td>}
                {columns.map((c) => (
                  <td key={c.key} style={{ textAlign: c.align }} className={`${c.align === "right" ? "is-right" : ""} ${c.mono ? "mono" : ""}`}>
                    {c.render ? c.render(r) : r[c.key]}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/* a small project tag */
function ProjTag({ pkey }) {
  const p = SW_DATA.PROJECTS.find((x) => x.key === pkey || x.id === pkey);
  const hue = p ? p.hue : 250;
  const c = SW_HELP.projectColors(hue);
  return <span className="projtag" style={{ background: c.soft, color: c.ink }}><span className="projtag__dot" style={{ background: c.base }} />{p ? p.name : pkey}</span>;
}

/* ============================ TimeCamp ============================== */
function TimeCampScreen({ t, lang, dark }) {
  const [tab, setTab] = useStateT("projects");
  const [projects, setProjects] = useStateT(() => SW_DATA.TC_PROJECTS.map((p) => ({ ...p })));
  const tog = (id) => setProjects((ps) => ps.map((p) => p.id === id ? { ...p, is_sync: !p.is_sync } : p));

  const projCols = [
    { key: "name", label: t.col_name, render: (r) => <div className="dt-name"><span className="mono dt-name__id">#{r.id}</span>{r.name}{r.is_archived && <Badge tone="neutral" soft>{t.col_archived}</Badge>}</div> },
    { key: "issue_key", label: t.col_mapping, render: (r) => r.issue_key ? <span className="map-arrow"><span className="mono">{r.issue_key}</span><Icon name="arrowRight" size={13} /></span> : <span className="faint">—</span> },
    { key: "entries_count", label: t.col_entries, align: "right", mono: true, width: 90 },
    { key: "is_sync", label: t.col_sync_on, align: "right", width: 90, render: (r) => <Toggle size="sm" checked={r.is_sync} onChange={() => tog(r.id)} /> },
  ];
  const untrCols = [
    { key: "description", label: t.col_desc, render: (r) => <span className="mono">{r.description}</span> },
    { key: "tc_project_name", label: t.col_project, render: (r) => r.tc_project_name },
    { key: "start_at", label: t.col_date, mono: true, render: (r) => r.start_at.slice(5) },
    { key: "dur", label: t.col_duration, align: "right", mono: true, width: 80, render: (r) => SW_HELP.fmtDur((new Date(r.end_at) - new Date(r.start_at)) / 60000) },
    { key: "act", label: "", align: "right", width: 110, render: () => <Btn size="sm" variant="ghost" icon="link">{lang === "uk" ? "Зіставити" : "Match"}</Btn> },
  ];

  return (
    <div className="page">
      <PageHeader title={t.tc_title} desc={t.tc_desc} actions={
        <><SyncBtn label={t.tbl_refresh} icon="cloudDown" />
          <SyncBtn label={lang === "uk" ? "Тягнути записи" : "Pull entries"} icon="sync" variant="primary" /></>
      } />
      <Tabs active={tab} onChange={setTab} tabs={[
        { id: "projects", label: t.tab_projects, icon: "table", count: projects.length },
        { id: "untracked", label: t.tab_untracked, icon: "alert", count: SW_DATA.TC_UNTRACKED.length },
      ]} />
      <div className="page__body">
        {tab === "projects"
          ? <DataTable columns={projCols} rows={projects} getId={(r) => r.id} />
          : <DataTable columns={untrCols} rows={SW_DATA.TC_UNTRACKED} getId={(r) => r.id} />}
      </div>
    </div>
  );
}

/* ============================== Jira =============================== */
function JiraScreen({ t, lang, dark }) {
  const [tab, setTab] = useStateT("projects");
  const [projects, setProjects] = useStateT(() => SW_DATA.JR_PROJECTS.map((p) => ({ ...p })));
  const togW = (id) => setProjects((ps) => ps.map((p) => p.id === id ? { ...p, is_watched: !p.is_watched } : p));

  const projCols = [
    { key: "key", label: t.col_key, width: 90, render: (r) => <span className="mono key-pill">{r.key}</span> },
    { key: "name", label: t.col_name, render: (r) => <div className="dt-name">{r.name}{r.is_archived && <Badge tone="neutral" soft>{t.col_archived}</Badge>}</div> },
    { key: "issues_count", label: t.col_issues, align: "right", mono: true, width: 90 },
    { key: "is_watched", label: t.col_watched, align: "right", width: 90, render: (r) => <Toggle size="sm" checked={r.is_watched} onChange={() => togW(r.id)} /> },
  ];
  const issueCols = [
    { key: "key", label: t.col_key, width: 100, render: (r) => <span className="mono key-pill">{r.key}</span> },
    { key: "summary", label: t.col_desc },
    { key: "project", label: t.col_project, width: 150, render: (r) => <ProjTag pkey={r.project} /> },
    { key: "status", label: t.col_status, width: 130, render: (r) => <JiraStatus s={r.status} /> },
    { key: "worklogs", label: "Worklogs", align: "right", mono: true, width: 90 },
  ];

  return (
    <div className="page">
      <PageHeader title={t.jr_title} desc={t.jr_desc} actions={
        <><SyncBtn label={t.tbl_refresh} icon="cloudDown" />
          <SyncBtn label={lang === "uk" ? "Тягнути задачі" : "Pull issues"} icon="sync" variant="primary" /></>
      } />
      <Tabs active={tab} onChange={setTab} tabs={[
        { id: "projects", label: t.tab_projects, icon: "table", count: projects.length },
        { id: "issues", label: t.tab_issues, icon: "inbox", count: SW_DATA.JR_ISSUES.length },
      ]} />
      <div className="page__body">
        {tab === "projects"
          ? <DataTable columns={projCols} rows={projects} getId={(r) => r.id} />
          : <DataTable columns={issueCols} rows={SW_DATA.JR_ISSUES} getId={(r) => r.key} />}
      </div>
    </div>
  );
}
function JiraStatus({ s }) {
  const tone = s === "Done" ? "green" : s === "To Do" ? "neutral" : s === "In Review" ? "amber" : "accent";
  return <Badge tone={tone} soft dot>{s}</Badge>;
}

/* ============================== Tempo ============================== */
function TempoScreen({ t, lang, dark }) {
  const [rows, setRows] = useStateT(() => SW_DATA.WST.map((w) => ({ ...w })));
  const [sel, setSel] = useStateT(() => new Set());

  const summary = useMemoT(() => {
    const s = {}; rows.forEach((r) => s[r.status] = (s[r.status] || 0) + 1); return s;
  }, [rows]);

  const pushSelected = () => {
    setRows((rs) => rs.map((r) => sel.has(r.id) && r.status !== "created"
      ? { ...r, status: "created", target_id: r.target_id || 880000 + Math.floor(Math.random() * 999) } : r));
    setSel(new Set());
  };

  const cols = [
    { key: "issue_key", label: t.col_issue, width: 110, render: (r) => <span className="mono key-pill">{r.issue_key}</span> },
    { key: "content", label: t.col_desc },
    { key: "worker_key", label: t.col_worker, width: 120, mono: true },
    { key: "started_at", label: t.col_date, width: 130, mono: true, render: (r) => r.started_at.slice(5) },
    { key: "time_spent", label: t.col_duration, align: "right", mono: true, width: 80, render: (r) => SW_HELP.secToHm(r.time_spent) },
    { key: "status", label: t.col_status, width: 150, render: (r) => <StatusBadge status={r.status} t={t} /> },
    { key: "target_id", label: t.col_target, align: "right", width: 110, mono: true, render: (r) => r.target_id ? "#" + r.target_id : <span className="faint">—</span> },
  ];

  const PIPE = [
    { key: "prepare", label: "prepare", trig: "worklog-tasks/prepare" },
    { key: "resolve", label: "resolve-issues", trig: "worklog-tasks/resolve-issues" },
    { key: "push", label: "push-to-tempo", trig: "worklog-tasks/push-to-tempo" },
  ];

  return (
    <div className="page">
      <PageHeader title={t.tempo_title} desc={t.tempo_desc} actions={
        <Btn size="sm" variant="primary" icon="sync" disabled={sel.size === 0} onClick={pushSelected}>
          {t.tbl_sync_selected}{sel.size > 0 ? ` (${sel.size})` : ""}
        </Btn>
      } />
      <div className="pipe">
        <div className="pipe__summary">
          {["pre_create", "create", "created", "failed"].map((s) => (
            <div key={s} className="pipe__stat">
              <StatusBadge status={s} t={t} />
              <b className="mono">{summary[s] || 0}</b>
            </div>
          ))}
        </div>
        <span className="spacer" />
        <div className="pipe__steps">
          <span className="pipe__label mono">pre_create → create → created</span>
          {PIPE.map((p) => <SyncBtn key={p.key} label={p.label} icon="bolt" size="sm" />)}
        </div>
      </div>
      <div className="page__body">
        <DataTable columns={cols} rows={rows} getId={(r) => r.id} selectable selected={sel} onSelected={setSel}
          empty={t.empty} />
      </div>
    </div>
  );
}

Object.assign(window, { PageHeader, Tabs, DataTable, StatusBadge, SyncBtn, ProjTag, TimeCampScreen, JiraScreen, TempoScreen });
