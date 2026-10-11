import { Link, useNavigate } from "react-router-dom";
import { api, setToken } from "../api";

export default function Navbar({ user, setUser }) {
  const navigate = useNavigate();

  async function logout() {
    // Backend fires the "logout" trigger, then deletes our token
    await api("/auth/logout/", { method: "POST" }).catch(() => {});
    setToken(null);
    setUser(null);
    navigate("/login");
  }

  return (
    <nav className="navbar">
      <Link to="/" className="brand">🔔 StarClinch Notify</Link>
      <div className="nav-links">
        {user ? (
          <>
            <Link to="/">My account</Link>
            {user.is_staff && <Link to="/admin">Notification Settings</Link>}
            <span className="muted">{user.email}</span>
            <button onClick={logout}>Log out</button>
          </>
        ) : (
          <>
            <Link to="/login">Log in</Link>
            <Link to="/signup">Sign up</Link>
          </>
        )}
      </div>
    </nav>
  );
}
