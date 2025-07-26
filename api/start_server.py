#!/usr/bin/env python3
"""
Startup script for the Video Converter API
"""

import subprocess
import sys
import os
from pathlib import Path

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ FFmpeg is installed")
            return True
    except FileNotFoundError:
        pass
    
    print("✗ FFmpeg is not installed. Please install FFmpeg first:")
    print("  macOS: brew install ffmpeg")
    print("  Ubuntu/Debian: sudo apt install ffmpeg")
    print("  Windows: Download from https://ffmpeg.org/download.html")
    return False

def install_dependencies():
    """Install Python dependencies"""
    print("Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

def start_server():
    """Start the Flask server"""
    print("Starting Video Converter API...")
    try:
        subprocess.run([sys.executable, 'unified_video_converter.py'], check=True)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to start server: {e}")

def main():
    print("Video Converter API Startup")
    print("=" * 30)
    
    # Check if we're in the right directory
    if not Path('unified_video_converter.py').exists():
        print("✗ Please run this script from the api/ directory")
        sys.exit(1)
    
    # Check FFmpeg
    if not check_ffmpeg():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Start server
    start_server()

if __name__ == '__main__':
    main() 