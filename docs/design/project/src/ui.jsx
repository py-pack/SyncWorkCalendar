/* =========================================================================
   Sync Work — shared UI primitives + icon set
   Exposes on window: Icon, Btn, IconBtn, Badge, Toggle, Segmented, Avatar,
   Tooltip, Menu, Sheet, Spinner, Field, Checkbox, useClickOutside
   ========================================================================= */
const { useState, useEffect, useRef, useCallback } = React;

/* ------------------------------- icons -------------------------------- */
const ICONS = {
  calendar: "M7 3v3M17 3v3M4 8h16M5 6h14a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1Z",
  table: "M4 5h16v14H4zM4 10h16M4 15h16M9.5 5v14M14.5 5v14",
  list: "M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01",
  activity: "M3 12h4l2 6 4-14 2 8h6",
  users: "M16 18v-1a3 3 0 0 0-3-3H7a3 3 0 0 0-3 3v1M10 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7ZM20 18v-1a3 3 0 0 0-2.2-2.9M15.5 4.2a3.5 3.5 0 0 1 0 6.6",
  sync: "M4 7a8 8 0 0 1 13.5-3L20 6M20 4v4h-4M20 17a8 8 0 0 1-13.5 3L4 18M4 20v-4h4",
  check: "M5 12.5l4.5 4.5L19 7.5",
  checkCircle: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18ZM8.5 12l2.5 2.5L15.5 9.5",
  clock: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18ZM12 7.5V12l3 2",
  cloudDown: "M7 18a4 4 0 0 1-.5-7.97A5.5 5.5 0 0 1 17.5 9.5 3.75 3.75 0 0 1 17 18M12 12v6M12 18l-2.5-2.5M12 18l2.5-2.5",
  chevL: "M14 6l-6 6 6 6",
  chevR: "M10 6l6 6-6 6",
  chevD: "M6 9l6 6 6-6",
  chevUp: "M6 15l6-6 6 6",
  plus: "M12 5v14M5 12h14",
  x: "M6 6l12 12M18 6L6 18",
  search: "M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14ZM20 20l-3.5-3.5",
  filter: "M4 5h16l-6 7v6l-4 2v-8L4 5Z",
  sun: "M12 4V2M12 22v-2M4 12H2M22 12h-2M6 6 4.5 4.5M19.5 19.5 18 18M18 6l1.5-1.5M4.5 19.5 6 18M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z",
  moon: "M20 13.5A8 8 0 1 1 10.5 4a6.5 6.5 0 0 0 9.5 9.5Z",
  google: "G",
  lock: "M7 11V8a5 5 0 0 1 10 0v3M5 11h14a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-7a1 1 0 0 1 1-1Z",
  user: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM5 20a7 7 0 0 1 14 0",
  dots: "M12 6h.01M12 12h.01M12 18h.01",
  dotsH: "M6 12h.01M12 12h.01M18 12h.01",
  drag: "M9 6h.01M9 12h.01M9 18h.01M15 6h.01M15 12h.01M15 18h.01",
  trash: "M5 7h14M10 7V5a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v2M6 7l1 13a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-13",
  edit: "M4 20h4L19 9l-4-4L4 16v4ZM14 6l4 4",
  link: "M9 15l6-6M10 7l1-1a4 4 0 0 1 6 6l-1 1M14 17l-1 1a4 4 0 0 1-6-6l1-1",
  split: "M6 4v6a3 3 0 0 0 3 3h9M18 9l3 4-3 4M6 20v-4",
  copy: "M9 9h9a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1v-9a1 1 0 0 1 1-1ZM5 15H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v1",
  alert: "M12 3 2 20h20L12 3ZM12 10v4M12 18h.01",
  logout: "M15 4h3a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1h-3M10 12h9M16 9l3 3-3 3",
  settings: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM19 12a7 7 0 0 0-.1-1.2l2-1.6-2-3.4-2.3 1a7 7 0 0 0-2-1.2l-.3-2.5h-4l-.3 2.5a7 7 0 0 0-2 1.2l-2.3-1-2 3.4 2 1.6A7 7 0 0 0 5 12a7 7 0 0 0 .1 1.2l-2 1.6 2 3.4 2.3-1a7 7 0 0 0 2 1.2l.3 2.5h4l.3-2.5a7 7 0 0 0 2-1.2l2.3 1 2-3.4-2-1.6A7 7 0 0 0 19 12Z",
  globe: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18ZM3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18",
  eye: "M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z",
  arrowRight: "M5 12h14M13 6l6 6-6 6",
  external: "M14 4h6v6M20 4l-8 8M18 14v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4",
  bolt: "M13 2 4 14h6l-1 8 9-12h-6l1-8Z",
  inbox: "M3 13h4l2 3h6l2-3h4M3 13l3-8h12l3 8v6a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1v-6Z",
};

