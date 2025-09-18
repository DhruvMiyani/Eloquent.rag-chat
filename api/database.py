"""Database management for chat persistence."""

import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, String, DateTime, Text, JSON, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from contextlib import asynccontextmanager

from config import settings
from models import Message, Chat, MessageRole

Base = declarative_base()

class ChatTable(Base):
    __tablename__ = "chats"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True, index=True)
    device_id = Column(String, nullable=True, index=True)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MessageTable(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_id = Column(String, index=True)
    role = Column(String)
    content = Column(Text)
    citations = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class SQLiteDatabase:
    def __init__(self):
        self.engine = None
        self.async_session = None

    async def initialize(self):
        """Initialize the database connection."""
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            future=True
        )
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def get_session(self):
        """Get a database session."""
        async with self.async_session() as session:
            yield session

    async def create_chat(
        self,
        chat_id: Optional[str] = None,
        user_id: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> Chat:
        """Create a new chat session."""
        if not chat_id:
            chat_id = str(uuid.uuid4())

        async with self.get_session() as session:
            chat = ChatTable(
                id=chat_id,
                user_id=user_id,
                device_id=device_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(chat)
            await session.commit()

        return Chat(
            id=chat_id,
            user_id=user_id,
            device_id=device_id,
            created_at=chat.created_at,
            updated_at=chat.updated_at
        )

    async def get_chat(self, chat_id: str) -> Optional[Chat]:
        """Get a chat by ID."""
        async with self.get_session() as session:
            result = await session.execute(
                text(f"SELECT * FROM chats WHERE id = '{chat_id}'")
            )
            chat_row = result.first()

            if not chat_row:
                return None

            return Chat(
                id=chat_row.id,
                user_id=chat_row.user_id,
                device_id=chat_row.device_id,
                title=chat_row.title,
                created_at=chat_row.created_at,
                updated_at=chat_row.updated_at
            )

    async def save_message(
        self,
        chat_id: str,
        role: MessageRole,
        content: str,
        citations: Optional[List[Dict]] = None
    ) -> Message:
        """Save a message to the database."""
        message_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()

        async with self.get_session() as session:
            message = MessageTable(
                id=message_id,
                chat_id=chat_id,
                role=role,
                content=content,
                citations=json.dumps(citations) if citations else None,
                timestamp=timestamp
            )
            session.add(message)

            # Update chat's updated_at
            await session.execute(
                text(f"UPDATE chats SET updated_at = '{timestamp.isoformat()}' WHERE id = '{chat_id}'")
            )

            await session.commit()

        return Message(
            id=message_id,
            chat_id=chat_id,
            role=role,
            content=content,
            timestamp=timestamp,
            citations=citations
        )

    async def get_messages(self, chat_id: str) -> List[Message]:
        """Get all messages for a chat."""
        async with self.get_session() as session:
            result = await session.execute(
                text(f"SELECT * FROM messages WHERE chat_id = '{chat_id}' ORDER BY timestamp ASC")
            )
            rows = result.fetchall()

            messages = []
            for row in rows:
                citations = json.loads(row.citations) if row.citations and row.citations != 'null' else None
                messages.append(Message(
                    id=row.id,
                    chat_id=row.chat_id,
                    role=row.role,
                    content=row.content,
                    timestamp=row.timestamp,
                    citations=citations
                ))

            return messages

    async def get_user_chats(
        self,
        user_id: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> List[Chat]:
        """Get all chats for a user or device."""
        async with self.get_session() as session:
            where_clause = []
            if user_id:
                where_clause.append(f"user_id = '{user_id}'")
            if device_id:
                where_clause.append(f"device_id = '{device_id}'")

            if not where_clause:
                return []

            query = f"SELECT * FROM chats WHERE {' OR '.join(where_clause)} ORDER BY updated_at DESC"
            result = await session.execute(text(query))
            rows = result.fetchall()

            chats = []
            for row in rows:
                chats.append(Chat(
                    id=row.id,
                    user_id=row.user_id,
                    device_id=row.device_id,
                    title=row.title,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                ))

            return chats

# Database singleton
db = SQLiteDatabase()