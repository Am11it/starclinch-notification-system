import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");

  async function submit(e) {
    e.preventDefault();
    // Backend fires the "password_reset" trigger
    const data = await api("/auth/password-reset/", { method: "POST", body: { email } });
    setMessage(data.message);
  }

  return (
    <form className="card narrow" onSubmit={submit}>
      <h2>Reset password</h2>
      <input placeholder="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      {message && <p className="success">{message}</p>}
      <button className="primary">Send reset message</button>
      <p className="muted"><Link to="/login">Back to log in</Link></p>
    </form>
  );
}
