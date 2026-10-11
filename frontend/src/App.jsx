import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { api, getToken } from "./api";
import { linkPushToUser } from "./push";
import Navbar from "./components/Navbar";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import ForgotPassword from "./pages/ForgotPassword";
import Home from "./pages/Home";
import AdminNotifications from "./pages/AdminNotifications";

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(!!getToken());

  // If we already have a token, load the logged-in user
  useEffect(() => {
    if (!getToken()) return;
    api("/auth/me/")
      .then((me) => {
        setUser(me);
        linkPushToUser(me.id);
      })
      .catch(() => localStorage.removeItem("token"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="page">Loading...</p>;

  return (
    <>
      <Navbar user={user} setUser={setUser} />
      <main className="page">
        <Routes>
          <Route path="/login" element={user ? <Navigate to="/" /> : <Login setUser={setUser} />} />
          <Route path="/signup" element={user ? <Navigate to="/" /> : <Signup setUser={setUser} />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/" element={user ? <Home user={user} setUser={setUser} /> : <Navigate to="/login" />} />
          <Route
            path="/admin"
            element={user?.is_staff ? <AdminNotifications /> : <Navigate to="/" />}
          />
        </Routes>
      </main>
    </>
  );
}
