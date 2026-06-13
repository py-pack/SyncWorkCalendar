/* =========================================================================
   Sync Work — calendar block + sync-state meta + detail popover
   Exposes: CalendarBlock, BlockPopover, SYNC_META, syncMeta
   ========================================================================= */
const { useState: useStateB, useRef: useRefB, useEffect: useEffectB } = React;

const SYNC_META = {
  service: { icon: "cloudDown", tone: "neutral", border: "dashed", labelKey: "st_service", shortKey: "st_service_short" },
  tempo:   { icon: "clock",     tone: "amber",   border: "solid",  labelKey: "st_tempo",   shortKey: "st_tempo_short" },
  synced:  { icon: "check",     tone: "green",   border: "double", labelKey: "st_synced",  shortKey: "st_synced_short" },
};
const syncMeta = (s) => SYNC_META[s] || SYNC_META.service;

/* state pill shown in the block corner */
function StateChip({ state, variant }) {
  const m = syncMeta(state);
  return (
    <span className={`blk-state blk-state--${state} blk-state--${variant}`} title={state}>
      <Icon name={m.icon} size={12} stroke={2} fill={state === "synced"} />
    </span>
  );
}

function CalendarBlock({
  block, proj, colors, dark, variant, hPx, selected, dimmed, dragging,
  onBodyDown, onResizeDown, onContextMenu, onMore, onClick,
}) {
  const m = syncMeta(block.status);
  const compact = hPx < 46;
  const tiny = hPx < 30;
  const dur = block.end - block.start;

  // per-variant container styles
  let style = { };
  let cls = ["blk", `blk--${variant}`, `blk--${block.status}`];
  if (selected) cls.push("is-selected");
  if (dimmed) cls.push("is-dimmed");
  if (dragging) cls.push("is-dragging");
  if (compact) cls.push("is-compact");

  if (variant === "basic") {
    style.background = dark ? colors.softDark : colors.base;
    style.color = dark ? colors.inkLight : "#fff";
    style["--blk-edge"] = dark ? colors.inkLight : "rgba(255,255,255,.85)";
    style["--blk-line"] = dark ? "rgba(255,255,255,.14)" : "rgba(255,255,255,.28)";
  } else if (variant === "soft") {
    style.background = dark ? colors.softDark : colors.soft;
    style.color = dark ? colors.inkLight : colors.ink;
    style["--blk-edge"] = colors.base;
    style["--blk-line"] = dark ? "rgba(255,255,255,.08)" : "rgba(0,0,0,.06)";
    style.borderLeft = `3px solid ${colors.base}`;
  } else { // bold
    style.background = dark
      ? `linear-gradient(160deg, ${colors.softDark}, color-mix(in oklch, ${colors.softDark}, #000 22%))`
      : `linear-gradient(160deg, ${colors.base}, ${colors.strong})`;
    style.color = dark ? colors.inkLight : "#fff";
    style["--blk-edge"] = dark ? colors.inkLight : "#fff";
    style["--blk-line"] = dark ? "rgba(255,255,255,.12)" : "rgba(255,255,255,.22)";
  }

  return (
    <div className={cls.join(" ")} style={style}
      onMouseDown={(e) => onBodyDown && onBodyDown(e, block)}
      onClick={(e) => { e.stopPropagation(); onClick && onClick(e, block); }}
      onContextMenu={(e) => onContextMenu && onContextMenu(e, block)}>

      {/* resize handles */}
      <div className="blk__rz blk__rz--top" onMouseDown={(e) => onResizeDown && onResizeDown(e, block, "top")} />
      <div className="blk__rz blk__rz--bot" onMouseDown={(e) => onResizeDown && onResizeDown(e, block, "bot")} />

      {variant === "bold" && <div className={`blk__ribbon blk__ribbon--${block.status}`} />}

      <div className="blk__top">
        <span className="blk__time mono">{SW_HELP.fmtSpan(block.start, block.end)}</span>
        <span className="blk__corner">
          <StateChip state={block.status} variant={variant} />
          {!tiny && (
            <button className="blk__more" onClick={(e) => { e.stopPropagation(); onMore && onMore(e, block); }} title="…">
              <Icon name="dots" size={13} />
            </button>
          )}
        </span>
      </div>

      {!compact && (
        <div className="blk__body">
          <div className="blk__title">{block.title}</div>
          <div className="blk__meta">
            <span className="blk__key mono">{block.issue}</span>
            <span className="blk__dot">·</span>
            <span className="blk__proj">{proj.name}</span>
          </div>
        </div>
      )}

      <div className="blk__foot">
        <span className="blk__dur mono">{SW_HELP.fmtDur(dur)}</span>
        {!compact && <span className="blk__projcat">{proj.cat}</span>}
      </div>
    </div>
  );
}

