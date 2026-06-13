/* =========================================================================
   Sync Work — app shell (sidebar, routing, theme/lang, auth gate)
   ========================================================================= */
const { useState: useStateApp, useEffect: useEffectApp } = React;

function useStored(key, init) {
  const [v, setV] = useStateApp(() => {
    try { const s = localStorage.getItem(key); return s != null ? JSON.parse(s) : init; } catch { return init; }
  });
  useEffectApp(() => { try { localStorage.setItem(key, JSON.stringify(v)); } catch {} }, [key, v]);
  return [v, setV];
}

const ACCENTS = {
  "#2a6fdb": { l: { a: "#2a6fdb", p: "#245fbd", s: "#e9f0fc", i: "#1b4fa0" }, d: { a: "#5a92e8", p: "#6c9eed", s: "#1a2740", i: "#aecbf6" } },
  "#1f8a5b": { l: { a: "#1f8a5b", p: "#1a7a50", s: "#e4f4ec", i: "#13633f" }, d: { a: "#46c485", p: "#5bd095", s: "#13291f", i: "#9fe6c2" } },
  "#6b53d6": { l: { a: "#6b53d6", p: "#5d46c0", s: "#ece9fb", i: "#4a37a0" }, d: { a: "#9c8cf0", p: "#a89af3", s: "#211b3a", i: "#cfc6f8" } },
  "#475569": { l: { a: "#475569", p: "#3b4757", s: "#eef1f5", i: "#2f3b4d" }, d: { a: "#8fa0b8", p: "#9fb0c6", s: "#1c2330", i: "#c4cfde" } },
  "#c2700a": { l: { a: "#c2700a", p: "#a85f08", s: "#fbefdc", i: "#8a4f07" }, d: { a: "#e0a04e", p: "#e8ad60", s: "#2e2414", i: "#f0cd95" } },
};
const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accent": "#2a6fdb",
  "density": "regular",
  "workBand": true,
  "weekends": true
}/*EDITMODE-END*/;

