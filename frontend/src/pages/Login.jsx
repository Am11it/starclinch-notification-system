import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, setToken } from "../api";
import { linkPushToUser } from "../push";

export default function Login({ setUser }) {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");

  async function submit(e) {
    e.preventDefault();
    setError("");
    try {
      // Backend fires the "login" trigger here
      const { token, user } = await api("/auth/login/", { method: "POST", body: form });
      setToken(token);
      setUser(user);
      linkPushToUser(user.id);
      navigate(user.is_staff ? "/admin" : "/");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form className="card narrow" onSubmit={submit}>
      <h2>Log in</h2>
      <input placeholder="Email" type="email" value={form.email}
        onChange={(e) => setForm({ ...form, email: e.target.value })} required />
      <input placeholder="Password" type="password" value={form.password}
        onChange={(e) => setForm({ ...form, password: e.target.value })} required />
      {error && <p className="error">{error}</p>}
      <button className="primary">Log in</button>
      <p className="muted">
        <Link to="/forgot-password">Forgot password?</Link> · <Link to="/signup">Create account</Link>
      </p>
    </form>
  );
}
