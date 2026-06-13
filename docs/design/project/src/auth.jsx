/* =========================================================================
   Sync Work — auth screen (login/password + Google)
   ========================================================================= */
const { useState: useStateA } = React;

function AuthScreen({ t, lang, setLang, theme, setTheme, onLogin }) {
  const [email, setEmail] = useStateA("i.petrenko@leadsdoit.io");
  const [pass, setPass] = useStateA("");
  const [remember, setRemember] = useStateA(true);
  const [loading, setLoading] = useStateA(null);

  const submit = (mode) => {
    if (loading) return;
    setLoading(mode);
    setTimeout(() => onLogin(), 850);
  };

  return (
    <div className="auth">
      <div className="auth__bg" aria-hidden="true">
        <div className="auth__grid" />
      </div>

      <div className="auth__topbar">
        <div className="auth__brand">
          <BrandMark size={22} />
          <span>Sync Work</span>
        </div>
        <div className="row" style={{ gap: 8 }}>
          <Segmented size="sm" value={lang} onChange={setLang}
            options={[{ value: "uk", label: "УКР" }, { value: "en", label: "ENG" }]} />
          <IconBtn variant="outline" name={theme === "dark" ? "sun" : "moon"}
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")} />
        </div>
      </div>

      <div className="auth__card-wrap">
        <div className="auth__card">
          <div className="auth__head">
            <BrandMark size={34} />
            <h1>{t.app_name}</h1>
            <p className="auth__sub">{t.auth_subtitle}</p>
            <div className="auth__tag mono">{t.auth_tagline}</div>
          </div>

          <form className="auth__form" onSubmit={(e) => { e.preventDefault(); submit("pass"); }}>
            <Field label={t.auth_email}>
              <input className="sw-input" value={email} onChange={(e) => setEmail(e.target.value)}
                autoComplete="username" placeholder="name@leadsdoit.io" />
            </Field>
            <Field label={t.auth_password}>
              <input className="sw-input" type="password" value={pass} onChange={(e) => setPass(e.target.value)}
                autoComplete="current-password" placeholder="••••••••" />
            </Field>
            <div className="auth__row">
              <label className="auth__remember">
                <Checkbox checked={remember} onChange={setRemember} />
                <span>{t.auth_remember}</span>
              </label>
              <a className="auth__link" href="#" onClick={(e) => e.preventDefault()}>{t.auth_forgot}</a>
            </div>
            <Btn variant="primary" size="lg" full type="submit" disabled={!!loading}>
              {loading === "pass" ? <Spinner size={17} /> : t.auth_signin}
            </Btn>
          </form>

          <div className="auth__or"><span>{t.auth_or}</span></div>

          <button className="auth__google" onClick={() => submit("google")} disabled={!!loading}>
            {loading === "google" ? <Spinner size={17} /> : <Icon name="google" size={18} />}
            <span>{t.auth_google}</span>
          </button>

          <div className="auth__note">
            <Icon name="lock" size={13} />
            <span>{t.auth_no_signup}</span>
          </div>
        </div>
        <div className="auth__hint mono">{t.auth_hint}</div>
      </div>
    </div>
  );
}

function BrandMark({ size = 28 }) {
  return (
    <span className="brandmark" style={{ width: size, height: size }}>
      <svg viewBox="0 0 32 32" width={size} height={size}>
        <rect x="1" y="1" width="30" height="30" rx="8" fill="var(--accent)" />
        <path d="M9 11.5a5 5 0 0 1 8.5-2l1.5 1.5M19 9v3.5h-3.5" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M23 20.5a5 5 0 0 1-8.5 2L13 21M13 23v-3.5h3.5" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </span>
  );
}

window.AuthScreen = AuthScreen;
window.BrandMark = BrandMark;
