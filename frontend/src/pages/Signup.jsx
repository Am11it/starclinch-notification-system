import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, setToken } from "../api";
import { linkPushToUser } from "../push";

export default function Signup({ setUser }) {
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", phone: "", password: "" });
  const [error, setError] = useState("");

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setError("");
    try {
      const { token, user } = await api("/auth/signup/", { method: "POST", body: form });
      setToken(token);
      setUser(user);
      linkPushToUser(user.id);
      navigate("/");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form className="card narrow" onSubmit={submit}>
      <h2>Create account</h2>
      <input placeholder="Name" value={form.name} onChange={update("name")} />
      <input placeholder="Email" type="email" value={form.email} onChange={update("email")} required />
      <input placeholder="WhatsApp number, e.g. 919876543210" value={form.phone} onChange={update("phone")} />
      <input placeholder="Password" type="password" value={form.password} onChange={update("password")} required />
      {error && <p className="error">{error}</p>}
      <button className="primary">Sign up</button>
      <p className="muted">Have an account? <Link to="/login">Log in</Link></p>
    </form>
  );
}
