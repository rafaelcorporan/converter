#!/bin/bash

# Professional Video Converter - Startup Script
echo "🎬 Starting Professional Video Converter..."

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ FFmpeg is not installed. Please install FFmpeg first:"
    echo "   macOS: brew install ffmpeg"
    echo "   Ubuntu/Debian: sudo apt install ffmpeg"
    echo "   Windows: Download from https://ffmpeg.org/download.html"
    exit 1
fi

echo "✅ FFmpeg is installed"

# Function to cleanup background processes
cleanup() {
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start Python backend
echo "🐍 Starting Python backend..."
cd api

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Setting up Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

python unified_video_converter.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 5

# Check if backend is running
if ! curl -s http://localhost:5001/api/health > /dev/null; then
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ Backend is running on http://localhost:5001"

# Start Next.js frontend
echo "⚛️  Starting Next.js frontend..."
npm run dev &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 5

echo "✅ Frontend is running on http://localhost:3000"
echo ""
echo "🎉 Video Converter is ready!"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user to stop
wait 