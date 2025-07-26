import os
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any
import json
import time
import threading
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import ffmpeg
from moviepy.editor import VideoFileClip
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global storage for conversion progress
conversion_progress = {}
conversion_results = {}

# Ensure upload and output directories exist
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

class VideoConverter:
    def __init__(self):
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
    
    def convert_with_ffmpeg(self, input_path: str, output_path: str, settings: Dict[str, Any], progress_callback=None) -> bool:
        """Convert video using FFmpeg-python with VP9 codec"""
        try:
            # Parse settings
            quality = settings.get('quality', 32)
            bitrate = settings.get('bitrate', 1000)
            resolution = settings.get('resolution', 'original')
            frame_rate = settings.get('frameRate', 30)
            two_pass = settings.get('twoPass', False)
            
            # Build FFmpeg command
            input_stream = ffmpeg.input(input_path)
            
            # Apply video filters based on settings
            video_stream = input_stream.video
            
            # Apply resolution if specified
            if resolution != 'original':
                if resolution == '1920x1080':
                    video_stream = video_stream.filter('scale', 1920, 1080)
                elif resolution == '1280x720':
                    video_stream = video_stream.filter('scale', 1280, 720)
                elif resolution == '854x480':
                    video_stream = video_stream.filter('scale', 854, 480)
            
            # Apply frame rate
            if frame_rate != 30:
                video_stream = video_stream.filter('fps', fps=frame_rate)
            
            # Configure output
            output_args = {
                'vcodec': 'libvpx-vp9',
                'crf': quality,
                'b:v': f'{bitrate}k',
                'deadline': 'good',
                'cpu-used': 4,
                'row-mt': 1,
                'tile-columns': 2,
                'frame-parallel': 1
            }
            
            # Add two-pass encoding if enabled
            if two_pass:
                # First pass
                first_pass_output = str(OUTPUT_DIR / f"pass1_{uuid.uuid4()}.webm")
                first_pass = (
                    video_stream
                    .output(first_pass_output, **output_args, **{"pass": 1})
                    .overwrite_output()
                )
                
                if progress_callback:
                    progress_callback(25)
                
                ffmpeg.run(first_pass, quiet=True)
                
                # Second pass
                second_pass = (
                    video_stream
                    .output(output_path, **output_args, **{"pass": 2})
                    .overwrite_output()
                )
                
                if progress_callback:
                    progress_callback(75)
                
                ffmpeg.run(second_pass, quiet=True)
                
                # Clean up first pass file
                os.remove(first_pass_output)
            else:
                # Single pass encoding
                output = (
                    video_stream
                    .output(output_path, **output_args)
                    .overwrite_output()
                )
                
                ffmpeg.run(output, quiet=True)
            
            if progress_callback:
                progress_callback(100)
            
            return True
            
        except Exception as e:
            logger.error(f"FFmpeg conversion error: {str(e)}")
            return False
    
    def convert_with_moviepy(self, input_path: str, output_path: str, settings: Dict[str, Any], progress_callback=None) -> bool:
        """Convert video using MoviePy (fallback method)"""
        try:
            # Parse settings
            quality = settings.get('quality', 32)
            bitrate = settings.get('bitrate', 1000)
            resolution = settings.get('resolution', 'original')
            frame_rate = settings.get('frameRate', 30)
            
            # Load video
            clip = VideoFileClip(input_path)
            
            if progress_callback:
                progress_callback(30)
            
            # Apply resolution if specified
            if resolution != 'original':
                if resolution == '1920x1080':
                    clip = clip.resize((1920, 1080))
                elif resolution == '1280x720':
                    clip = clip.resize((1280, 720))
                elif resolution == '854x480':
                    clip = clip.resize((854, 480))
            
            # Apply frame rate
            if frame_rate != 30:
                clip = clip.set_fps(frame_rate)
            
            if progress_callback:
                progress_callback(60)
            
            # Write output with VP9 codec
            clip.write_videofile(
                output_path,
                codec='libvpx-vp9',
                bitrate=f'{bitrate}k',
                preset='medium',
                threads=4,
                verbose=False,
                logger=None
            )
            
            if progress_callback:
                progress_callback(100)
            
            clip.close()
            return True
            
        except Exception as e:
            logger.error(f"MoviePy conversion error: {str(e)}")
            return False

