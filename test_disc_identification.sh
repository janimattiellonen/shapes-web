#!/bin/bash

# Test script for disc identification system
# Usage: ./test_disc_identification.sh <path_to_disc_image>

API_URL="http://localhost:8000"

if [ -z "$1" ]; then
    echo "Usage: $0 <path_to_disc_image>"
    echo "Example: $0 ~/Downloads/my_disc.jpg"
    exit 1
fi

IMAGE_PATH="$1"

if [ ! -f "$IMAGE_PATH" ]; then
    echo "Error: Image file not found: $IMAGE_PATH"
    exit 1
fi

echo "=================================================="
echo "Disc Identification System - Test Script"
echo "=================================================="
echo ""

# Test 1: Health Check
echo "1. Testing health endpoint..."
curl -s "${API_URL}/discs/identification/health/check" | python3 -m json.tool
echo ""
echo ""

# Test 2: Register the disc
echo "2. Registering disc..."
RESPONSE=$(curl -s -X POST "${API_URL}/discs/identification/register" \
  -F "image=@${IMAGE_PATH}" \
  -F "owner_name=Test User" \
  -F "owner_contact=test@example.com" \
  -F "disc_model=Clash Vanilla" \
  -F "disc_color=White" \
  -F "notes=Test disc from image")

echo "$RESPONSE" | python3 -m json.tool
DISC_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['disc_id'])" 2>/dev/null)
echo ""
echo "Disc registered with ID: $DISC_ID"
echo ""
echo ""

# Test 3: Search for the same disc
echo "3. Searching for the disc (should find high similarity)..."
curl -s -X POST "${API_URL}/discs/identification/search" \
  -F "image=@${IMAGE_PATH}" \
  -F "top_k=5" \
  -F "min_similarity=0.5" | python3 -m json.tool
echo ""
echo ""

# Test 4: Get disc info
if [ ! -z "$DISC_ID" ]; then
    echo "4. Getting disc information..."
    curl -s "${API_URL}/discs/identification/${DISC_ID}" | python3 -m json.tool
    echo ""
    echo ""
fi

echo "=================================================="
echo "Test Complete!"
echo "=================================================="
echo ""
echo "You can view the API docs at: ${API_URL}/docs"
echo "Your disc ID: $DISC_ID"
echo ""
