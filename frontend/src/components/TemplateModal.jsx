import { useState } from "react";
import { api } from "../api";

const CHANNEL_NAMES = { whatsapp: "WhatsApp", email: "Email", webpush: "Web Push" };

// Popup to create or edit one template.
export default function TemplateModal({ template, triggerName, variables, onClose, onSaved }) {
  const [form, setForm] = useState(template);
  const [error, setError] = useState("");
  const isNew = !template.id;

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  async function save(e) {
    e.preventDefault();
    try {
      const body = { trigger: form.trigger, channel: form.channel, enabled: form.enabled,
        subject: form.subject || "", title: form.title || "", body: form.body };
      if (isNew) await api("/admin/templates/", { method: "POST", body });
      else await api(`/admin/templates/${form.id}/`, { method: "PATCH", body });
      onSaved();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="overlay" onClick={onClose}>
      <form className="card modal" onClick={(e) => e.stopPropagation()} onSubmit={save}>
        <h2>
          {isNew ? "Create" : "Edit"} {CHANNEL_NAMES[form.channel]} template · {triggerName}
        </h2>

        {form.channel === "email" && (
          <>
            <label>Subject</label>
            <input value={form.subject || ""} onChange={update("subject")} required />
          </>
        )}
        {form.channel === "webpush" && (
          <>
            <label>Title</label>
            <input value={form.title || ""} onChange={update("title")} required />
          </>
        )}

        <label>Message</label>
        <textarea rows={5} value={form.body} onChange={update("body")} required />

        <p className="muted">
          Variables you can use: {Object.keys(variables).map((v) => <code key={v}>{`{{${v}}}`} </code>)}
        </p>
        {form.channel === "whatsapp" && (
          <p className="muted">
            After saving, press <b>Sync</b> to send it to Meta for approval, and again until it says
            APPROVED. Editing the text needs a new approval. Meta rules: no variable at the very start or
            end of the message, and avoid "login" / "password" wording (Meta rejects it as the wrong category).
          </p>
        )}
        {form.channel === "webpush" && (
          <div className="platforms">
            <label>Platforms</label>
            <label className="switch"><input type="checkbox" checked readOnly /> Web browsers</label>
            <label className="switch"><input type="checkbox" checked={false} disabled /> iOS (off — web push only)</label>
            <label className="switch"><input type="checkbox" checked={false} disabled /> Android (off — web push only)</label>
          </div>
        )}

        {error && <p className="error">{error}</p>}
        <div className="actions">
          <button type="button" onClick={onClose}>Cancel</button>
          <button className="primary">Save</button>
        </div>
      </form>
    </div>
  );
}
