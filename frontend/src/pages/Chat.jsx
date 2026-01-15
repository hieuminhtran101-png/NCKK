import React, { useState, useEffect, useRef } from "react";
import { chatAPI, userAPI } from "../api";
import "../styles/Chat.css";

function Chat({ email, userId }) {
  const [activeTab, setActiveTab] = useState("ai"); // 'ai' or 'users'
  const [aiMessages, setAiMessages] = useState([]);
  const [userMessages, setUserMessages] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (activeTab === "ai") {
      loadAiMessages();
    } else {
      loadConversations();
    }
  }, [activeTab]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [aiMessages, userMessages]);

  const loadAiMessages = async () => {
    try {
      const response = await chatAPI.getAiMessages();
      setAiMessages(response.data || []);
    } catch (err) {
      console.error("Error loading AI messages:", err);
    }
  };

  const loadConversations = async () => {
    try {
      const response = await chatAPI.getConversations();
      setConversations(response.data || []);
    } catch (err) {
      console.error("Error loading conversations:", err);
    }
  };

  const loadUserMessages = async (recipientId) => {
    try {
      const response = await chatAPI.getUserMessages(recipientId);
      setUserMessages(response.data || []);
    } catch (err) {
      console.error("Error loading user messages:", err);
    }
  };

  const handleSendAiMessage = async (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    setLoading(true);
    try {
      const response = await chatAPI.getAiResponse(inputText);

      // Add user message
      setAiMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          sender_id: userId,
          content: inputText,
          created_at: new Date().toISOString(),
          is_ai: false,
        },
      ]);

      // Add AI response
      setAiMessages((prev) => [
        ...prev,
        {
          id: response.data.id,
          sender_id: "ai",
          content: response.data.content,
          created_at: response.data.created_at,
          is_ai: true,
        },
      ]);

      setInputText("");
    } catch (err) {
      alert(
        "Error getting AI response: " +
          (err.response?.data?.detail || err.message)
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSendUserMessage = async (e) => {
    e.preventDefault();
    if (!inputText.trim() || !selectedUser) return;

    setLoading(true);
    try {
      await chatAPI.sendMessage(selectedUser, inputText);

      // Add message to list
      setUserMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          sender_id: userId,
          recipient_id: selectedUser,
          content: inputText,
          created_at: new Date().toISOString(),
          is_ai: false,
        },
      ]);

      setInputText("");
    } catch (err) {
      alert(
        "Error sending message: " + (err.response?.data?.detail || err.message)
      );
    } finally {
      setLoading(false);
    }
  };

  const selectUserConversation = (recipientId) => {
    setSelectedUser(recipientId);
    loadUserMessages(recipientId);
  };

  return (
    <div className="chat-container">
      <div className="chat-tabs">
        <button
          className={`chat-tab ${activeTab === "ai" ? "active" : ""}`}
          onClick={() => setActiveTab("ai")}
        >
          💬 AI Chat
        </button>
        <button
          className={`chat-tab ${activeTab === "users" ? "active" : ""}`}
          onClick={() => setActiveTab("users")}
        >
          👥 User Chat
        </button>
      </div>

      <div className="chat-content">
        {activeTab === "ai" ? (
          <div className="chat-main">
            <div className="chat-messages">
              {aiMessages.length === 0 ? (
                <div className="empty-chat">
                  <div className="empty-icon">🤖</div>
                  <p>Start chatting with AI!</p>
                </div>
              ) : (
                aiMessages.map((msg, idx) => (
                  <div
                    key={msg.id}
                    className={`chat-message ${msg.is_ai ? "ai" : "user"}`}
                  >
                    <div className="message-avatar">
                      {msg.is_ai ? "🤖" : "👤"}
                    </div>
                    <div className="message-content">
                      <div className="message-text">{msg.content}</div>
                      <div className="message-time">
                        {new Date(msg.created_at).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSendAiMessage} className="chat-form">
              <input
                type="text"
                placeholder="Ask AI anything..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                disabled={loading}
              />
              <button type="submit" disabled={loading || !inputText.trim()}>
                {loading ? "⏳" : "📤 Send"}
              </button>
            </form>
          </div>
        ) : (
          <div className="chat-users">
            <div className="conversations-list">
              <h3>Conversations</h3>
              {conversations.length === 0 ? (
                <div className="empty-list">No conversations yet</div>
              ) : (
                conversations.map((conv) => (
                  <div
                    key={conv.id}
                    className={`conversation-item ${
                      selectedUser === conv.participant2_id ? "active" : ""
                    }`}
                    onClick={() => selectUserConversation(conv.participant2_id)}
                  >
                    <div className="conv-avatar">👤</div>
                    <div className="conv-info">
                      <div className="conv-name">
                        User {conv.participant2_id.substring(0, 8)}
                      </div>
                      <div className="conv-preview">
                        {conv.last_message.substring(0, 30)}...
                      </div>
                      <div className="conv-time">
                        {new Date(conv.last_message_time).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {selectedUser ? (
              <div className="chat-main">
                <div className="chat-header">
                  <h3>User {selectedUser.substring(0, 8)}</h3>
                </div>

                <div className="chat-messages">
                  {userMessages.length === 0 ? (
                    <div className="empty-chat">
                      <p>No messages yet. Start the conversation!</p>
                    </div>
                  ) : (
                    userMessages.map((msg) => (
                      <div
                        key={msg.id}
                        className={`chat-message ${
                          msg.sender_id === userId ? "user" : "other"
                        }`}
                      >
                        <div className="message-avatar">👤</div>
                        <div className="message-content">
                          <div className="message-text">{msg.content}</div>
                          <div className="message-time">
                            {new Date(msg.created_at).toLocaleTimeString()}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                  <div ref={messagesEndRef} />
                </div>

                <form onSubmit={handleSendUserMessage} className="chat-form">
                  <input
                    type="text"
                    placeholder="Type a message..."
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    disabled={loading}
                  />
                  <button type="submit" disabled={loading || !inputText.trim()}>
                    {loading ? "⏳" : "📤 Send"}
                  </button>
                </form>
              </div>
            ) : (
              <div className="chat-main empty">
                <div className="empty-chat">
                  <p>Select a conversation to start chatting</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default Chat;
