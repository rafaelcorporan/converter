# Professional Video Converter

A modern web application for converting MP4 videos to WebM (VP9) format with advanced encoding options. Built with Next.js frontend and Python Flask backend.

## Features

- **Real-time Video Conversion**: Convert MP4 to WebM using VP9 codec
- **Advanced Settings**: Quality, bitrate, resolution, frame rate, and two-pass encoding
- **Progress Tracking**: Real-time conversion progress with detailed statistics
- **Multiple Conversion Methods**: FFmpeg-python and MoviePy fallback
- **Modern UI**: Beautiful, responsive interface built with Tailwind CSS
- **File Management**: Upload, queue, and download converted files

## Tech Stack

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Radix UI** - Component library
- **React Hook Form** - Form handling

### Backend
- **Python Flask** - API server
- **FFmpeg-python** - Video processing
- **MoviePy** - Fallback video processing
- **CORS** - Cross-origin requests

## Prerequisites

1. **Node.js** (v18 or higher)
2. **Python** (v3.8 or higher)
3. **FFmpeg** - Required for video conversion

### Installing FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repository-url>
cd project
```

### 2. Install Frontend Dependencies
```bash
npm install
```

### 3. Install Backend Dependencies
```bash
cd api
python -m pip install -r requirements.txt
```

### 4. Configuration Setup (Optional)
The application uses centralized configuration with environment variable support:

```bash
# Copy environment template
cp .env.example .env

# Edit configuration if needed
# All settings have sensible defaults
```

### 5. Quick Start (Recommended)
Use the unified startup script that handles both frontend and backend:

```bash
./start-unified.sh
```

This will:
- ✅ Check FFmpeg installation
- ✅ Set up Python virtual environment
- ✅ Start unified backend on port 5001
- ✅ Start frontend on port 3000
- ✅ Validate service connectivity

### 6. Manual Start (Alternative)
#### Start Backend Server
```bash
cd api
python unified_video_converter.py
```

The Python API will start on `http://localhost:5001`

#### Start Frontend Development Server
In a new terminal:
```bash
npm run dev
```

The Next.js app will start on `http://localhost:3000`

## Usage

1. **Upload Files**: Drag and drop or select MP4 video files
2. **Configure Settings**: Adjust quality, bitrate, resolution, and other options
3. **Start Conversion**: Click "Start Conversion" to begin processing
4. **Monitor Progress**: Watch real-time conversion progress
5. **Download Results**: Download converted WebM files when complete

## API Endpoints

- `POST /api/convert` - Start video conversion
- `GET /api/progress/<conversion_id>` - Get conversion progress
- `GET /api/download/<conversion_id>` - Download converted file
- `GET /api/health` - Health check

## Conversion Settings

- **Preset**: web-standard, high-quality, max-compression, custom
- **Quality**: CRF value (0-63, lower = better quality)
- **Bitrate**: Target bitrate in kbps
- **Resolution**: original, 1920x1080, 1280x720, 854x480
- **Frame Rate**: FPS setting
- **Two-Pass**: Enable for better quality (slower)

## Architecture

### System Overview
```
┌─────────────────┐    HTTP/5001    ┌──────────────────┐
│  Next.js        │ ──────────────► │ Python Flask     │
│  Frontend       │                 │ Backend          │
│  (Port 3000)    │ ◄────────────── │ (Port 5001)      │
└─────────────────┘                 └──────────────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │ FFmpeg           │
                                    │ Video Processing │
                                    └──────────────────┘
```

### Configuration Management
- **Centralized Config**: `config.json` - Single source of truth
- **Environment Support**: `.env` - Development/production overrides
- **Validation**: Automated consistency checking across all components

### Service Communication
- **API Base URL**: Configurable via environment (`NEXT_PUBLIC_API_URL`)
- **Health Checks**: `/api/health` endpoint with monitoring
- **Error Handling**: Centralized error messages and connection validation

## File Structure

```
project/
├── app/                         # Next.js app directory
├── components/                  # React components
├── lib/                         # Utilities and API client
├── api/                         # Python backend
│   ├── unified_video_converter.py  # Unified Flask application
│   ├── config.py               # Configuration management
│   ├── requirements.txt        # Python dependencies
│   └── start_server.py         # Startup script
├── config.json                 # Centralized configuration
├── .env.example                # Environment template
├── tests/                      # Integration test suite
│   └── test_integration.py     # Comprehensive tests
├── monitor/                    # Health monitoring
│   └── health_monitor.py       # Real-time monitoring
├── scripts/                    # Validation scripts
│   ├── validate_config.py      # Configuration validation
│   └── pre-commit-check.sh     # Pre-commit hooks
├── logs/                       # Application logs
├── uploads/                    # Temporary upload directory
└── outputs/                    # Converted video output directory
```

## Development

### Frontend Development
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run lint         # Run ESLint
```

### Backend Development
```bash
cd api
python video_converter.py  # Start Flask server directly
```

## Testing & Validation

### Configuration Validation
Validate your configuration setup:

```bash
python3 scripts/validate_config.py
```

### Integration Testing
Run comprehensive integration tests:

```bash
python3 tests/test_integration.py
```

### Health Monitoring
Monitor service health in real-time:

```bash
python3 monitor/health_monitor.py
```

### Connectivity Testing
Quick connectivity test:

```bash
python3 tests/test_integration.py connectivity
```

## Troubleshooting

### Common Issues

1. **FFmpeg not found**: Install FFmpeg using the instructions above
2. **Python dependencies**: Run `pip install -r requirements.txt` in the api directory
3. **CORS errors**: Ensure the backend is running on port 5001
4. **File upload issues**: Check that uploads/ and outputs/ directories exist
5. **Configuration errors**: Run `python3 scripts/validate_config.py` to check configuration consistency
6. **Connection failures**: Use `./start-unified.sh` for automatic service startup and validation

### Advanced Troubleshooting

#### Service Health Check
```bash
curl http://localhost:5001/api/health
```

#### Configuration Validation
```bash
# Validate all configuration files
python3 scripts/validate_config.py

# Check port consistency
grep -r "5001" . --include="*.py" --include="*.ts" --include="*.js" --include="*.md"
```

#### Log Analysis
```bash
# Backend logs
tail -f logs/health_monitor.log

# Check service status
python3 monitor/health_monitor.py
```

### Logs

- Frontend logs appear in the browser console
- Backend logs appear in the terminal running the Python server
- Health monitoring logs: `logs/health_monitor.log`
- Configuration validation output: console

## Production Deployment

### Frontend
```bash
npm run build
npm start
```

### Backend
```bash
cd api
gunicorn -w 4 -b 0.0.0.0:5001 video_converter:app
```

## License

MIT License - see LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions, please open an issue on GitHub. 