function Icon({ name, size = 18, stroke = 1.6, fill = false, style, className }) {
  if (name === "google") {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" style={style} className={className}>
        <path fill="#4285F4" d="M22 12.2c0-.7-.1-1.4-.2-2H12v3.8h5.6a4.8 4.8 0 0 1-2.1 3.2v2.6h3.4c2-1.8 3.1-4.5 3.1-7.6Z"/>
        <path fill="#34A853" d="M12 22c2.7 0 5-.9 6.7-2.4l-3.4-2.6c-.9.6-2.1 1-3.3 1-2.6 0-4.7-1.7-5.5-4.1H3v2.6A10 10 0 0 0 12 22Z"/>
        <path fill="#FBBC05" d="M6.5 13.9a6 6 0 0 1 0-3.8V7.5H3a10 10 0 0 0 0 9l3.5-2.6Z"/>
        <path fill="#EA4335" d="M12 6.1c1.5 0 2.8.5 3.8 1.5l2.9-2.9A10 10 0 0 0 3 7.5l3.5 2.6C7.3 7.8 9.4 6.1 12 6.1Z"/>
      </svg>
    );
  }
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill={fill ? "currentColor" : "none"}
      stroke="currentColor" strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round"
      style={style} className={className}>
      <path d={ICONS[name] || ""} />
    </svg>
  );
}

/* --------------------------- click outside ---------------------------- */
function useClickOutside(ref, handler) {
  useEffect(() => {
    function onDown(e) {
      if (ref.current && !ref.current.contains(e.target)) handler(e);
    }
    document.addEventListener("mousedown", onDown);
    document.addEventListener("touchstart", onDown);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("touchstart", onDown);
    };
  }, [ref, handler]);
}

/* ------------------------------ button -------------------------------- */
function Btn({ children, variant = "default", size = "md", icon, iconRight, onClick, disabled, active, full, title, type }) {
  const cls = ["sw-btn", `sw-btn--${variant}`, `sw-btn--${size}`];
  if (active) cls.push("is-active");
  if (full) cls.push("is-full");
  return (
    <button type={type || "button"} className={cls.join(" ")} onClick={onClick} disabled={disabled} title={title}>
      {icon && <Icon name={icon} size={size === "sm" ? 15 : 17} />}
      {children && <span>{children}</span>}
      {iconRight && <Icon name={iconRight} size={size === "sm" ? 15 : 17} />}
    </button>
  );
}
function IconBtn({ name, onClick, title, active, size = "md", variant = "ghost", badge }) {
  const cls = ["sw-iconbtn", `sw-iconbtn--${variant}`, `sw-iconbtn--${size}`];
  if (active) cls.push("is-active");
  return (
    <button type="button" className={cls.join(" ")} onClick={onClick} title={title}>
      <Icon name={name} size={size === "sm" ? 16 : 18} />
      {badge != null && <span className="sw-iconbtn__badge">{badge}</span>}
    </button>
  );
}

/* ------------------------------ badge --------------------------------- */
function Badge({ children, tone = "neutral", dot, soft, icon }) {
  const cls = ["sw-badge", `sw-badge--${tone}`];
  if (soft) cls.push("is-soft");
  return (
    <span className={cls.join(" ")}>
      {dot && <span className="sw-badge__dot" />}
      {icon && <Icon name={icon} size={12} />}
      {children}
    </span>
  );
}

