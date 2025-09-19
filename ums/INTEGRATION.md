# UMS Integration Guide

This guide explains how to integrate the User Management Services (UMS) module with your existing FastAPI backend and frontend.

## Backend Integration

### 1. Add UMS Dependencies

First, add the required dependencies to your `requirements.txt`:

```txt
bcrypt==4.0.1
PyJWT==2.8.0
```

### 2. Database Setup

The UMS module uses SQLAlchemy models. Ensure your database supports the UMS tables:

```python
# In your main app's database setup
from ums.models.user import Base as UMSBase

# Add UMS tables to your database
engine = create_engine(DATABASE_URL)
UMSBase.metadata.create_all(bind=engine)
```

### 3. FastAPI Integration

Add the UMS routes to your FastAPI application:

```python
# main.py or wherever you define your FastAPI app
from fastapi import FastAPI
from ums.api.routes import router as ums_router

app = FastAPI()

# Include UMS routes
app.include_router(ums_router)
```

### 4. Database Dependency Configuration

Update the UMS routes to use your app's database dependency:

```python
# In ums/api/routes.py, replace the get_db function with:
from your_app.database import get_db  # Import your app's database dependency
```

### 5. JWT Secret Configuration

Configure the JWT secret key for the UserService:

```python
# In your app's configuration
from ums.services.user_service import UserService

# Use your app's secret key
SECRET_KEY = "your-secret-key"  # Store in environment variables

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db, secret_key=SECRET_KEY)
```

## Frontend Integration

### 1. Install the Fingerprinting Utility

Copy the fingerprinting utility to your frontend:

```bash
# Copy the fingerprinting utility
cp ums/frontend/fingerprint.js your-frontend/lib/ums/
```

### 2. Initialize Anonymous Session

Replace your existing authentication logic with UMS:

```javascript
// lib/ums/auth.js
import { createSessionData, storeSessionToken, getSessionToken } from './fingerprint.js';

export async function initializeAnonymousSession() {
    try {
        // Check for existing session token
        const existingToken = getSessionToken();
        if (existingToken) {
            // Try to authenticate with existing session
            const response = await fetch('/api/ums/auth/session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_token: existingToken })
            });

            if (response.ok) {
                const data = await response.json();
                return data;
            }
        }

        // Create new anonymous session with fingerprinting
        const sessionData = await createSessionData();
        const response = await fetch('/api/ums/session/anonymous', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(sessionData)
        });

        const data = await response.json();

        // Store session token
        storeSessionToken(data.session.session_token);

        return data;
    } catch (error) {
        console.error('Failed to initialize session:', error);
        throw error;
    }
}
```

### 3. Update Your Authentication Store

Update your authentication state management to support UMS:

```javascript
// stores/authStore.js (Zustand example)
import { create } from 'zustand';
import { initializeAnonymousSession } from '../lib/ums/auth.js';

export const useAuthStore = create((set, get) => ({
    user: null,
    session: null,
    isLoading: true,
    isAuthenticated: false,

    initializeAuth: async () => {
        try {
            set({ isLoading: true });
            const result = await initializeAnonymousSession();

            set({
                user: result.user,
                session: result.session,
                isAuthenticated: true,
                isLoading: false
            });

            // Show welcome message for returning users
            if (result.is_returning) {
                console.log('Welcome back! We recognized you.');
            }

        } catch (error) {
            console.error('Authentication failed:', error);
            set({ isLoading: false });
        }
    },

    logout: async () => {
        const { session } = get();
        if (session?.session_token) {
            await fetch('/api/ums/auth/logout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_token: session.session_token })
            });
        }

        // Clear session token
        clearSessionToken();

        set({
            user: null,
            session: null,
            isAuthenticated: false
        });
    }
}));
```

### 4. User Registration/Conversion

For converting anonymous users to registered users:

```javascript
// lib/ums/auth.js
export async function convertToRegistered(email, password, name) {
    try {
        const response = await fetch('/api/ums/auth/convert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getSessionToken()}`
            },
            body: JSON.stringify({ email, password, name })
        });

        const data = await response.json();

        // Update stored token
        storeSessionToken(data.session.session_token);

        return data;
    } catch (error) {
        console.error('User conversion failed:', error);
        throw error;
    }
}
```

## API Endpoints

The UMS module provides the following endpoints:

### Anonymous User Flow
- `POST /api/ums/session/anonymous` - Create/retrieve anonymous session
- `POST /api/ums/auth/session` - Authenticate by session token

### User Registration & Authentication
- `POST /api/ums/auth/register` - Register new user
- `POST /api/ums/auth/login` - Login existing user
- `POST /api/ums/auth/convert` - Convert anonymous to registered
- `POST /api/ums/auth/logout` - Logout user

### User Information
- `GET /api/ums/user/me` - Get current user info
- `GET /api/ums/user/{user_id}/analytics` - Get user analytics
- `GET /api/ums/user/{user_id}/journey` - Get user journey data

### Statistics
- `GET /api/ums/stats` - Get overall user statistics

## User Journey Flow

The UMS module supports three user types with natural progression:

1. **Anonymous User** (First-time visitor)
   - No registration required
   - Browser fingerprinting for recognition
   - Session tracking

2. **Returning User** (Recognized anonymous user)
   - Automatically promoted when fingerprint matches
   - Maintains chat history
   - Encouraged to register

3. **Registered User** (Authenticated with credentials)
   - Full account features
   - Secure authentication
   - Persistent data across devices

## Environment Variables

Add these to your `.env` file:

```env
# JWT Secret for token generation
JWT_SECRET_KEY=your-super-secure-secret-key

# Database configuration (if separate from main app)
UMS_DATABASE_URL=sqlite:///./ums.db
```

## Security Considerations

1. **JWT Secret**: Use a strong, unique secret key for JWT token generation
2. **Fingerprinting**: Browser fingerprinting is used for user recognition, not security
3. **Session Storage**: Session tokens should be stored securely (httpOnly cookies in production)
4. **HTTPS**: Always use HTTPS in production for secure token transmission

## Testing

Test the integration by:

1. Visiting the app as a new user (should create anonymous session)
2. Refreshing the page (should recognize returning user)
3. Opening in incognito mode (should create new anonymous session)
4. Registering an account (should convert anonymous to registered)

## Migration from Existing Auth

If you have existing authentication, you can migrate gradually:

1. Install UMS alongside existing auth
2. Update new user flow to use UMS
3. Migrate existing users by creating UMS User records
4. Gradually transition all authentication to UMS

## Support

For questions about UMS integration, check:
- Model definitions in `ums/models/user.py`
- Service implementations in `ums/services/`
- API documentation in `ums/api/routes.py`