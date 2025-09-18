"""DynamoDB implementation for chat persistence."""

import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
import boto3
from boto3.dynamodb.conditions import Key

from config import settings
from models import Message, Chat, MessageRole

class DynamoDBDatabase:
    def __init__(self):
        self.dynamodb = None
        self.chats_table = None
        self.messages_table = None

    async def initialize(self):
        """Initialize DynamoDB connection and tables."""
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name=settings.AWS_REGION
        )

        # Table names
        chats_table_name = f"{settings.DYNAMODB_TABLE_PREFIX}_chats"
        messages_table_name = f"{settings.DYNAMODB_TABLE_PREFIX}_messages"

        # Create or get tables
        try:
            self.chats_table = self.dynamodb.Table(chats_table_name)
            self.chats_table.load()
        except:
            # Create chats table
            self.chats_table = self.dynamodb.create_table(
                TableName=chats_table_name,
                KeySchema=[
                    {'AttributeName': 'id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'device_id', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'user_id_index',
                        'Keys': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    },
                    {
                        'IndexName': 'device_id_index',
                        'Keys': [
                            {'AttributeName': 'device_id', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            self.chats_table.wait_until_exists()

        try:
            self.messages_table = self.dynamodb.Table(messages_table_name)
            self.messages_table.load()
        except:
            # Create messages table
            self.messages_table = self.dynamodb.create_table(
                TableName=messages_table_name,
                KeySchema=[
                    {'AttributeName': 'chat_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'chat_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            self.messages_table.wait_until_exists()

    async def create_chat(
        self,
        chat_id: Optional[str] = None,
        user_id: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> Chat:
        """Create a new chat session."""
        if not chat_id:
            chat_id = str(uuid.uuid4())

        timestamp = datetime.utcnow().isoformat()

        item = {
            'id': chat_id,
            'created_at': timestamp,
            'updated_at': timestamp
        }

        if user_id:
            item['user_id'] = user_id
        if device_id:
            item['device_id'] = device_id

        self.chats_table.put_item(Item=item)

        return Chat(
            id=chat_id,
            user_id=user_id,
            device_id=device_id,
            created_at=datetime.fromisoformat(timestamp),
            updated_at=datetime.fromisoformat(timestamp)
        )

    async def get_chat(self, chat_id: str) -> Optional[Chat]:
        """Get a chat by ID."""
        response = self.chats_table.get_item(Key={'id': chat_id})

        if 'Item' not in response:
            return None

        item = response['Item']
        return Chat(
            id=item['id'],
            user_id=item.get('user_id'),
            device_id=item.get('device_id'),
            title=item.get('title'),
            created_at=datetime.fromisoformat(item['created_at']),
            updated_at=datetime.fromisoformat(item['updated_at'])
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
        timestamp_str = timestamp.isoformat()

        # Save message
        item = {
            'chat_id': chat_id,
            'timestamp': timestamp_str,
            'message_id': message_id,
            'role': role,
            'content': content
        }

        if citations:
            item['citations'] = json.dumps(citations)

        self.messages_table.put_item(Item=item)

        # Update chat's updated_at
        self.chats_table.update_item(
            Key={'id': chat_id},
            UpdateExpression='SET updated_at = :timestamp',
            ExpressionAttributeValues={
                ':timestamp': timestamp_str
            }
        )

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
        response = self.messages_table.query(
            KeyConditionExpression=Key('chat_id').eq(chat_id),
            ScanIndexForward=True  # Sort by timestamp ascending
        )

        messages = []
        for item in response.get('Items', []):
            citations = None
            if 'citations' in item:
                citations = json.loads(item['citations'])

            messages.append(Message(
                id=item.get('message_id'),
                chat_id=item['chat_id'],
                role=item['role'],
                content=item['content'],
                timestamp=datetime.fromisoformat(item['timestamp']),
                citations=citations
            ))

        return messages

    async def get_user_chats(
        self,
        user_id: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> List[Chat]:
        """Get all chats for a user or device."""
        chats = []

        if user_id:
            response = self.chats_table.query(
                IndexName='user_id_index',
                KeyConditionExpression=Key('user_id').eq(user_id)
            )
            for item in response.get('Items', []):
                chats.append(Chat(
                    id=item['id'],
                    user_id=item.get('user_id'),
                    device_id=item.get('device_id'),
                    title=item.get('title'),
                    created_at=datetime.fromisoformat(item['created_at']),
                    updated_at=datetime.fromisoformat(item['updated_at'])
                ))

        if device_id and not user_id:
            response = self.chats_table.query(
                IndexName='device_id_index',
                KeyConditionExpression=Key('device_id').eq(device_id)
            )
            for item in response.get('Items', []):
                chats.append(Chat(
                    id=item['id'],
                    user_id=item.get('user_id'),
                    device_id=item.get('device_id'),
                    title=item.get('title'),
                    created_at=datetime.fromisoformat(item['created_at']),
                    updated_at=datetime.fromisoformat(item['updated_at'])
                ))

        # Sort by updated_at descending
        chats.sort(key=lambda x: x.updated_at, reverse=True)
        return chats