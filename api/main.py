"""Main FastAPI application."""

from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, Cookie
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uuid
import logging

from config import settings
from models import (
    ChatRequest, ChatResponse, Chat, ChatListResponse,
    Message, MessageRole, ErrorResponse, HealthResponse
)
from rag_service import RAGService

# Dynamic database selection based on environment
if settings.USE_DYNAMODB:
    from database_dynamodb import DynamoDBDatabase
    db = DynamoDBDatabase()
else:
    from database import SQLiteDatabase
    db = SQLiteDatabase()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info("Starting up...")
    await db.initialize()
    yield
    # Shutdown
    logger.info("Shutting down...")

# Initialize FastAPI app
app = FastAPI(
    title="AI-Powered Chatbot API",
    description="RAG-based chatbot for fintech FAQ support",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get device_id from cookie
async def get_device_id(device_id: Optional[str] = Cookie(None)) -> Optional[str]:
    return device_id

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint."""
    return {
        "message": "AI-Powered Chatbot API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    services = {
        "database": False,
        "pinecone": False,
        "openai": False
    }

    # Check database
    try:
        test_chat = await db.get_chat("test-health-check")
        services["database"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")

    # Check Pinecone
    try:
        from rag_service import index
        stats = index.describe_index_stats()
        services["pinecone"] = stats.total_vector_count > 0
    except Exception as e:
        logger.error(f"Pinecone health check failed: {e}")

    # Check OpenAI
    try:
        import openai
        # Simple check - just verify API key is set
        services["openai"] = bool(settings.OPENAI_API_KEY)
    except Exception as e:
        logger.error(f"OpenAI health check failed: {e}")

    all_healthy = all(services.values())

    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        timestamp=datetime.utcnow(),
        services=services
    )

@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(
    request: ChatRequest,
    device_id: Optional[str] = Depends(get_device_id)
):
    """
    Process a chat message with RAG.
    Creates a new chat session if chat_id is not provided.
    """
    try:
        # Use provided device_id or generate one
        if not request.device_id and device_id:
            request.device_id = device_id
        elif not request.device_id and not device_id:
            request.device_id = str(uuid.uuid4())

        # Get or create chat session
        chat_id = request.chat_id
        if not chat_id:
            # Create new chat
            chat = await db.create_chat(
                user_id=request.user_id,
                device_id=request.device_id
            )
            chat_id = chat.id
        else:
            # Verify chat exists
            chat = await db.get_chat(chat_id)
            if not chat:
                raise HTTPException(status_code=404, detail="Chat not found")

        # Save user message
        await db.save_message(
            chat_id=chat_id,
            role=MessageRole.USER,
            content=request.message
        )

        # Get chat history for context
        messages = await db.get_messages(chat_id)
        chat_history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages[:-1]  # Exclude the message we just saved
        ]

        # Process through RAG pipeline
        answer, citations = await RAGService.process_query(
            query=request.message,
            chat_history=chat_history
        )

        # Save assistant response
        citations_dict = [citation.dict() for citation in citations]
        await db.save_message(
            chat_id=chat_id,
            role=MessageRole.ASSISTANT,
            content=answer,
            citations=citations_dict
        )

        # Get all messages
        all_messages = await db.get_messages(chat_id)

        return ChatResponse(
            chat_id=chat_id,
            answer=answer,
            citations=citations,
            messages=all_messages
        )

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chats/{chat_id}", response_model=ChatResponse, tags=["Chat"])
async def get_chat(chat_id: str):
    """Get a chat session with all messages."""
    try:
        # Verify chat exists
        chat = await db.get_chat(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        # Get messages
        messages = await db.get_messages(chat_id)

        # Get latest assistant message for response
        assistant_messages = [m for m in messages if m.role == MessageRole.ASSISTANT]
        latest_answer = assistant_messages[-1].content if assistant_messages else ""
        latest_citations = assistant_messages[-1].citations if assistant_messages else []

        return ChatResponse(
            chat_id=chat_id,
            answer=latest_answer,
            citations=latest_citations or [],
            messages=messages
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chats", response_model=ChatListResponse, tags=["Chat"])
async def list_chats(
    user_id: Optional[str] = None,
    device_id: Optional[str] = Depends(get_device_id)
):
    """List all chats for a user or device."""
    try:
        chats = await db.get_user_chats(
            user_id=user_id,
            device_id=device_id
        )

        return ChatListResponse(chats=chats)

    except Exception as e:
        logger.error(f"List chats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return ErrorResponse(
        error="Not Found",
        detail=str(exc.detail) if hasattr(exc, 'detail') else "Resource not found"
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return ErrorResponse(
        error="Internal Server Error",
        detail="An unexpected error occurred"
    )

# For AWS Lambda deployment with Mangum
def handler(event, context):
    """AWS Lambda handler."""
    from mangum import Mangum
    asgi_handler = Mangum(app)
    return asgi_handler(event, context)