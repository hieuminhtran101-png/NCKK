import axios from "axios";

const API_URL = "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  register: (email, password, full_name) =>
    api.post("/auth/register", { email, password, full_name, role: "user" }),
  login: (email, password) => api.post("/auth/login", { email, password }),
  getMe: () => api.get("/users/me"),
};

export const scheduleAPI = {
  getAll: () => api.get("/schedules"),
  getById: (id) => api.get(`/schedules/${id}`),
  create: (data) => api.post("/schedules", data),
  update: (id, data) => api.put(`/schedules/${id}`, data),
  delete: (id) => api.delete(`/schedules/${id}`),
  batch: (schedules) => api.post("/schedules/batch", schedules),
};

export const eventAPI = {
  getAll: () => api.get("/events"),
  create: (data) => api.post("/events", data),
  delete: (id) => api.delete(`/events/${id}`),
};

export const uploadAPI = {
  uploadSchedule: (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/upload/schedule", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

export const aiAPI = {
  parseText: (text) => api.post("/ai/parse-text", { text }),
  confirmParse: (request_id) => api.post("/ai/confirm-parse", { request_id }),
  getPriority: (event_id) => api.get(`/ai/priority/${event_id}`),
  getFreeSlots: (date, duration = 60) =>
    api.get("/ai/free-slots", { params: { date, duration } }),
};

export const chatAPI = {
  sendMessage: (recipientId, content) =>
    api.post("/chat/messages", { recipient_id: recipientId, content }),
  getConversations: () => api.get("/chat/conversations"),
  getUserMessages: (recipientId) => api.get(`/chat/messages/${recipientId}`),
  getAiMessages: () => api.get("/chat/ai-messages"),
  getAiResponse: (content) => api.post("/chat/ai-response", { content }),
};

export default api;
