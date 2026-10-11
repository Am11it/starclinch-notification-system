import { api } from "../api";

// One cell of the admin table = one template for (trigger, channel).
export default function TemplateCell({ trigger, channel, template, onEdit, onChange, notify, testTo }) {
  if (!template) {
    return (
      <td className="cell empty">
        <button onClick={() => onEdit({ trigger: trigger.id, channel, enabled: true, body: "" })}>
          + Create template
        </button>
      </td>
    );
  }

  async function run(label, request) {
    try {
      const result = await request();
      notify(`${label}: ${result.detail ?? "done"}`, true);
    } catch (err) {
      notify(`${label} failed: ${err.message}`, false);
    }
    onChange();
  }

  const toggle = () =>
    run(template.enabled ? "Turned off" : "Turned on", () =>
      api(`/admin/templates/${template.id}/`, { method: "PATCH", body: { enabled: !template.enabled } })
    );
  const test = () =>
    run("Test send", () =>
      api(`/admin/templates/${template.id}/test/`, {
        method: "POST",
        body: { email: testTo.email || undefined, phone: testTo.phone || undefined },
      })
    );
  const sync = () => run("WhatsApp sync", () => api(`/admin/templates/${template.id}/sync/`, { method: "POST" }));

  return (
    <td className={`cell ${template.enabled ? "" : "off"}`}>
      <label className="switch">
        <input type="checkbox" checked={template.enabled} onChange={toggle} />
        {template.enabled ? "On" : "Off"}
      </label>

      {(template.subject || template.title) && <b>{template.subject || template.title}</b>}
      <p className="preview">{template.body}</p>

      {channel === "whatsapp" && (
        <span className={`badge ${template.wa_status.toLowerCase()}`}>Meta: {template.wa_status}</span>
      )}

      <div className="actions">
        <button onClick={() => onEdit(template)}>Edit</button>
        {channel === "whatsapp" && <button onClick={sync}>Sync</button>}
        <button onClick={test}>Test</button>
      </div>
    </td>
  );
}
