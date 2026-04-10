import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const sendMessage = async (message, conversationId = null) => {
  const response = await api.post('/api/chat', {
    message,
    conversation_id: conversationId,
  });
  return response.data;
};

export const getConversations = async () => {
  const response = await api.get('/api/history');
  return response.data;
};

export const getConversation = async (conversationId) => {
  const response = await api.get(`/api/history/${conversationId}`);
  return response.data;
};

export const deleteConversation = async (conversationId) => {
  const response = await api.delete(`/api/history/${conversationId}`);
  return response.data;
};

export default api;
