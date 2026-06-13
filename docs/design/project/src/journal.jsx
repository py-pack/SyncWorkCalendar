/* =========================================================================
   Sync Work — Sync journal (api-jobs) with verify step
   ========================================================================= */
const { useState: useStateJ } = React;

function JournalScreen({ t, lang, dark }) {
  const [jobs, setJobs] = useStateJ(() => SW_DATA.API_JOBS.map((j) => ({ ...j })));
  const [open, setOpen] = useStateJ(null);
  const [filter, setFilter] = useStateJ("all");

  const verify = (id) => setJobs((js) => js.map((j) => j.id === id ? { ...j, status: "verified", verified_by: "i.petrenko", verified_at: "2026-06-05 18:09:00" } : j));

  const FILTERS = [
    { id: "all", label: t.cal_all },
    { id: "needs_verification", label: t.s_needs_verification },
    { id: "failed", label: t.s_failed },
    { id: "running", label: t.s_running },
  ];
  const shown = filter === "all" ? jobs : jobs.filter((j) => j.status === filter);
  const cur = open ? jobs.find((j) => j.id === open) : null;

  const cols = [
    { key: "id", label: "ID", width: 90, mono: true },
    { key: "trigger_name", label: t.job_trigger, render: (r) => <span className="mono job-trig"><Icon name="bolt" size={13} />{r.trigger_name}</span> },
    { key: "status", label: t.col_status, width: 170, render: (r) => r.status === "running" ? <Badge tone="accent" soft><Spinner size={11} />{t.s_running}</Badge> : <StatusBadge status={r.status} t={t} /> },
    { key: "started_at", label: t.job_started, width: 160, mono: true, render: (r) => r.started_at.slice(5) },
    { key: "created_by", label: t.job_by, width: 120, mono: true },
    { key: "act", label: "", align: "right", width: 130, render: (r) => r.status === "needs_verification"
        ? <Btn size="sm" variant="primary" icon="check" onClick={(e) => { e.stopPropagation(); verify(r.id); }}>{t.job_verify}</Btn>
        : <Icon name="chevR" size={16} /> },
  ];

  return (
    <div className="page">
      <PageHeader title={t.jr_journal_title} desc={t.jr_journal_desc} actions={<SyncBtn label={t.tbl_refresh} icon="sync" />} />
      <div className="pipe">
        <div className="cal__chips">
          {FILTERS.map((f) => (
            <button key={f.id} className={`chip ${filter === f.id ? "is-on" : ""}`} onClick={() => setFilter(f.id)}>{f.label}</button>
          ))}
        </div>
      </div>
      <div className="page__body">
        <DataTable columns={cols} rows={shown} getId={(r) => r.id} onRowClick={(r) => setOpen(r.id)} empty={t.empty} />
      </div>

      <Sheet open={!!cur} onClose={() => setOpen(null)} title={cur ? cur.id : ""} width={420}>
        {cur && (
          <div className="jobdet">
            <div className="jobdet__row"><span className="mono job-trig"><Icon name="bolt" size={14} />{cur.trigger_name}</span></div>
            <div className="jobdet__grid">
              <div><span className="muted">{t.col_status}</span>{cur.status === "running" ? <Badge tone="accent" soft><Spinner size={11} />{t.s_running}</Badge> : <StatusBadge status={cur.status} t={t} />}</div>
              <div><span className="muted">{t.job_by}</span><span className="mono">{cur.created_by}</span></div>
              <div><span className="muted">{t.job_started}</span><span className="mono">{cur.started_at}</span></div>
              <div><span className="muted">{t.job_finished}</span><span className="mono">{cur.finished_at || "—"}</span></div>
              <div><span className="muted">{t.job_verified_by}</span><span className="mono">{cur.verified_by || "—"}</span></div>
              <div><span className="muted">verified_at</span><span className="mono">{cur.verified_at ? cur.verified_at.slice(11) : "—"}</span></div>
            </div>

            <div className="jobdet__sec">
              <div className="jobdet__lbl">{t.job_payload}</div>
              <pre className="jobdet__json mono">{JSON.stringify(cur.payload, null, 2)}</pre>
            </div>
            {cur.result && <div className="jobdet__sec">
              <div className="jobdet__lbl">{t.job_result}</div>
              <pre className="jobdet__json mono">{JSON.stringify(cur.result, null, 2)}</pre>
            </div>}
            {cur.error && <div className="jobdet__sec">
              <div className="jobdet__lbl is-err">{t.job_error}</div>
              <pre className="jobdet__json mono is-err">{cur.error}</pre>
            </div>}

            {cur.status === "needs_verification" && (
              <div className="jobdet__verify">
                <Icon name="eye" size={16} />
                <span>{t.s_needs_verification}</span>
                <Btn size="sm" variant="primary" icon="check" onClick={() => verify(cur.id)}>{t.job_verify}</Btn>
              </div>
            )}
          </div>
        )}
      </Sheet>
    </div>
  );
}

window.JournalScreen = JournalScreen;
