import React, { useState, useEffect } from "react";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import "./index.css";

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [email, setEmail] = useState("");
  const [userId, setUserId] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    const storedEmail = localStorage.getItem("email");
    const storedUserId = localStorage.getItem("userId");
    if (token && storedEmail) {
      setIsLoggedIn(true);
      setEmail(storedEmail);
      setUserId(storedUserId || "");
    }
  }, []);

  const handleLogin = (userEmail, newUserId = "") => {
    setEmail(userEmail);
    setUserId(newUserId);
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("email");
    localStorage.removeItem("userId");
    setIsLoggedIn(false);
    setEmail("");
    setUserId("");
  };

  return (
    <div className="App">
      {isLoggedIn ? (
        <Dashboard email={email} userId={userId} onLogout={handleLogout} />
      ) : (
        <Login onLogin={handleLogin} />
      )}
    </div>
  );
}

export default App;
