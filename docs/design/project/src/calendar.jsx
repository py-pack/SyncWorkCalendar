/* =========================================================================
   Sync Work — weekly timesheet grid (toolbar, filters, drag/resize)
   Exposes: CalendarScreen
   ========================================================================= */
const { useState: useStateC, useRef: useRefC, useMemo, useEffect: useEffectC } = React;

const DAY_START = 8 * 60;     // 08:00
const DAY_END = 21 * 60;      // 21:00
const HOUR_H = 56;            // px per hour
const SNAP = 5;               // minutes
const PXMIN = HOUR_H / 60;

const WEEK_DATES = ["1", "2", "3", "4", "5", "6", "7"]; // June 2026, Mon..Sun
const TODAY_IDX = 2;          // Wed 3 Jun "now"
const NOW_MIN = 18 * 60 + 12; // current-time line

function CalendarScreen({ t, lang, dark, variant, setVariant }) {
  const P = SW_DATA.PROJECTS;
  const [blocks, setBlocks] = useStateC(() => SW_DATA.BLOCKS.map((b) => ({ ...b })));
  const [hiddenProj, setHiddenProj] = useStateC(() => new Set());
  const [hiddenState, setHiddenState] = useStateC(() => new Set());
  const [showFilters, setShowFilters] = useStateC(true);
  const [sel, setSel] = useStateC(null);
  const [pop, setPop] = useStateC(null);       // {block, anchor}
  const [menu, setMenu] = useStateC(null);      // {block, x, y}
  const [drag, setDrag] = useStateC(null);      // live drag/resize state
  const [syncing, setSyncing] = useStateC(false);
  const gridRef = useRefC(null);

  const projById = (id) => P.find((p) => p.id === id);
  const colorsFor = (id) => SW_HELP.projectColors(projById(id).hue);

  const visible = blocks.filter((b) => !hiddenProj.has(b.proj) && !hiddenState.has(b.status));

  // per-day totals + lane layout
  const byDay = useMemo(() => {
    const days = Array.from({ length: 7 }, () => []);
    visible.forEach((b) => days[b.day].push(b));
    return days.map((list) => {
      const sorted = [...list].sort((a, b) => a.start - b.start || a.end - b.end);
      const lanes = [];
      sorted.forEach((b) => {
        let placed = false;
        for (const lane of lanes) {
          if (lane[lane.length - 1].end <= b.start) { lane.push(b); b._lane = lanes.indexOf(lane); placed = true; break; }
        }
        if (!placed) { b._lane = lanes.length; lanes.push([b]); }
      });
      // compute lane count for overlap groups (simple: max concurrent)
      sorted.forEach((b) => {
        const overlap = sorted.filter((o) => o.start < b.end && o.end > b.start);
        b._lanes = Math.max(...overlap.map((o) => (o._lane ?? 0) + 1));
      });
      return sorted;
    });
  }, [visible]);

  const dayTotals = byDay.map((list) => list.reduce((s, b) => s + (b.end - b.start), 0));
  const weekTotal = dayTotals.reduce((a, b) => a + b, 0);
  const billTotal = visible.filter((b) => b.billable).reduce((s, b) => s + (b.end - b.start), 0);

  /* ----------------------------- drag/resize ------------------------------ */
  function snap(min) { return Math.round(min / SNAP) * SNAP; }

  function startBody(e, block) {
    if (e.button !== 0) return;
    e.preventDefault();
    const startY = e.clientY, startX = e.clientX;
    const orig = { ...block };
    const colW = gridRef.current.querySelector(".cal-col").offsetWidth;
    let moved = false;
    function move(ev) {
      const dy = ev.clientY - startY, dx = ev.clientX - startX;
      if (Math.abs(dy) > 3 || Math.abs(dx) > 3) moved = true;
      const dMin = snap(dy / PXMIN);
      const dDay = Math.round(dx / colW);
      const dur = orig.end - orig.start;
      let ns = clamp(orig.start + dMin, DAY_START, DAY_END - dur);
      let nd = clamp(orig.day + dDay, 0, 6);
      setDrag({ id: block.id, day: nd, start: ns, end: ns + dur });
    }
    function up() {
      window.removeEventListener("mousemove", move);
      window.removeEventListener("mouseup", up);
      setDrag((d) => {
        if (d && moved) setBlocks((bs) => bs.map((b) => b.id === d.id ? { ...b, day: d.day, start: d.start, end: d.end } : b));
        return null;
      });
    }
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
  }

  function startResize(e, block, edge) {
    e.stopPropagation(); e.preventDefault();
    const startY = e.clientY;
    const orig = { ...block };
    function move(ev) {
      const dMin = snap((ev.clientY - startY) / PXMIN);
      if (edge === "top") {
        const ns = clamp(orig.start + dMin, DAY_START, orig.end - SNAP);
        setDrag({ id: block.id, day: orig.day, start: ns, end: orig.end });
      } else {
        const ne = clamp(orig.end + dMin, orig.start + SNAP, DAY_END);
        setDrag({ id: block.id, day: orig.day, start: orig.start, end: ne });
      }
    }
    function up() {
      window.removeEventListener("mousemove", move);
      window.removeEventListener("mouseup", up);
      setDrag((d) => {
        if (d) setBlocks((bs) => bs.map((b) => b.id === d.id ? { ...b, start: d.start, end: d.end } : b));
        return null;
      });
    }
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
  }

  /* ------------------------------ actions -------------------------------- */
  const updateBlock = (nb) => setBlocks((bs) => bs.map((b) => b.id === nb.id ? nb : b));
  const delBlock = (b) => { setBlocks((bs) => bs.filter((x) => x.id !== b.id)); setPop(null); setMenu(null); setSel(null); };
  const dupBlock = (b) => setBlocks((bs) => [...bs, { ...b, id: "d" + Date.now(), start: b.end + 5, end: b.end + 5 + (b.end - b.start), status: "service" }]);
  const syncBlock = (b) => { updateBlock({ ...b, status: "synced" }); setPop(null); setMenu(null); };

  const blockMenuItems = (b) => [
    { label: t.blk_open, icon: "eye", onClick: () => openPop(b) },
    { label: t.blk_sync, icon: "sync", disabled: b.status === "synced", onClick: () => syncBlock(b) },
    { divider: true },
    { label: t.blk_edit_issue, icon: "edit", onClick: () => openPop(b) },
    { label: t.blk_duplicate, icon: "copy", onClick: () => dupBlock(b) },
    { label: t.blk_split, icon: "split", onClick: () => splitBlock(b) },
    { divider: true },
    { label: t.blk_delete, icon: "trash", danger: true, onClick: () => delBlock(b) },
  ];
  function splitBlock(b) {
    const mid = Math.round((b.start + b.end) / 2 / SNAP) * SNAP;
    setBlocks((bs) => [
      ...bs.map((x) => x.id === b.id ? { ...x, end: mid } : x),
      { ...b, id: "s" + Date.now(), start: mid, status: "service" },
    ]);
  }
  function openPop(b, anchor) {
    setMenu(null); setSel(b.id);
    setPop({ block: b, anchor: anchor || { x: window.innerWidth / 2, y: 160 } });
  }

  function runSync() {
    setSyncing(true);
    setTimeout(() => {
      setBlocks((bs) => bs.map((b) => b.status === "tempo" ? { ...b, status: "synced" } : b));
      setSyncing(false);
    }, 1400);
  }

  const livePos = (b) => {
    const d = drag && drag.id === b.id ? drag : b;
    return { day: d.day, start: d.start, end: d.end };
  };

  const STATES = ["service", "tempo", "synced"];

  return (
    <div className="cal">
      {/* toolbar */}
      <div className="cal__toolbar">
        <div className="cal__nav">
          <IconBtn name="chevL" variant="outline" size="sm" title="prev" />
          <Btn size="sm" variant="default">{t.today}</Btn>
          <IconBtn name="chevR" variant="outline" size="sm" title="next" />
        </div>
        <div className="cal__range">
          <span className="cal__range-main">1 – 7 {lang === "uk" ? "червня" : "June"}</span>
          <span className="cal__range-sub mono">2026 · W23</span>
        </div>
        <span className="spacer" />
        <div className="cal__totals">
          <div className="cal__total"><span className="muted">{t.cal_total}</span><b className="mono">{SW_HELP.fmtDur(weekTotal)}</b></div>
          <div className="cal__total"><span className="muted">{t.cal_billable}</span><b className="mono">{SW_HELP.fmtDur(billTotal)}</b></div>
        </div>
        <div className="cal__tbsep" />
        <Segmented size="sm" value={variant} onChange={setVariant} options={[
          { value: "basic", label: t.cal_variant_basic },
          { value: "soft", label: t.cal_variant_soft },
          { value: "bold", label: t.cal_variant_bold },
        ]} />
        <IconBtn name="filter" variant="outline" size="sm" active={showFilters} onClick={() => setShowFilters((v) => !v)} title={t.cal_filters} />
        <Btn size="sm" variant="primary" icon="sync" onClick={runSync} disabled={syncing}>
          {syncing ? t.syncing : t.sync_now}
        </Btn>
      </div>

      {/* filters */}
      {showFilters && (
        <div className="cal__filters">
          <div className="cal__fgroup">
            <span className="cal__flabel">{t.cal_projects}</span>
            <div className="cal__chips">
              {P.map((p) => {
                const c = SW_HELP.projectColors(p.hue);
                const on = !hiddenProj.has(p.id);
                return (
                  <button key={p.id} className={`chip ${on ? "is-on" : ""}`} onClick={() => setHiddenProj((s) => toggle(s, p.id))}>
                    <span className="chip__dot" style={{ background: on ? c.base : "var(--text-faint)" }} />
                    {p.name}
                  </button>
                );
              })}
            </div>
          </div>
          <div className="cal__fsep" />
          <div className="cal__fgroup">
            <span className="cal__flabel">{t.cal_status}</span>
            <div className="cal__chips">
              {STATES.map((s) => {
                const m = syncMeta(s); const on = !hiddenState.has(s);
                return (
                  <button key={s} className={`chip ${on ? "is-on" : ""}`} onClick={() => setHiddenState((x) => toggle(x, s))}>
                    <Icon name={m.icon} size={13} />
                    {t[m.shortKey]}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* grid */}
      <div className="cal__scroll">
        <div className="cal__grid" ref={gridRef}>
          {/* time gutter */}
          <div className="cal-gutter">
            <div className="cal-gutter__head" />
            <div className="cal-gutter__body">
              {hours().map((h) => (
                <div key={h} className="cal-gutter__h" style={{ height: HOUR_H }}>
                  <span className="mono">{String(h).padStart(2, "0")}:00</span>
                </div>
              ))}
            </div>
          </div>

          {/* day columns */}
          {WEEK_DATES.map((date, di) => {
            const isToday = di === TODAY_IDX;
            const weekend = di >= 5;
            return (
              <div key={di} className={`cal-col ${isToday ? "is-today" : ""} ${weekend ? "is-weekend" : ""}`}>
                <div className="cal-col__head">
                  <div className="cal-col__day">
                    <span className="cal-col__dow">{t[["mon","tue","wed","thu","fri","sat","sun"][di]]}</span>
                    <span className={`cal-col__date ${isToday ? "is-today" : ""}`}>{date}</span>
                  </div>
                  <span className="cal-col__total mono">{dayTotals[di] ? SW_HELP.fmtDur(dayTotals[di]) : "—"}</span>
                </div>
                <div className="cal-col__body" style={{ height: hours().length * HOUR_H }}
                  onClick={() => { setSel(null); setPop(null); }}>
                  {/* hour lines */}
                  {hours().map((h, i) => <div key={h} className="cal-line" style={{ top: i * HOUR_H }} />)}
                  {/* work-hours band 9-18 */}
                  <div className="cal-work" style={{ top: (9 * 60 - DAY_START) * PXMIN, height: (9 * 60) * PXMIN }} />
                  {/* now line */}
                  {isToday && <div className="cal-now" style={{ top: (NOW_MIN - DAY_START) * PXMIN }}><span /></div>}
                  {/* blocks */}
                  {byDay[di].map((b) => {
                    const pos = livePos(b);
                    if (pos.day !== di) return null;
                    const top = (pos.start - DAY_START) * PXMIN;
                    const h = (pos.end - pos.start) * PXMIN;
                    const lanes = b._lanes || 1, lane = b._lane || 0;
                    const w = lanes > 1 ? `calc((100% - 6px) / ${lanes})` : "calc(100% - 6px)";
                    const left = lanes > 1 ? `calc(${lane} * (100% - 6px) / ${lanes} + 3px)` : "3px";
                    return (
                      <div key={b.id} className="cal-blk-wrap" style={{ top, height: h, left, width: w }}>
                        <CalendarBlock block={b} proj={projById(b.proj)} colors={colorsFor(b.proj)} dark={dark}
                          variant={variant} hPx={h} selected={sel === b.id} dragging={drag && drag.id === b.id}
                          onBodyDown={startBody} onResizeDown={startResize}
                          onClick={(e) => openPop(b, { x: e.clientX, y: e.clientY })}
                          onMore={(e) => setMenu({ block: b, x: e.clientX, y: e.clientY })}
                          onContextMenu={(e) => { e.preventDefault(); setMenu({ block: b, x: e.clientX, y: e.clientY }); }} />
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {pop && <BlockPopover block={blocks.find((b) => b.id === pop.block.id)} proj={projById(pop.block.proj)}
        colors={colorsFor(pop.block.proj)} t={t} anchor={pop.anchor} dark={dark}
        onClose={() => setPop(null)} onChange={updateBlock} onSync={syncBlock} onDelete={delBlock} />}

      {menu && <Menu items={blockMenuItems(menu.block)} x={menu.x} y={menu.y} onClose={() => setMenu(null)} />}
    </div>
  );
}

function hours() { const a = []; for (let h = DAY_START / 60; h < DAY_END / 60; h++) a.push(h); return a; }
function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
function toggle(set, v) { const n = new Set(set); n.has(v) ? n.delete(v) : n.add(v); return n; }

window.CalendarScreen = CalendarScreen;