converter = VideoConverter()

def update_progress(conversion_id: str, progress: int):
    """Update conversion progress"""
    conversion_progress[conversion_id] = progress
    logger.info(f"Conversion {conversion_id}: {progress}%")

@app.route('/api/convert', methods=['POST'])
def convert_video():
    """Convert uploaded video file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        settings = json.loads(request.form.get('settings', '{}'))
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Generate unique conversion ID
        conversion_id = str(uuid.uuid4())
        
        # Save uploaded file
        input_filename = f"{conversion_id}_{file.filename}"
        input_path = UPLOAD_DIR / input_filename
        file.save(input_path)
        
        # Generate output filename
        output_filename = f"{conversion_id}_converted.webm"
        output_path = OUTPUT_DIR / output_filename
        
        # Initialize progress
        conversion_progress[conversion_id] = 0
        conversion_results[conversion_id] = {
            'status': 'processing',
            'input_path': str(input_path),
            'output_path': str(output_path),
            'error': None
        }
        
        def progress_callback(progress: int):
            update_progress(conversion_id, progress)
        
        # Start conversion in background thread
        def convert_thread():
            try:
                # Try FFmpeg first, fallback to MoviePy
                success = converter.convert_with_ffmpeg(
                    str(input_path), 
                    str(output_path), 
                    settings, 
                    progress_callback
                )
                
                if not success:
                    logger.info(f"FFmpeg failed, trying MoviePy for {conversion_id}")
                    success = converter.convert_with_moviepy(
                        str(input_path), 
                        str(output_path), 
                        settings, 
                        progress_callback
                    )
                
                if success:
                    conversion_results[conversion_id]['status'] = 'completed'
                    # Get file sizes
                    input_size = os.path.getsize(input_path)
                    output_size = os.path.getsize(output_path)
                    conversion_results[conversion_id].update({
                        'input_size': input_size,
                        'output_size': output_size,
                        'compression_ratio': round((1 - output_size / input_size) * 100, 2)
                    })
                else:
                    conversion_results[conversion_id].update({
                        'status': 'error',
                        'error': 'Conversion failed'
                    })
                
            except Exception as e:
                logger.error(f"Conversion error for {conversion_id}: {str(e)}")
                conversion_results[conversion_id].update({
                    'status': 'error',
                    'error': str(e)
                })
            finally:
                # Clean up input file
                try:
                    os.remove(input_path)
                except:
                    pass
        
        thread = threading.Thread(target=convert_thread)
        thread.start()
        
        return jsonify({
            'conversion_id': conversion_id,
            'message': 'Conversion started'
        })
        
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress/<conversion_id>', methods=['GET'])
def get_progress(conversion_id):
    """Get conversion progress"""
    progress = conversion_progress.get(conversion_id, 0)
    result = conversion_results.get(conversion_id, {})
    
    return jsonify({
        'conversion_id': conversion_id,
        'progress': progress,
        'status': result.get('status', 'unknown'),
        'error': result.get('error'),
        'compression_ratio': result.get('compression_ratio'),
        'input_size': result.get('input_size'),
        'output_size': result.get('output_size')
    })

@app.route('/api/download/<conversion_id>', methods=['GET'])
def download_converted(conversion_id):
    """Download converted video file"""
    result = conversion_results.get(conversion_id)
    
    if not result or result['status'] != 'completed':
        return jsonify({'error': 'File not ready or not found'}), 404
    
    output_path = result['output_path']
    
    if not os.path.exists(output_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(
        output_path,
        as_attachment=True,
        download_name=f"converted_{conversion_id}.webm",
        mimetype='video/webm'
    )

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Video converter API is running'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 