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

### 4. Start the Backend Server
```bash
cd api
python start_server.py
```

The Python API will start on `http://localhost:5000`

### 5. Start the Frontend Development Server
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

## File Structure

```
project/
├── app/                    # Next.js app directory
├── components/             # React components
├── lib/                    # Utilities and API client
├── api/                    # Python backend
│   ├── video_converter.py  # Main Flask application
│   ├── requirements.txt    # Python dependencies
│   └── start_server.py     # Startup script
├── uploads/                # Temporary upload directory
└── outputs/                # Converted video output directory
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

## Troubleshooting

### Common Issues

1. **FFmpeg not found**: Install FFmpeg using the instructions above
2. **Python dependencies**: Run `pip install -r requirements.txt` in the api directory
3. **CORS errors**: Ensure the backend is running on port 5000
4. **File upload issues**: Check that uploads/ and outputs/ directories exist

### Logs

- Frontend logs appear in the browser console
- Backend logs appear in the terminal running the Python server

## Production Deployment

### Frontend
```bash
npm run build
npm start
```

### Backend
```bash
cd api
gunicorn -w 4 -b 0.0.0.0:5000 video_converter:app
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