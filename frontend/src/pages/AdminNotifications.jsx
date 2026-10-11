import { useEffect, useState } from "react";
import { api } from "../api";
import TemplateCell from "../components/TemplateCell";
import TemplateModal from "../components/TemplateModal";

const CHANNELS = [
  { key: "whatsapp", name: "WhatsApp" },
  { key: "email", name: "Email" },
  { key: "webpush", name: "Web Push" },
];

// Admin "Notification Settings": rows = triggers, columns = channels.
export default function AdminNotifications() {
  const [triggers, setTriggers] = useState([]);
  const [logs, setLogs] = useState([]);
  const [variables, setVariables] = useState({});
  const [editing, setEditing] = useState(null); // template being created / edited
  const [newTrigger, setNewTrigger] = useState({ key: "", name: "", description: "" });
  const [notice, setNotice] = useState(null);
  // Where "Test" sends go. Empty = the admin's own profile email / phone.
  const [testTo, setTestTo] = useState({ email: "", phone: "" });

  async function load() {
    setTriggers(await api("/admin/triggers/"));
    setLogs(await api("/admin/logs/"));
  }

  useEffect(() => {
    load();
    api("/admin/variables/").then(setVariables);
  }, []);

  const notify = (text, ok) => setNotice({ text, ok });

  async function addTrigger(e) {
    e.preventDefault();
    try {
      await api("/admin/triggers/", { method: "POST", body: newTrigger });
      setNewTrigger({ key: "", name: "", description: "" });
      load();
    } catch (err) {
      notify(err.message, false);
    }
  }

  async function renameTrigger(trigger) {
    const name = prompt("Trigger name", trigger.name);
    if (!name) return;
    const description = prompt("When does it fire?", trigger.description) ?? trigger.description;
    await api(`/admin/triggers/${trigger.id}/`, { method: "PATCH", body: { name, description } });
    load();
  }

  async function deleteTrigger(trigger) {
    if (!confirm(`Delete trigger "${trigger.name}" and its templates?`)) return;
    await api(`/admin/triggers/${trigger.id}/`, { method: "DELETE" });
    load();
  }

  async function runInactivityCheck() {
    const { notified } = await api("/admin/run-inactivity-check/", { method: "POST" });
    notify(`Inactivity check done: ${notified} user(s) notified`, true);
    load();
  }

  const editingTrigger = editing && triggers.find((t) => t.id === editing.trigger);

  return (
    <div>
      <div className="header-row">
        <h1>Notification Settings</h1>
        <button onClick={runInactivityCheck}>Run "not logged in" check now</button>
      </div>
      <div className="card inline-form">
        <h3>Send tests to</h3>
        <input placeholder="Email (empty = your account email)" type="email" value={testTo.email}
          onChange={(e) => setTestTo({ ...testTo, email: e.target.value })} />
        <input placeholder="WhatsApp number, e.g. 919876543210 (empty = your profile)" value={testTo.phone}
          onChange={(e) => setTestTo({ ...testTo, phone: e.target.value })} />
        <p className="muted">Web Push tests go to this browser — enable push in "My account" first.</p>
      </div>
      {notice && (
        <p className={notice.ok ? "success" : "error"} onClick={() => setNotice(null)}>{notice.text}</p>
      )}

      <div className="table-wrap">
        <table className="settings">
          <thead>
            <tr>
              <th>Trigger</th>
              {CHANNELS.map((c) => <th key={c.key}>{c.name}</th>)}
            </tr>
          </thead>
          <tbody>
            {triggers.map((trigger) => (
              <tr key={trigger.id}>
                <td className="trigger">
                  <b>{trigger.name}</b>
                  <code>{trigger.key}</code>
                  <span className="muted">{trigger.description}</span>
                  <span>
                    <button className="link edit" onClick={() => renameTrigger(trigger)}>Rename</button>
                    {" · "}
                    <button className="link" onClick={() => deleteTrigger(trigger)}>Delete</button>
                  </span>
                </td>
                {CHANNELS.map((c) => (
                  <TemplateCell
                    key={c.key}
                    trigger={trigger}
                    channel={c.key}
                    template={trigger.templates[c.key]}
                    onEdit={setEditing}
                    onChange={load}
                    notify={notify}
                    testTo={testTo}
                  />
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <form className="card inline-form" onSubmit={addTrigger}>
        <h3>Add a trigger</h3>
        <input placeholder="key, e.g. cart_abandoned" value={newTrigger.key}
          onChange={(e) => setNewTrigger({ ...newTrigger, key: e.target.value })} required />
        <input placeholder="Name, e.g. Cart abandoned" value={newTrigger.name}
          onChange={(e) => setNewTrigger({ ...newTrigger, name: e.target.value })} required />
        <input placeholder="When it fires" value={newTrigger.description}
          onChange={(e) => setNewTrigger({ ...newTrigger, description: e.target.value })} />
        <button className="primary">Add</button>
      </form>

      <h2>Recent sends</h2>
      <div className="table-wrap">
        <table className="logs">
          <thead>
            <tr><th>Time</th><th>Trigger</th><th>Channel</th><th>To</th><th>Result</th></tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id}>
                <td>{new Date(log.created_at).toLocaleString()}</td>
                <td>{log.trigger} {log.is_test && <span className="badge">test</span>}</td>
                <td>{log.channel}</td>
                <td>{log.recipient}</td>
                <td className={log.success ? "success" : "error"} title={log.response}>
                  {log.success ? "Sent" : "Failed"} — {log.response.slice(0, 80)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editing && (
        <TemplateModal
          template={editing}
          triggerName={editingTrigger?.name}
          variables={variables}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            load();
          }}
        />
      )}
    </div>
  );
}
