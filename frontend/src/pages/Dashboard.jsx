import React, { useState, useEffect } from "react";
import { scheduleAPI, uploadAPI, aiAPI, eventAPI } from "../api";
import Chat from "./Chat";
import "../styles/Dashboard.css";

function Dashboard({ email, onLogout, userId }) {
  const [schedules, setSchedules] = useState([]);
  const [events, setEvents] = useState([]);
  const [activeTab, setActiveTab] = useState("schedule");
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [showParseForm, setShowParseForm] = useState(false);
  const [parseText, setParseText] = useState("");
  const [loading, setLoading] = useState(false);
  const [parsedSchedules, setParsedSchedules] = useState([]);
  const [requestId, setRequestId] = useState(null);

  useEffect(() => {
    // Only load if email exists (meaning user is logged in)
    if (email) {
      loadSchedules();
      loadEvents();
    }
  }, [email]);

  const loadSchedules = async () => {
    try {
      const response = await scheduleAPI.getAll();
      setSchedules(response.data || []);
    } catch (err) {
      console.error("Error loading schedules:", err);
    }
  };

  const loadEvents = async () => {
    try {
      const response = await eventAPI.getAll();
      setEvents(response.data || []);
    } catch (err) {
      console.error("Error loading events:", err);
    }
  };

  const handleFileUpload = async (file) => {
    setLoading(true);
    try {
      const response = await uploadAPI.uploadSchedule(file);
      setParsedSchedules(response.data.schedules || []);
      setRequestId(response.data.request_id);
      setShowUploadForm(false);
      alert("File parsed successfully! Please review and confirm.");
    } catch (err) {
      alert("Error uploading file: " + err.response?.data?.detail);
    } finally {
      setLoading(false);
    }
  };

  const handleParsText = async () => {
    if (!parseText.trim()) return;
    setLoading(true);
    try {
      const response = await aiAPI.parseText(parseText);
      setParsedSchedules(response.data.schedules || []);
      setRequestId(response.data.request_id);
      setParseText("");
      setShowParseForm(false);
      alert("Text parsed successfully! Review and confirm to save.");
    } catch (err) {
      alert("Error parsing text: " + err.response?.data?.detail);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmSchedules = async () => {
    if (parsedSchedules.length === 0) {
      alert("No schedules to confirm");
      return;
    }
    setLoading(true);
    try {
      if (requestId) {
        // Call confirm-parse endpoint with request_id
        await aiAPI.confirmParse(requestId);
      } else {
        // Fallback: try to save via batch endpoint (if it exists)
        await scheduleAPI.batch(parsedSchedules);
      }
      setParsedSchedules([]);
      setRequestId(null);
      loadSchedules();
      alert("Schedules saved successfully!");
    } catch (err) {
      alert("Error saving schedules: " + err.response?.data?.detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>📅 Smart Scheduler</h1>
        <div className="header-actions">
          <span className="user-email">{email}</span>
          <button onClick={onLogout} className="logout-btn">
            Logout
          </button>
        </div>
      </header>

      <div className="dashboard-tabs">
        <button
          className={`tab ${activeTab === "schedule" ? "active" : ""}`}
          onClick={() => setActiveTab("schedule")}
        >
          My Schedule
        </button>
        <button
          className={`tab ${activeTab === "upload" ? "active" : ""}`}
          onClick={() => setActiveTab("upload")}
        >
          Import Schedule
        </button>
        <button
          className={`tab ${activeTab === "events" ? "active" : ""}`}
          onClick={() => setActiveTab("events")}
        >
          Events
        </button>{" "}
        <button
          className={`tab-btn ${activeTab === "chat" ? "active" : ""}`}
          onClick={() => setActiveTab("chat")}
        >
          💬 Chat
        </button>{" "}
      </div>

      <div className="dashboard-content">
        {activeTab === "schedule" && (
          <div className="schedule-view">
            <h2>📚 My Schedules</h2>
            {schedules.length === 0 ? (
              <p className="empty-message">No schedules yet. Upload one!</p>
            ) : (
              <div className="schedule-grid">
                {schedules.map((schedule, idx) => (
                  <div key={idx} className="schedule-card">
                    <h3>{schedule.subject || "Untitled"}</h3>
                    <p>
                      <strong>Day:</strong> {schedule.day}
                    </p>
                    <p>
                      <strong>Time:</strong> {schedule.start_time} -{" "}
                      {schedule.end_time}
                    </p>
                    {schedule.location && (
                      <p>
                        <strong>Location:</strong> {schedule.location}
                      </p>
                    )}
                    {schedule.notes && (
                      <p>
                        <strong>Notes:</strong> {schedule.notes}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "upload" && (
          <div className="upload-view">
            <h2>📤 Import Schedule</h2>
            <div className="upload-options">
              <button
                className="upload-btn"
                onClick={() => setShowUploadForm(!showUploadForm)}
              >
                📁 Upload Excel File
              </button>
              <button
                className="upload-btn"
                onClick={() => setShowParseForm(!showParseForm)}
              >
                ✏️ Parse Text
              </button>
            </div>

            {showUploadForm && (
              <div className="upload-form">
                <input
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={(e) => {
                    if (e.target.files[0]) {
                      handleFileUpload(e.target.files[0]);
                    }
                  }}
                />
              </div>
            )}

            {showParseForm && (
              <div className="upload-form">
                <textarea
                  value={parseText}
                  onChange={(e) => setParseText(e.target.value)}
                  placeholder="E.g., Toán ngày 15/1 phòng 201 8am-10am&#10;Văn ngày 16/1 phòng 102"
                  rows="5"
                />
                <button
                  onClick={handleParsText}
                  disabled={loading}
                  className="primary-btn"
                >
                  {loading ? "Parsing..." : "Parse Text"}
                </button>
              </div>
            )}

            {parsedSchedules.length > 0 && (
              <div className="parsed-schedules">
                <h3>📋 Parsed Schedules (Review & Confirm)</h3>
                <div className="schedule-grid">
                  {parsedSchedules.map((schedule, idx) => (
                    <div key={idx} className="schedule-card">
                      <h4>{schedule.subject}</h4>
                      <p>
                        <strong>Day:</strong> {schedule.day}
                      </p>
                      <p>
                        <strong>Time:</strong> {schedule.start_time} -{" "}
                        {schedule.end_time}
                      </p>
                      {schedule.location && (
                        <p>
                          <strong>Location:</strong> {schedule.location}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
                <button
                  onClick={handleConfirmSchedules}
                  disabled={loading}
                  className="confirm-btn"
                >
                  {loading ? "Saving..." : "✅ Confirm & Save"}
                </button>
              </div>
            )}
          </div>
        )}

        {activeTab === "events" && (
          <div className="events-view">
            <h2>📌 Events & Deadlines</h2>
            {events.length === 0 ? (
              <p className="empty-message">No events yet.</p>
            ) : (
              <div className="events-list">
                {events.map((event, idx) => (
                  <div key={idx} className="event-card">
                    <h4>{event.title}</h4>
                    <p>{event.description}</p>
                    <span className="event-date">{event.deadline}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "chat" && <Chat email={email} userId={userId} />}
      </div>
    </div>
  );
}

export default Dashboard;
