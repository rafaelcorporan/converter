#!/bin/bash

# Professional Video Converter - Unified Startup Script
echo "🎬 Starting Professional Video Converter (Unified Version)..."

# Load environment variables if .env exists
if [ -f ".env" ]; then
    echo "📋 Loading environment configuration from .env"
    export $(cat .env | grep -v '^#' | xargs)
fi

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

# Start Python backend with unified converter
echo "🐍 Starting Python backend (Unified)..."
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

# Use environment variable for backend port, default to 5001
BACKEND_PORT=${BACKEND_PORT:-5001}

python unified_video_converter.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 5

# Check if backend is running using configured port
if ! curl -s http://localhost:${BACKEND_PORT}/api/health > /dev/null; then
    echo "❌ Backend failed to start on port ${BACKEND_PORT}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ Backend is running on http://localhost:${BACKEND_PORT}"

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
echo "   Backend:  http://localhost:${BACKEND_PORT}"
echo "   Config:   $([ -f config.json ] && echo 'config.json' || echo 'default')"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user to stop
wait