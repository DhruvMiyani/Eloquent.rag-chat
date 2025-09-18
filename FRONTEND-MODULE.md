# Eloquent AI Frontend Module - ChatGPT-Style UI

## Overview
A modern, responsive frontend application for the Eloquent AI Financial Assistant chatbot, featuring a ChatGPT-inspired user interface. Built with Next.js 14, TypeScript, and Tailwind CSS.

## Key Features Implemented

### 1. **ChatGPT-Style Interface**
- Clean, minimalist design matching the screenshot provided
- Purple accent color scheme (Purple-600 primary)
- Responsive layout with collapsible sidebar
- Professional header with navigation and user menu

### 2. **Chat Functionality**
- Real-time messaging interface
- Multi-line input with auto-resize
- Message history with role indicators (user/assistant)
- Loading states with animated typing indicator
- Markdown support for rich text responses
- Suggested questions for new users

### 3. **User Management**
- **Anonymous Users**: Auto-created on first visit
- **Registered Users**: Full account with email/password
- **Account Conversion**: Seamless upgrade from anonymous to registered
- JWT-based authentication
- Persistent sessions with cookies

### 4. **Conversation Management**
- Create new conversations
- View conversation history
- Edit conversation titles inline
- Delete conversations with confirmation
- Search conversations
- Auto-title generation from first message

### 5. **Sidebar Features**
- "New Analysis" button (purple CTA)
- Search bar for conversations
- Recent conversations list with timestamps
- Knowledge base section (PDF documents)
- Settings button at bottom
- Collapsible with toggle button

## Technical Architecture

### Technology Stack
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **HTTP Client**: Axios with interceptors
- **Icons**: Lucide React
- **Markdown**: React Markdown with GFM
- **Authentication**: JWT tokens with js-cookie

### Project Structure
```
eloquent-ai-frontend/
├── app/                    # Next.js app directory
│   ├── layout.tsx         # Root layout with metadata
│   ├── page.tsx           # Main chat application
│   └── globals.css        # Tailwind styles
├── components/
│   ├── Sidebar.tsx        # Left navigation panel
│   ├── Header.tsx         # Top navigation bar
│   ├── ChatArea.tsx       # Main chat interface
│   └── AuthModal.tsx      # Authentication modal
├── lib/
│   └── api.ts            # API client with interceptors
├── store/
│   └── useStore.ts       # Global state management
├── types/
│   └── index.ts          # TypeScript interfaces
└── .env.local            # Environment variables
```

### Component Details

#### **Sidebar Component**
- Displays user's conversation history
- Search functionality for filtering conversations
- Inline editing of conversation titles
- Delete conversations with confirmation
- Shows knowledge base documents
- Collapsible with smooth transitions

#### **ChatArea Component**
- Central chat interface
- Displays welcome screen for new conversations
- Shows suggested questions as clickable cards
- Renders message history with role indicators
- Auto-scrolls to latest messages
- Multi-line input with Shift+Enter support

#### **Header Component**
- Application branding "Eloquent AI - Financial Assistant"
- Navigation links (Resources, Careers)
- User authentication status
- "Request a demo" CTA button
- User dropdown menu with logout option

#### **AuthModal Component**
- Supports login, registration, and account conversion
- Clean form design with error handling
- Contextual messaging for anonymous users
- Loading states during authentication

## API Integration

### Authentication Endpoints
```typescript
POST /api/auth/anonymous         // Create anonymous session
POST /api/auth/login             // User login
POST /api/auth/register          // New user registration
POST /api/auth/convert           // Convert anonymous to registered
GET  /api/auth/me               // Get current user details
```

### Chat Endpoints
```typescript
GET    /api/chat/conversations              // List all conversations
POST   /api/chat/conversations              // Create new conversation
GET    /api/chat/conversations/{id}         // Get conversation with messages
DELETE /api/chat/conversations/{id}         // Delete conversation
PATCH  /api/chat/conversations/{id}         // Update conversation title
POST   /api/chat/conversations/{id}/messages // Send message
```

## State Management

### Zustand Store Structure
- **User State**: Current user, authentication token
- **Chat State**: Conversations, current conversation, messages
- **UI State**: Loading states, sidebar visibility
- **Actions**: Authentication, CRUD operations, messaging

### Key Store Actions
```typescript
loginAnonymous()              // Create anonymous session
loginWithCredentials()        // Authenticate user
sendMessage()                // Send chat message
createNewConversation()      // Start new chat
selectConversation()         // Switch conversations
updateConversationTitle()    // Rename conversation
```

## Running the Application

### Prerequisites
- Node.js 18+ installed
- npm or yarn package manager
- Backend API running on port 8000

### Installation
```bash
cd eloquent-ai-frontend
npm install
```

### Development
```bash
npm run dev
# Application runs on http://localhost:3000
```

### Production Build
```bash
npm run build
npm start
```

## Environment Configuration

Create `.env.local` file:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## UI/UX Features

### Visual Design
- Clean, modern interface with subtle shadows
- Purple accent color (#9333EA) for CTAs
- Gray color palette for neutral elements
- Smooth transitions and hover effects
- Responsive design for all screen sizes

### User Experience
- Instant anonymous access (no registration required)
- Seamless chat experience with real-time updates
- Intuitive conversation management
- Persistent chat history
- Smart auto-save functionality

## Security Features
- JWT token management with automatic refresh
- Secure cookie storage for tokens
- API interceptors for authentication
- Protected routes and API calls
- XSS protection with React's built-in sanitization

## Performance Optimizations
- Next.js Turbopack for fast development
- Component lazy loading
- Optimized re-renders with Zustand
- Efficient API calls with request batching
- Debounced search functionality

## Browser Compatibility
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Future Enhancements
- Real-time WebSocket support
- File upload capabilities
- Voice input/output
- Export conversation history
- Dark mode toggle
- Multi-language support

## Deployment Ready
The application is production-ready with:
- Environment variable configuration
- Error boundary implementation
- Loading states and error handling
- SEO metadata configuration
- Performance optimizations

## Summary
This frontend module provides a complete, production-ready ChatGPT-style interface for the Eloquent AI Financial Assistant. It features modern design, robust state management, secure authentication, and seamless integration with the backend API. The application is fully responsive, accessible, and ready for deployment to AWS or any cloud platform.