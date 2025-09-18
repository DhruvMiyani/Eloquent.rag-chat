#!/bin/bash

echo "🚀 Testing Chat Functionality"
echo "=============================="

# Test 1: Health Check
echo "1️⃣ Testing API Health..."
curl -s http://localhost:8002/health | jq '.status'

# Test 2: Anonymous Auth
echo "2️⃣ Creating Anonymous User..."
AUTH_RESPONSE=$(curl -s -X POST http://localhost:8002/api/auth/anonymous)
TOKEN=$(echo $AUTH_RESPONSE | jq -r '.token')
USER_ID=$(echo $AUTH_RESPONSE | jq -r '.user.id')
echo "✅ User ID: $USER_ID"

# Test 3: Create Conversation
echo "3️⃣ Creating Conversation..."
CONV_RESPONSE=$(curl -s -X POST http://localhost:8002/api/chat/conversations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Chat"}')
CONV_ID=$(echo $CONV_RESPONSE | jq -r '.id')
echo "✅ Conversation ID: $CONV_ID"

# Test 4: Send Message
echo "4️⃣ Sending Message..."
MESSAGE_RESPONSE=$(curl -s -X POST http://localhost:8002/api/chat/conversations/$CONV_ID/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "How do I reset my password?"}')

echo "5️⃣ AI Response:"
echo $MESSAGE_RESPONSE | jq -r '.content'

# Test 5: Get Conversation History
echo "6️⃣ Getting Conversation History..."
HISTORY=$(curl -s -X GET http://localhost:8002/api/chat/conversations/$CONV_ID \
  -H "Authorization: Bearer $TOKEN")
MESSAGE_COUNT=$(echo $HISTORY | jq '.messages | length')
echo "✅ Messages in conversation: $MESSAGE_COUNT"

echo ""
echo "🎉 Chat functionality test complete!"
echo "Frontend: http://localhost:3001"
echo "Backend API: http://localhost:8002"
echo "API Docs: http://localhost:8002/docs"