/* ---------------------- detail popover (click) ----------------------- */
function BlockPopover({ block, proj, colors, t, anchor, onClose, onChange, onSync, onDelete, dark }) {
  const ref = useRefB(null);
  useClickOutside(ref, onClose);
  useEffectB(() => {
    const esc = (e) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", esc);
    return () => document.removeEventListener("keydown", esc);
  }, []);
  if (!block) return null;
  const m = syncMeta(block.status);
  const W = 340, H = 430;
  let left = anchor.x + 14, top = anchor.y - 20;
  if (left + W > window.innerWidth - 12) left = anchor.x - W - 14;
  if (left < 12) left = 12;
  if (top + H > window.innerHeight - 12) top = window.innerHeight - H - 12;
  if (top < 12) top = 12;

  const set = (patch) => onChange({ ...block, ...patch });

  return (
    <div ref={ref} className="pop" style={{ left, top, width: W }}>
      <div className="pop__head" style={{ background: dark ? colors.softDark : colors.soft }}>
        <span className="pop__swatch" style={{ background: colors.base }} />
        <span className="pop__proj">{proj.name}<span className="muted"> · {proj.cat}</span></span>
        <span className="spacer" />
        <IconBtn name="x" size="sm" onClick={onClose} />
      </div>

      <div className="pop__body">
        <div className="pop__times">
          <input className="sw-input pop__t mono" defaultValue={SW_HELP.fmtMin(block.start)}
            onBlur={(e) => { const v = parseT(e.target.value); if (v != null) set({ start: Math.min(v, block.end - 5) }); }} />
          <span className="pop__dash">–</span>
          <input className="sw-input pop__t mono" defaultValue={SW_HELP.fmtMin(block.end)}
            onBlur={(e) => { const v = parseT(e.target.value); if (v != null) set({ end: Math.max(v, block.start + 5) }); }} />
          <span className="pop__durpill mono">{SW_HELP.fmtDur(block.end - block.start)}</span>
        </div>

        <Field label={t.blk_issue}>
          <input className="sw-input mono" value={block.issue} onChange={(e) => set({ issue: e.target.value })} />
        </Field>
        <Field label={t.blk_desc}>
          <textarea className="sw-input" rows={2} value={block.title} onChange={(e) => set({ title: e.target.value })} />
        </Field>

        <div className="pop__rows">
          <div className="pop__r">
            <span className="muted">{t.col_status}</span>
            <Badge tone={m.tone} soft icon={m.icon}>{t[m.labelKey]}</Badge>
          </div>
          <div className="pop__r">
            <span className="muted">{t.blk_billable}</span>
            <Toggle size="sm" checked={block.billable} onChange={(v) => set({ billable: v })} />
          </div>
        </div>
      </div>

      <div className="pop__foot">
        {block.status !== "synced"
          ? <Btn variant="primary" size="sm" icon="sync" onClick={() => onSync(block)}>{t.blk_sync}</Btn>
          : <Badge tone="green" soft icon="check">{t.st_synced}</Badge>}
        <span className="spacer" />
        <IconBtn name="activity" size="sm" title={t.blk_history} />
        <IconBtn name="trash" size="sm" title={t.blk_delete} onClick={() => onDelete(block)} />
      </div>
    </div>
  );
}

function parseT(s) {
  const m = String(s).trim().match(/^(\d{1,2})[:.\s]?(\d{2})?$/);
  if (!m) return null;
  let h = +m[1], mm = m[2] ? +m[2] : 0;
  if (h > 23 || mm > 59) return null;
  return h * 60 + mm;
}

Object.assign(window, { CalendarBlock, BlockPopover, SYNC_META, syncMeta, StateChip });
