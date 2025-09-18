"""Main FastAPI application for Eloquent AI Chatbot."""

from datetime import datetime, timedelta
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from passlib.context import CryptContext
from jose import JWTError, jwt
import uuid
import os
import secrets
from dotenv import load_dotenv
import openai
from pinecone import Pinecone
import logging
from rag_service import RAGService

# Load environment variables
load_dotenv()

# Setup logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chat_database.db")
SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)
ALGORITHM = "HS256"

# Log warning if using generated secret key
if not os.getenv("SECRET_KEY"):
    logger.warning("No SECRET_KEY found in environment. Using generated key for this session only.")
    logger.warning("For production, set SECRET_KEY environment variable to a secure random string.")

ACCESS_TOKEN_EXPIRE_MINUTES = 1440
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "ai-powered-chatbot-challenge")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3001")

# Database setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Security
security = HTTPBearer()

# Initialize OpenAI
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# Initialize Pinecone
pc = None
index = None
if PINECONE_API_KEY:
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX)
    except Exception as e:
        logger.error(f"Failed to initialize Pinecone: {e}")

# Database Models
class UserDB(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=True)
    name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)
    is_anonymous = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversations = relationship("ConversationDB", back_populates="user", cascade="all, delete-orphan")

class ConversationDB(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, default="New Conversation")
    user_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserDB", back_populates="conversations")
    messages = relationship("MessageDB", back_populates="conversation", cascade="all, delete-orphan")

