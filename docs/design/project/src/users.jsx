/* =========================================================================
   Sync Work — Users management (admin creates accounts; no self sign-up)
   ========================================================================= */
const { useState: useStateU } = React;

function UsersScreen({ t, lang, dark }) {
  const [users, setUsers] = useStateU(() => SW_DATA.USERS.map((u) => ({ ...u })));
  const [adding, setAdding] = useStateU(false);
  const [menuId, setMenuId] = useStateU(null);
  const [draft, setDraft] = useStateU({ name: "", email: "", worker_key: "", role: "member" });

  const tog = (id) => setUsers((us) => us.map((u) => u.id === id ? { ...u, active: !u.active } : u));
  const remove = (id) => setUsers((us) => us.filter((u) => u.id !== id));
  const add = () => {
    if (!draft.name.trim()) return;
    const initials = draft.name.split(" ").map((s) => s[0]).join("").slice(0, 2).toUpperCase();
    setUsers((us) => [...us, { ...draft, id: Date.now(), active: true, last_seen: "—", initials, hue: 120 + Math.random() * 200 }]);
    setDraft({ name: "", email: "", worker_key: "", role: "member" });
    setAdding(false);
  };

  const roleBadge = (role) => {
    const tone = role === "admin" ? "accent" : role === "viewer" ? "neutral" : "green";
    const label = role === "admin" ? t.user_role_admin : role === "viewer" ? t.user_role_viewer : t.user_role_member;
    return <Badge tone={tone} soft={role !== "admin"}>{label}</Badge>;
  };

  const cols = [
    { key: "name", label: t.user_full_name, render: (r) => (
      <div className="dt-name">
        <Avatar initials={r.initials} hue={r.hue} size={30} />
        <div className="user-name">
          <span>{r.name}</span>
          <span className="muted">{r.email}</span>
        </div>
      </div>
    ) },
    { key: "worker_key", label: t.user_worker_key, width: 150, render: (r) => <span className="mono key-pill">{r.worker_key}</span> },
    { key: "role", label: t.col_role, width: 120, render: (r) => roleBadge(r.role) },
    { key: "last_seen", label: t.col_last_seen, width: 130, render: (r) => <span className="muted">{r.last_seen}</span> },
    { key: "active", label: "", align: "right", width: 90, render: (r) => <Toggle size="sm" checked={r.active} onChange={() => tog(r.id)} /> },
    { key: "act", label: "", align: "right", width: 44, render: (r) => (
      <span style={{ position: "relative" }}>
        <IconBtn name="dots" size="sm" onClick={(e) => { e.stopPropagation(); setMenuId(menuId === r.id ? null : r.id); }} />
        {menuId === r.id && <Menu onClose={() => setMenuId(null)} items={[
          { label: t.blk_edit_issue.replace("…", ""), icon: "edit" },
          { label: r.active ? t.user_disabled : t.user_active, icon: r.active ? "lock" : "check", onClick: () => tog(r.id) },
          { divider: true },
          { label: t.blk_delete, icon: "trash", danger: true, onClick: () => remove(r.id) },
        ]} />}
      </span>
    ) },
  ];

  return (
    <div className="page">
      <PageHeader title={t.users_title} desc={t.users_desc} actions={
        <Btn size="sm" variant="primary" icon="plus" onClick={() => setAdding(true)}>{t.users_add}</Btn>
      } />
      <div className="page__body">
        <DataTable columns={cols} rows={users} getId={(r) => r.id} />
      </div>

      <Sheet open={adding} onClose={() => setAdding(false)} title={t.users_add} width={400}>
        <div className="userform">
          <Field label={t.user_full_name}><input className="sw-input" value={draft.name} placeholder="Ім'я Прізвище"
            onChange={(e) => setDraft({ ...draft, name: e.target.value })} /></Field>
          <Field label={t.col_email}><input className="sw-input" value={draft.email} placeholder="name@leadsdoit.io"
            onChange={(e) => setDraft({ ...draft, email: e.target.value })} /></Field>
          <Field label={t.user_worker_key} hint="Jira key (APP__CURRENT_USER)">
            <input className="sw-input mono" value={draft.worker_key} placeholder="i.petrenko"
              onChange={(e) => setDraft({ ...draft, worker_key: e.target.value })} /></Field>
          <Field label={t.col_role}>
            <Segmented value={draft.role} onChange={(v) => setDraft({ ...draft, role: v })} options={[
              { value: "admin", label: t.user_role_admin },
              { value: "member", label: t.user_role_member },
              { value: "viewer", label: t.user_role_viewer },
            ]} />
          </Field>
          <div className="userform__note"><Icon name="lock" size={13} /><span>{t.users_desc}</span></div>
          <div className="userform__foot">
            <Btn variant="default" onClick={() => setAdding(false)}>{t.blk_cancel}</Btn>
            <Btn variant="primary" icon="plus" onClick={add}>{t.users_invite}</Btn>
          </div>
        </div>
      </Sheet>
    </div>
  );
}

window.UsersScreen = UsersScreen;
