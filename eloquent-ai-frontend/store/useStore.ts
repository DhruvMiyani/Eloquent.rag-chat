import { create } from 'zustand';
import { User, Conversation, Message } from '@/types';
import { chatAPI, authAPI } from '@/lib/api';
import Cookies from 'js-cookie';

interface AppState {
  // User state
  user: User | null;
  token: string | null;

  // Chat state
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: Message[];
  isLoading: boolean;
  isSidebarOpen: boolean;

  // Actions
  setUser: (user: User | null, token?: string) => void;
  initializeAuth: () => Promise<void>;
  loginAnonymous: () => Promise<void>;
  loginWithCredentials: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  convertToRegisteredUser: (email: string, password: string, name: string) => Promise<void>;
  logout: () => void;

  // Chat actions
  loadConversations: () => Promise<void>;
  selectConversation: (conversationId: string) => Promise<void>;
  createNewConversation: () => Promise<void>;
  deleteConversation: (conversationId: string) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  toggleSidebar: () => void;
  updateConversationTitle: (conversationId: string, title: string) => Promise<void>;
}

const useStore = create<AppState>((set, get) => ({
      // Initial state
      user: null,
      token: null,
      conversations: [],
      currentConversation: null,
      messages: [],
      isLoading: false,
      isSidebarOpen: true,

      // User actions
      setUser: (user, token) => {
        if (token) {
          Cookies.set('token', token, { expires: 7 });
        }
        set({ user, token });
      },

      initializeAuth: async () => {
        try {
          const existingToken = Cookies.get('token');

          if (existingToken) {
            console.log('Found existing token, clearing old token...');
            Cookies.remove('token');
          }

          // Create new anonymous session
          console.log('No valid token found, creating new anonymous session...');
          await get().loginAnonymous();
        } catch (error) {
          console.error('Failed to initialize auth:', error);
        }
      },

      loginAnonymous: async () => {
        try {
          console.log('Calling authAPI.loginAnonymous...');
          const { user, token } = await authAPI.loginAnonymous();
          console.log('Got user and token:', { user, token });
          get().setUser(user, token);
          console.log('Set user in store, loading conversations...');
          await get().loadConversations();
          console.log('Conversations loaded successfully');
        } catch (error) {
          console.error('Failed to login anonymously:', error);
          throw error;
        }
      },

      loginWithCredentials: async (email, password) => {
        try {
          const { user, token } = await authAPI.loginWithCredentials(email, password);
          get().setUser(user, token);
          await get().loadConversations();
        } catch (error) {
          console.error('Failed to login:', error);
          throw error;
        }
      },

      register: async (email, password, name) => {
        try {
          const { user, token } = await authAPI.register(email, password, name);
          get().setUser(user, token);
          await get().loadConversations();
        } catch (error) {
          console.error('Failed to register:', error);
          throw error;
        }
      },

      convertToRegisteredUser: async (email, password, name) => {
        try {
          const { user, token } = await authAPI.convertAnonymousToUser(email, password, name);
          get().setUser(user, token);
        } catch (error) {
          console.error('Failed to convert anonymous user:', error);
          throw error;
        }
      },

      logout: () => {
        Cookies.remove('token');
        set({ user: null, token: null, conversations: [], currentConversation: null, messages: [] });
      },

      // Chat actions
      loadConversations: async () => {
        try {
          set({ isLoading: true });
          const conversations = await chatAPI.getConversations();
          set({ conversations, isLoading: false });
        } catch (error) {
          console.error('Failed to load conversations:', error);
          set({ isLoading: false });
        }
      },

      selectConversation: async (conversationId) => {
        try {
          set({ isLoading: true });
          const conversation = await chatAPI.getConversation(conversationId);
          set({
            currentConversation: conversation,
            messages: conversation.messages || [],
            isLoading: false
          });
        } catch (error) {
          console.error('Failed to select conversation:', error);
          set({ isLoading: false });
        }
      },

      createNewConversation: async () => {
        try {
          const conversation = await chatAPI.createConversation();
          set((state) => ({
            conversations: [conversation, ...state.conversations],
            currentConversation: conversation,
            messages: []
          }));
        } catch (error) {
          console.error('Failed to create conversation:', error);
        }
      },

      deleteConversation: async (conversationId) => {
        try {
          await chatAPI.deleteConversation(conversationId);
          set((state) => ({
            conversations: state.conversations.filter((c) => c.id !== conversationId),
            currentConversation: state.currentConversation?.id === conversationId ? null : state.currentConversation,
            messages: state.currentConversation?.id === conversationId ? [] : state.messages
          }));
        } catch (error) {
          console.error('Failed to delete conversation:', error);
        }
      },

      sendMessage: async (content) => {
        const { currentConversation, user } = get();

        if (!currentConversation || !user) {
          throw new Error('No active conversation or user');
        }

        const userMessage: Message = {
          id: `temp-${Date.now()}`,
          content,
          role: 'user',
          timestamp: new Date().toISOString(),
          conversationId: currentConversation.id
        };

        set((state) => ({
          messages: [...state.messages, userMessage],
          isLoading: true
        }));

        try {
          const assistantMessage = await chatAPI.sendMessage(currentConversation.id, content);

          set((state) => ({
            messages: [...state.messages.filter(m => m.id !== userMessage.id), userMessage, assistantMessage],
            isLoading: false
          }));

          // Update conversation title if it's the first message
          if (get().messages.length === 2 && currentConversation.title === 'New Conversation') {
            const title = content.substring(0, 50) + (content.length > 50 ? '...' : '');
            await get().updateConversationTitle(currentConversation.id, title);
          }
        } catch (error) {
          console.error('Failed to send message:', error);
          set((state) => ({
            messages: state.messages.filter(m => m.id !== userMessage.id),
            isLoading: false
          }));
          throw error;
        }
      },

      toggleSidebar: () => {
        set((state) => ({ isSidebarOpen: !state.isSidebarOpen }));
      },

      updateConversationTitle: async (conversationId, title) => {
        try {
          const updatedConversation = await chatAPI.updateConversationTitle(conversationId, title);
          set((state) => ({
            conversations: state.conversations.map((c) =>
              c.id === conversationId ? updatedConversation : c
            ),
            currentConversation: state.currentConversation?.id === conversationId
              ? updatedConversation
              : state.currentConversation
          }));
        } catch (error) {
          console.error('Failed to update conversation title:', error);
        }
      }
}));

export default useStore;