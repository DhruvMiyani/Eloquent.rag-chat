export interface User {
  id: string;
  name?: string;
  email?: string;
  isAnonymous: boolean;
  createdAt?: string;
}

export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
  conversationId: string;
}

export interface Conversation {
  id: string;
  title: string;
  userId: string;
  createdAt: string;
  updatedAt: string;
  messages?: Message[];
}

export interface ChatState {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: Message[];
  isLoading: boolean;
  user: User | null;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

export interface SuggestedQuestion {
  text: string;
  category: 'password' | 'account' | 'security' | 'payment' | 'general';
}