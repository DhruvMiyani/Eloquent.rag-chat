"""Main FastAPI application for Eloquent AI Chatbot - Python 3.7 compatible."""

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
import pinecone
import logging

# Load environment variables (only if not already set)
if not os.getenv("OPENAI_API_KEY"):
    load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Pinecone with the old API
pinecone.init(
    api_key=os.getenv("PINECONE_API_KEY"),
    environment="aped-4627-b74a"
)

# Create the FastAPI app
app = FastAPI(title="Eloquent AI Chatbot API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = "sqlite:///./chat_database.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OpenAI configuration
# Force reload of environment variables and reset OpenAI API key
api_key_from_env = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key_from_env
logger.info(f"OpenAI API Key configured (last 10 chars): {openai.api_key[-10:] if openai.api_key else 'None'}")
logger.info(f"Environment OPENAI_API_KEY (last 10 chars): {api_key_from_env[-10:] if api_key_from_env else 'None'}")

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    timestamp: datetime

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse]

# Database models
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    name = Column(String, nullable=True)
    is_anonymous = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="user")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    title = Column(String, default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String)  # 'user' or 'assistant'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Simple RAG service for Python 3.7
class SimpleRAGService:
    def __init__(self):
        self.index_name = "ai-powered-chatbot-challenge"
        try:
            self.index = pinecone.Index(self.index_name)
        except Exception as e:
            logger.error(f"Error connecting to Pinecone: {e}")
            self.index = None

    def query_similar_content(self, query: str, top_k: int = 3) -> List[Dict]:
        if not self.index:
            return []

        try:
            # Ensure OpenAI API key is set correctly at runtime
            openai.api_key = os.getenv("OPENAI_API_KEY")

            # Create embedding for query
            response = openai.Embedding.create(
                input=query,
                model="text-embedding-3-small"
            )
            query_embedding = response['data'][0]['embedding']

            # Query Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )

            return [match.metadata for match in results.matches if match.score > 0.7]
        except Exception as e:
            logger.error(f"Error querying RAG: {e}")
            return []

    def generate_response_with_context(self, query: str, context_docs: List[Dict]) -> str:
        context = "\n".join([doc.get('content', '') for doc in context_docs])

        prompt = f"""You are a helpful financial services assistant. Use the following context to answer the user's question. If the context doesn't contain relevant information, provide a general helpful response.

Context:
{context}

User Question: {query}

Assistant Response:"""

        try:
            # Ensure OpenAI API key is set correctly at runtime
            openai.api_key = os.getenv("OPENAI_API_KEY")

            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful financial services assistant. Use the provided context to answer questions accurately."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I'm experiencing some technical difficulties. Please try again later."

# Initialize RAG service
rag_service = SimpleRAGService()

# Authentication functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Routes
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Eloquent AI Chatbot API is running"}

@app.post("/api/auth/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        name=user_data.name,
        is_anonymous=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.id}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "email": db_user.email,
            "name": db_user.name,
            "is_anonymous": db_user.is_anonymous,
            "created_at": db_user.created_at
        }
    }

@app.post("/api/auth/login")
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "is_anonymous": user.is_anonymous,
            "created_at": user.created_at
        }
    }

@app.post("/api/auth/anonymous")
async def create_anonymous_user(db: Session = Depends(get_db)):
    # Create anonymous user
    db_user = User(is_anonymous=True)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.id}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "email": db_user.email,
            "name": db_user.name,
            "is_anonymous": db_user.is_anonymous,
            "created_at": db_user.created_at
        }
    }

@app.get("/api/conversations")
async def get_conversations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conversations = db.query(Conversation).filter(Conversation.user_id == current_user.id).all()
    return [
        {
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at
        }
        for conv in conversations
    ]

@app.post("/api/conversations")
async def create_conversation(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conversation = Conversation(user_id=current_user.id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at
    }

@app.get("/api/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(Message).filter(Message.conversation_id == conversation_id).all()
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp
        }
        for msg in messages
    ]

@app.post("/api/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Save user message
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=message_data.content
    )
    db.add(user_message)

    # Generate AI response using RAG
    context_docs = rag_service.query_similar_content(message_data.content)
    ai_response = rag_service.generate_response_with_context(message_data.content, context_docs)

    # Save AI response
    ai_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=ai_response
    )
    db.add(ai_message)

    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(user_message)
    db.refresh(ai_message)

    return {
        "user_message": {
            "id": user_message.id,
            "role": user_message.role,
            "content": user_message.content,
            "timestamp": user_message.timestamp
        },
        "ai_message": {
            "id": ai_message.id,
            "role": ai_message.role,
            "content": ai_message.content,
            "timestamp": ai_message.timestamp
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)