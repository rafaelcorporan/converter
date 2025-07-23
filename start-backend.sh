#!/bin/bash

# Simple backend starter script
echo "🐍 Starting Video Converter Backend..."

cd api

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Start the server
echo "🚀 Starting server on http://localhost:5001..."
python simple_video_converter.py