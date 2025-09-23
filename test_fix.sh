#!/bin/bash

echo "==================================="
echo "BodyScript Gallery Fix Test"
echo "==================================="
echo ""

# Check if backend is running
echo "1. Checking backend API on port 8001..."
curl -s http://localhost:8001/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ Backend is running"
else
    echo "   ✗ Backend is NOT running"
    echo "   Please start backend: cd backend && uvicorn app:app --port 8001"
fi

# Check if frontend server is running
echo ""
echo "2. Checking frontend server on port 8000..."
curl -s http://localhost:8000/ > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ Frontend server is running"
else
    echo "   ✗ Frontend server is NOT running"
    echo "   Please start frontend: cd frontend && python -m http.server 8000"
fi

# Check API data
echo ""
echo "3. Checking gallery API data..."
VIDEOS=$(curl -s http://localhost:8001/api/gallery 2>/dev/null | python -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('videos', [])))" 2>/dev/null)
if [ ! -z "$VIDEOS" ]; then
    echo "   ✓ Found $VIDEOS videos in gallery"
else
    echo "   ✗ Could not fetch gallery data"
fi

# Check if config is correct
echo ""
echo "4. Checking frontend config..."
API_URL=$(grep "window.API_URL" /Users/nrw/python/bodyscript/frontend/config.js | cut -d'"' -f2)
echo "   API_URL is set to: $API_URL"
if [ "$API_URL" = "http://localhost:8001" ]; then
    echo "   ✓ Config is correct"
else
    echo "   ✗ Config needs update to http://localhost:8001"
fi

echo ""
echo "==================================="
echo "INSTRUCTIONS:"
echo "==================================="
echo ""
echo "1. Open http://localhost:8000/ in your browser"
echo "2. Open browser console (F12)"
echo "3. You should see:"
echo "   - [DATA] Gallery data loaded"
echo "   - [RENDER] Videos with categories"
echo "4. Click any category tag (#dance, #yoga, #martial, #sports) to filter"
echo ""