function App() {
  const [authed, setAuthed] = useStored("sw_authed", false);
  const [tw, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [lang, setLang] = useStored("sw_lang", "uk");
  const [theme, setTheme] = useStored("sw_theme", "light");
  const [route, setRoute] = useStored("sw_route", "calendar");
  const [variant, setVariant] = useStored("sw_variant", "soft");
  const [collapsed, setCollapsed] = useStored("sw_nav_collapsed", false);
  const t = SW_I18N[lang];

  useEffectApp(() => { document.documentElement.setAttribute("data-theme", theme); }, [theme]);
  useEffectApp(() => {
    const set = (ACCENTS[tw.accent] || ACCENTS["#2a6fdb"])[theme === "dark" ? "d" : "l"];
    const r = document.documentElement.style;
    r.setProperty("--accent", set.a); r.setProperty("--accent-press", set.p);
    r.setProperty("--accent-soft", set.s); r.setProperty("--accent-ink", set.i);
  }, [tw.accent, theme]);

  if (!authed) {
    return <AuthScreen t={t} lang={lang} setLang={setLang} theme={theme} setTheme={setTheme} onLogin={() => setAuthed(true)} />;
  }

  const dark = theme === "dark";
  const NAV = [
    { section: t.nav_section_track, items: [
      { id: "calendar", label: t.nav_calendar, icon: "calendar" },
    ]},
    { section: t.nav_section_data, items: [
      { id: "timecamp", label: t.nav_timecamp, icon: "clock" },
      { id: "jira", label: t.nav_jira, icon: "inbox" },
      { id: "tempo", label: t.nav_tempo, icon: "sync" },
      { id: "journal", label: t.nav_journal, icon: "activity", badge: 1 },
    ]},
    { section: t.nav_section_admin, items: [
      { id: "users", label: t.nav_users, icon: "users" },
    ]},
  ];

  const screens = {
    calendar: <CalendarScreen t={t} lang={lang} dark={dark} variant={variant} setVariant={setVariant} />,
    timecamp: <TimeCampScreen t={t} lang={lang} dark={dark} />,
    jira: <JiraScreen t={t} lang={lang} dark={dark} />,
    tempo: <TempoScreen t={t} lang={lang} dark={dark} />,
    journal: <JournalScreen t={t} lang={lang} dark={dark} />,
    users: <UsersScreen t={t} lang={lang} dark={dark} />,
  };

  return (
    <div className={`shell ${collapsed ? "is-collapsed" : ""} dens-${tw.density} ${tw.workBand ? "" : "no-workband"} ${tw.weekends ? "" : "no-weekends"}`}>
      <aside className="nav">
        <div className="nav__brand">
          <BrandMark size={26} />
          {!collapsed && <span className="nav__brandname">Sync Work</span>}
          <button className="nav__collapse" onClick={() => setCollapsed((v) => !v)} title="Toggle">
            <Icon name={collapsed ? "chevR" : "chevL"} size={16} />
          </button>
        </div>

        <nav className="nav__menu">
          {NAV.map((grp) => (
            <div key={grp.section} className="nav__group">
              {!collapsed && <div className="nav__section">{grp.section}</div>}
              {grp.items.map((it) => (
                <button key={it.id} className={`nav__item ${route === it.id ? "is-active" : ""}`}
                  onClick={() => setRoute(it.id)} title={collapsed ? it.label : undefined}>
                  <Icon name={it.icon} size={18} />
                  {!collapsed && <span>{it.label}</span>}
                  {!collapsed && it.badge && <span className="nav__badge">{it.badge}</span>}
                  {collapsed && it.badge && <span className="nav__badge nav__badge--dot" />}
                </button>
              ))}
            </div>
          ))}
        </nav>

        <div className="nav__foot">
          <div className="nav__controls">
            {!collapsed && <Segmented size="sm" value={lang} onChange={setLang}
              options={[{ value: "uk", label: "УКР" }, { value: "en", label: "ENG" }]} />}
            <IconBtn name={dark ? "sun" : "moon"} variant="ghost" size="sm"
              onClick={() => setTheme(dark ? "light" : "dark")} title="Theme" />
          </div>
          <UserChip collapsed={collapsed} t={t} onLogout={() => setAuthed(false)} />
        </div>
      </aside>

      <main className="main">{screens[route]}</main>

      <TweaksPanel>
        <TweakSection label={lang === "uk" ? "Акцент" : "Accent"} />
        <TweakColor label={lang === "uk" ? "Колір" : "Color"} value={tw.accent}
          options={["#2a6fdb", "#1f8a5b", "#6b53d6", "#475569", "#c2700a"]}
          onChange={(v) => setTweak("accent", v)} />
        <TweakSection label={lang === "uk" ? "Щільність" : "Density"} />
        <TweakRadio label={lang === "uk" ? "Інтерфейс" : "Layout"} value={tw.density}
          options={["compact", "regular"]} onChange={(v) => setTweak("density", v)} />
        <TweakSection label={lang === "uk" ? "Календар" : "Calendar"} />
        <TweakToggle label={lang === "uk" ? "Смуга робочих годин" : "Work-hours band"} value={tw.workBand}
          onChange={(v) => setTweak("workBand", v)} />
        <TweakToggle label={lang === "uk" ? "Показувати вихідні" : "Show weekends"} value={tw.weekends}
          onChange={(v) => setTweak("weekends", v)} />
      </TweaksPanel>
    </div>
  );
}

function UserChip({ collapsed, t, onLogout }) {
  const [open, setOpen] = useStateApp(false);
  const u = SW_DATA.USERS[0];
  return (
    <div className="userchip" style={{ position: "relative" }}>
      <button className="userchip__btn" onClick={() => setOpen((v) => !v)}>
        <Avatar initials={u.initials} hue={u.hue} size={30} />
        {!collapsed && (
          <span className="userchip__info">
            <span className="userchip__name">{u.name}</span>
            <span className="userchip__key mono">{u.worker_key}</span>
          </span>
        )}
        {!collapsed && <Icon name="chevUp" size={14} />}
      </button>
      {open && (
        <Menu onClose={() => setOpen(false)} items={[
          { label: t.profile, icon: "user" },
          { label: t.settings, icon: "settings" },
          { divider: true },
          { label: t.logout, icon: "logout", danger: true, onClick: onLogout },
        ]} />
      )}
    </div>
  );
}

/* placeholders — replaced by real screens once tables.jsx etc. load */
function Stub({ title }) { return <div style={{ padding: 40 }}><h2>{title}</h2><p className="muted">Coming up next.</p></div>; }
window.TimeCampScreen = window.TimeCampScreen || (() => <Stub title="TimeCamp" />);
window.JiraScreen = window.JiraScreen || (() => <Stub title="Jira" />);
window.TempoScreen = window.TempoScreen || (() => <Stub title="Tempo" />);
window.JournalScreen = window.JournalScreen || (() => <Stub title="Journal" />);
window.UsersScreen = window.UsersScreen || (() => <Stub title="Users" />);

window.SyncWorkApp = App;