class MessageDB(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    content = Column(Text)
    role = Column(String)  # 'user' or 'assistant'
    conversation_id = Column(String, ForeignKey("conversations.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("ConversationDB", back_populates="messages")

Base.metadata.create_all(bind=engine)

# Pydantic models
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: str
    is_anonymous: bool
    created_at: Optional[datetime] = None

class Token(BaseModel):
    user: User
    token: str

class MessageBase(BaseModel):
    content: str
    role: str = "user"

class Message(MessageBase):
    id: str
    conversation_id: str
    timestamp: datetime

class ConversationBase(BaseModel):
    title: Optional[str] = "New Conversation"

class Conversation(ConversationBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[Message]] = []

class ConversationCreate(BaseModel):
    title: Optional[str] = None

class ConversationUpdate(BaseModel):
    title: str

class MessageCreate(BaseModel):
    content: str

# Initialize FastAPI app
app = FastAPI(
    title="Eloquent AI Financial Assistant API",
    description="RAG-based chatbot for financial services FAQ support",
    version="1.0.0"
)

# Initialize RAG service
rag_service = RAGService()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auth utilities
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

def get_current_user(user_id: str = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

# RAG Service
async def get_rag_response(query: str) -> str:
    """Get response from RAG system using Pinecone and OpenAI."""
    try:
        # Use the RAG service to generate response
        response_data = await rag_service.generate_rag_response(query)

        if response_data.get('error'):
            logger.error(f"RAG service error: {response_data['error']}")
            return "I apologize, but I'm having trouble processing your request. Please try again later."

        return response_data['response']

    except Exception as e:
        logger.error(f"RAG service error: {e}")
        return "I apologize, but I'm having trouble processing your request. Please try again later."

# Error response models
class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail

# Custom exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "details": None
            }
        }
    )

# API Routes
@app.get("/")
def read_root():
    return {"message": "Eloquent AI Financial Assistant API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "database": "connected"
    }

@app.post("/api/admin/setup-vector-db")
async def setup_vector_database():
    """Initialize the vector database with FAQ data."""
    try:
        logger.info("Starting vector database setup...")

        # Setup index
        index_setup = await rag_service.setup_index()
        if not index_setup:
            return {
                "success": False,
                "message": "Failed to setup Pinecone index. Check API key and configuration.",
                "error": "INDEX_SETUP_FAILED"
            }

        # Index FAQ data
        faq_file_path = "fintech_faq_data.json"
        indexing_success = await rag_service.index_faq_data(faq_file_path)

        if indexing_success:
            stats = await rag_service.get_index_stats()
            return {
                "success": True,
                "message": "Vector database setup completed successfully",
                "stats": stats
            }
        else:
            return {
                "success": False,
                "message": "Failed to index FAQ data",
                "error": "INDEXING_FAILED"
            }

    except Exception as e:
        logger.error(f"Vector database setup error: {e}")
        return {
            "success": False,
            "message": f"Setup failed: {str(e)}",
            "error": "SETUP_ERROR"
        }

@app.get("/api/admin/vector-db-stats")
async def get_vector_database_stats():
    """Get vector database statistics."""
    try:
        stats = await rag_service.get_index_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to get vector DB stats: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# Authentication endpoints
@app.post("/api/auth/anonymous", response_model=Token)
def create_anonymous_user(db: Session = Depends(get_db)):
    """Create an anonymous user session."""
    user = UserDB(
        id=str(uuid.uuid4()),
        is_anonymous=True,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": user.id})
    return Token(
        user=User(
            id=user.id,
            email=user.email,
            name=user.name,
            is_anonymous=user.is_anonymous,
            created_at=user.created_at
        ),
        token=token
    )

@app.post("/api/auth/register", response_model=Token)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user exists
    existing_user = db.query(UserDB).filter(UserDB.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    user = UserDB(
        id=str(uuid.uuid4()),
        email=user_data.email,
        name=user_data.name,
        hashed_password=get_password_hash(user_data.password),
        is_anonymous=False,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": user.id})
    return Token(
        user=User(
            id=user.id,
            email=user.email,
            name=user.name,
            is_anonymous=user.is_anonymous,
            created_at=user.created_at
        ),
        token=token
    )

@app.post("/api/auth/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login with email and password."""
    user = db.query(UserDB).filter(UserDB.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    token = create_access_token(data={"sub": user.id})
    return Token(
        user=User(
            id=user.id,
            email=user.email,
            name=user.name,
            is_anonymous=user.is_anonymous,
            created_at=user.created_at
        ),
        token=token
    )

@app.post("/api/auth/convert", response_model=Token)
def convert_anonymous_to_user(
    user_data: UserCreate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Convert an anonymous user to a registered user."""
    if not current_user.is_anonymous:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already registered"
        )

    # Check if email is already taken
    existing_user = db.query(UserDB).filter(UserDB.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Update user
    current_user.email = user_data.email
    current_user.name = user_data.name
    current_user.hashed_password = get_password_hash(user_data.password)
    current_user.is_anonymous = False

    db.commit()
    db.refresh(current_user)

    token = create_access_token(data={"sub": current_user.id})
    return Token(
        user=User(
            id=current_user.id,
            email=current_user.email,
            name=current_user.name,
            is_anonymous=current_user.is_anonymous,
            created_at=current_user.created_at
        ),
        token=token
    )

@app.get("/api/auth/me", response_model=User)
def get_current_user_info(current_user: UserDB = Depends(get_current_user)):
    """Get current user information."""
    return User(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        is_anonymous=current_user.is_anonymous,
        created_at=current_user.created_at
    )

# Chat endpoints
@app.get("/api/chat/conversations", response_model=List[Conversation])
def get_conversations(
    limit: int = 50,
    offset: int = 0,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversations for the current user with pagination."""
    if limit > 100:
        limit = 100  # Maximum limit
    if limit < 1:
        limit = 1

    conversations = db.query(ConversationDB).filter(
        ConversationDB.user_id == current_user.id
    ).order_by(ConversationDB.updated_at.desc()).offset(offset).limit(limit).all()

    return [
        Conversation(
            id=conv.id,
            title=conv.title,
            user_id=conv.user_id,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            messages=[]
        )
        for conv in conversations
    ]

@app.post("/api/chat/conversations", response_model=Conversation)
def create_conversation(
    conv_data: ConversationCreate = ConversationCreate(),
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation."""
    conversation = ConversationDB(
        id=str(uuid.uuid4()),
        title=conv_data.title or "New Conversation",
        user_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return Conversation(
        id=conversation.id,
        title=conversation.title,
        user_id=conversation.user_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[]
    )

@app.get("/api/chat/conversations/{conversation_id}", response_model=Conversation)
def get_conversation(
    conversation_id: str,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific conversation with messages."""
    conversation = db.query(ConversationDB).filter(
        ConversationDB.id == conversation_id,
        ConversationDB.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    messages = [
        Message(
            id=msg.id,
            content=msg.content,
            role=msg.role,
            conversation_id=msg.conversation_id,
            timestamp=msg.timestamp
        )
        for msg in conversation.messages
    ]

    return Conversation(
        id=conversation.id,
        title=conversation.title,
        user_id=conversation.user_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=messages
    )

@app.patch("/api/chat/conversations/{conversation_id}", response_model=Conversation)
def update_conversation(
    conversation_id: str,
    update_data: ConversationUpdate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update conversation title."""
    conversation = db.query(ConversationDB).filter(
        ConversationDB.id == conversation_id,
        ConversationDB.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    conversation.title = update_data.title
    conversation.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(conversation)

    return Conversation(
        id=conversation.id,
        title=conversation.title,
        user_id=conversation.user_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[]
    )

@app.delete("/api/chat/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation."""
    conversation = db.query(ConversationDB).filter(
        ConversationDB.id == conversation_id,
        ConversationDB.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    db.delete(conversation)
    db.commit()

    return {"message": "Conversation deleted successfully"}

@app.post("/api/chat/conversations/{conversation_id}/messages", response_model=Message)
async def send_message(
    conversation_id: str,
    message_data: MessageCreate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message and get AI response."""
    # Check if conversation exists and belongs to user
    conversation = db.query(ConversationDB).filter(
        ConversationDB.id == conversation_id,
        ConversationDB.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Save user message
    user_message = MessageDB(
        id=str(uuid.uuid4()),
        content=message_data.content,
        role="user",
        conversation_id=conversation_id,
        timestamp=datetime.utcnow()
    )
    db.add(user_message)

    # Get AI response
    ai_response = await get_rag_response(message_data.content)

    # Save AI response
    assistant_message = MessageDB(
        id=str(uuid.uuid4()),
        content=ai_response,
        role="assistant",
        conversation_id=conversation_id,
        timestamp=datetime.utcnow()
    )
    db.add(assistant_message)

    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(assistant_message)

    return Message(
        id=assistant_message.id,
        content=assistant_message.content,
        role=assistant_message.role,
        conversation_id=assistant_message.conversation_id,
        timestamp=assistant_message.timestamp
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)