import axios from 'axios';
import Cookies from 'js-cookie';
import { User, Conversation, Message } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://52.91.192.0';

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
      user: transformUser(response.data.user),
      token: response.data.access_token
    };
  },

  async loginWithCredentials(email: string, password: string): Promise<{ user: User; token: string }> {
    const response = await api.post('/api/auth/login', { email, password });
    return {
      user: transformUser(response.data.user),
      token: response.data.access_token
    };
  },

  async register(email: string, password: string, name: string): Promise<{ user: User; token: string }> {
    const response = await api.post('/api/auth/register', { email, password, name });
    return {
      user: transformUser(response.data.user),
      token: response.data.access_token
    };
  },

  async getCurrentUser(): Promise<User> {
    // No endpoint for getting current user - we'll just validate the token
    throw new Error('getCurrentUser not implemented');
  },

  async convertAnonymousToUser(email: string, password: string, name: string): Promise<{ user: User; token: string }> {
    const response = await api.post('/api/auth/convert', { email, password, name });
    return {
      user: transformUser(response.data.user),
      token: response.data.access_token
    };
  },
};

export const chatAPI = {
  async sendMessage(conversationId: string, content: string): Promise<Message> {
    const response = await api.post(`/api/conversations/${conversationId}/messages`, { content });
    // Backend returns { user_message: {...}, ai_message: {...} }
    // We return the ai_message since the user_message is already in the UI
    return response.data.ai_message;
  },

  async getConversations(): Promise<Conversation[]> {
    const response = await api.get('/api/conversations');
    return response.data;
  },

  async getConversation(id: string): Promise<Conversation> {
    const response = await api.get(`/api/conversations/${id}`);
    return response.data;
  },

  async createConversation(title?: string): Promise<Conversation> {
    const response = await api.post('/api/conversations', { title });
    return response.data;
  },

  async deleteConversation(id: string): Promise<void> {
    await api.delete(`/api/conversations/${id}`);
  },

  async updateConversationTitle(id: string, title: string): Promise<Conversation> {
    const response = await api.patch(`/api/conversations/${id}`, { title });
    return response.data;
  },
};

export default api;