/* ------------------------------ toggle -------------------------------- */
function Toggle({ checked, onChange, size = "md" }) {
  return (
    <button type="button" className={`sw-toggle sw-toggle--${size} ${checked ? "is-on" : ""}`}
      onClick={() => onChange && onChange(!checked)} role="switch" aria-checked={checked}>
      <span className="sw-toggle__knob" />
    </button>
  );
}
function Checkbox({ checked, indeterminate, onChange }) {
  const ref = useRef(null);
  useEffect(() => { if (ref.current) ref.current.indeterminate = !!indeterminate; }, [indeterminate]);
  return (
    <span className={`sw-check ${checked ? "is-on" : ""} ${indeterminate ? "is-ind" : ""}`}
      onClick={(e) => { e.stopPropagation(); onChange && onChange(!checked); }}>
      {checked && !indeterminate && <Icon name="check" size={12} stroke={2.4} />}
      {indeterminate && <span className="sw-check__dash" />}
      <input ref={ref} type="checkbox" checked={checked} readOnly style={{ display: "none" }} />
    </span>
  );
}

/* ----------------------------- segmented ------------------------------ */
function Segmented({ value, onChange, options, size = "md" }) {
  return (
    <div className={`sw-seg sw-seg--${size}`}>
      {options.map((o) => (
        <button key={o.value} type="button"
          className={`sw-seg__opt ${value === o.value ? "is-active" : ""}`}
          onClick={() => onChange(o.value)} title={o.title}>
          {o.icon && <Icon name={o.icon} size={15} />}
          {o.label && <span>{o.label}</span>}
        </button>
      ))}
    </div>
  );
}

/* ------------------------------ avatar -------------------------------- */
function Avatar({ initials, hue = 220, size = 30 }) {
  return (
    <span className="sw-avatar" style={{
      width: size, height: size, fontSize: size * 0.38,
      background: `oklch(0.92 0.04 ${hue})`, color: `oklch(0.42 0.13 ${hue})`,
    }}>{initials}</span>
  );
}

/* ------------------------------- menu --------------------------------- */
function Menu({ items, onClose, x, y, anchorRef }) {
  const ref = useRef(null);
  useClickOutside(ref, onClose);
  useEffect(() => {
    function esc(e) { if (e.key === "Escape") onClose(); }
    document.addEventListener("keydown", esc);
    return () => document.removeEventListener("keydown", esc);
  }, [onClose]);
  let style = {};
  if (x != null) {
    const mx = Math.min(x, window.innerWidth - 240);
    const my = Math.min(y, window.innerHeight - (items.length * 38 + 16));
    style = { position: "fixed", left: mx, top: my };
  }
  return (
    <div ref={ref} className="sw-menu" style={style} onClick={(e) => e.stopPropagation()}>
      {items.map((it, i) =>
        it.divider ? <div key={i} className="sw-menu__div" /> : (
          <button key={i} className={`sw-menu__item ${it.danger ? "is-danger" : ""}`}
            onClick={() => { it.onClick && it.onClick(); onClose(); }} disabled={it.disabled}>
            {it.icon && <Icon name={it.icon} size={16} />}
            <span>{it.label}</span>
            {it.hint && <span className="sw-menu__hint">{it.hint}</span>}
          </button>
        )
      )}
    </div>
  );
}

/* ------------------------------- sheet -------------------------------- */
function Sheet({ open, onClose, children, title, width = 380, side = "right" }) {
  if (!open) return null;
  return (
    <div className="sw-sheet-overlay" onMouseDown={onClose}>
      <div className={`sw-sheet sw-sheet--${side}`} style={{ width }} onMouseDown={(e) => e.stopPropagation()}>
        {title && (
          <div className="sw-sheet__head">
            <div className="sw-sheet__title">{title}</div>
            <IconBtn name="x" size="sm" onClick={onClose} />
          </div>
        )}
        <div className="sw-sheet__body">{children}</div>
      </div>
    </div>
  );
}

/* ------------------------------ spinner ------------------------------- */
function Spinner({ size = 16 }) {
  return <span className="sw-spinner" style={{ width: size, height: size }} />;
}

/* ------------------------------ field --------------------------------- */
function Field({ label, children, hint }) {
  return (
    <label className="sw-field">
      {label && <span className="sw-field__label">{label}</span>}
      {children}
      {hint && <span className="sw-field__hint">{hint}</span>}
    </label>
  );
}

Object.assign(window, {
  Icon, Btn, IconBtn, Badge, Toggle, Checkbox, Segmented, Avatar, Menu,
  Sheet, Spinner, Field, useClickOutside,
});
