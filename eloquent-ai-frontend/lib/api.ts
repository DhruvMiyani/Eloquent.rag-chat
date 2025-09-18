import axios from 'axios';
import Cookies from 'js-cookie';
import { User, Conversation, Message } from '@/types';

const API_BASE_URL = 'http://10.0.0.149:8002';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = Cookies.get('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Helper function to transform snake_case to camelCase for user objects
const transformUser = (user: any) => {
  if (!user) return user;
  return {
    ...user,
    isAnonymous: user.is_anonymous,
    createdAt: user.created_at
  };
};

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      Cookies.remove('token');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  async loginAnonymous(): Promise<{ user: User; token: string }> {
    console.log('API_BASE_URL:', API_BASE_URL);
    console.log('Making request to:', `${API_BASE_URL}/api/auth/anonymous`);
    const response = await api.post('/api/auth/anonymous');
    console.log('API response:', response.data);
    return {
      ...response.data,
      user: transformUser(response.data.user)
    };
  },

  async loginWithCredentials(email: string, password: string): Promise<{ user: User; token: string }> {
    const response = await api.post('/api/auth/login', { email, password });
    return {
      ...response.data,
      user: transformUser(response.data.user)
    };
  },

  async register(email: string, password: string, name: string): Promise<{ user: User; token: string }> {
    const response = await api.post('/api/auth/register', { email, password, name });
    return {
      ...response.data,
      user: transformUser(response.data.user)
    };
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get('/api/auth/me');
    return transformUser(response.data);
  },

  async convertAnonymousToUser(email: string, password: string, name: string): Promise<{ user: User; token: string }> {
    const response = await api.post('/api/auth/convert', { email, password, name });
    return {
      ...response.data,
      user: transformUser(response.data.user)
    };
  },
};

export const chatAPI = {
  async sendMessage(conversationId: string, content: string): Promise<Message> {
    const response = await api.post(`/api/chat/conversations/${conversationId}/messages`, { content });
    return response.data;
  },

  async getConversations(): Promise<Conversation[]> {
    const response = await api.get('/api/chat/conversations');
    return response.data;
  },

  async getConversation(id: string): Promise<Conversation> {
    const response = await api.get(`/api/chat/conversations/${id}`);
    return response.data;
  },

  async createConversation(title?: string): Promise<Conversation> {
    const response = await api.post('/api/chat/conversations', { title });
    return response.data;
  },

  async deleteConversation(id: string): Promise<void> {
    await api.delete(`/api/chat/conversations/${id}`);
  },

  async updateConversationTitle(id: string, title: string): Promise<Conversation> {
    const response = await api.patch(`/api/chat/conversations/${id}`, { title });
    return response.data;
  },
};

export default api;