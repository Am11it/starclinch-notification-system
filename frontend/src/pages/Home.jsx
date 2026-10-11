import { useEffect, useState } from "react";
import { api } from "../api";
import { enablePush, isPushEnabled } from "../push";

// The "website" side: things a normal user does, which fire triggers.
export default function Home({ user, setUser }) {
  const [name, setName] = useState(user.first_name);
  const [phone, setPhone] = useState(user.phone || "");
  const [pushOn, setPushOn] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    isPushEnabled().then(setPushOn).catch(() => {});
  }, []);

  async function saveProfile(e) {
    e.preventDefault();
    const updated = await api("/auth/me/", { method: "PATCH", body: { first_name: name, phone } });
    setUser(updated);
    setMessage("Profile saved");
  }

  async function turnOnPush() {
    try {
      setPushOn(await enablePush());
      setMessage("Browser subscribed to push notifications");
    } catch (err) {
      setMessage(err.message);
    }
  }

  async function placeOrder() {
    await api("/events/fire/", { method: "POST", body: { trigger: "order_placed" } });
    setMessage("Order placed! (fired the 'order_placed' trigger)");
  }

  return (
    <div className="grid">
      <div className="card">
        <h2>Hi {user.first_name || user.email} 👋</h2>
        <p className="muted">
          Logging in and out fires the <b>login</b> / <b>logout</b> triggers. Try the actions below too.
        </p>
        {message && <p className="success">{message}</p>}

        <h3>Web Push</h3>
        {pushOn ? (
          <p className="success">✅ This browser is subscribed</p>
        ) : (
          <button onClick={turnOnPush}>Enable push notifications</button>
        )}

        <h3>Demo actions</h3>
        <button onClick={placeOrder}>🛒 Place an order</button>
      </div>

      <form className="card" onSubmit={saveProfile}>
        <h2>My profile</h2>
        <label>Name</label>
        <input value={name} onChange={(e) => setName(e.target.value)} />
        <label>Email</label>
        <input value={user.email} disabled />
        <label>WhatsApp number (country code, no +)</label>
        <input placeholder="919876543210" value={phone} onChange={(e) => setPhone(e.target.value)} />
        <button className="primary">Save</button>
      </form>
    </div>
  );
}
