import os
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any
import json
import time
import threading
import subprocess
import re
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import ffmpeg
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

class SimpleVideoConverter:
    def __init__(self):
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
    
    def get_video_duration(self, file_path: str) -> float:
        """Get video duration using ffprobe"""
        try:
            probe = ffmpeg.probe(file_path)
            # Try to get duration from multiple sources
            for stream in probe['streams']:
                if 'duration' in stream:
                    return float(stream['duration'])
            
            # Fallback to format duration
            if 'format' in probe and 'duration' in probe['format']:
                return float(probe['format']['duration'])
            
            # Last resort: use ffprobe with different format
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 
                'format=duration', '-of', 'csv=p=0', file_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
                
        except Exception as e:
            logger.error(f"Error getting video duration: {e}")
        
        # If all else fails, return a reasonable default (assume 60 seconds)
        logger.warning(f"Could not determine video duration for {file_path}, using default")
        return 60.0
    
    def parse_ffmpeg_progress(self, line: str) -> Dict[str, Any]:
        """Parse FFmpeg progress output"""
        progress_data = {
            'progress': 0,
            'time': '00:00:00',
            'fps': 0,
            'speed': '0x',
            'eta': '00:00:00'
        }
        
        try:
            # Parse time progress (more flexible regex)
            time_match = re.search(r'time=(\d{1,2}:\d{2}:\d{2}(?:\.\d{1,2})?)', line)
            if time_match:
                progress_data['time'] = time_match.group(1)
            
            # Parse FPS (e.g., "fps=24.5")
            fps_match = re.search(r'fps=(\d+\.?\d*)', line)
            if fps_match:
                try:
                    progress_data['fps'] = float(fps_match.group(1))
                except ValueError:
                    progress_data['fps'] = 0
            
            # Parse speed (e.g., "speed=1.2x")
            speed_match = re.search(r'speed=(\d+\.?\d*x)', line)
            if speed_match:
                progress_data['speed'] = speed_match.group(1)
            
            # Parse bitrate (e.g., "bitrate=1000.0kbits/s")
            bitrate_match = re.search(r'bitrate=(\d+\.?\d*(?:k|M)?bits/s)', line)
            if bitrate_match:
                progress_data['bitrate'] = bitrate_match.group(1)
                
        except Exception as e:
            logger.warning(f"Error parsing FFmpeg progress line: {e}")
        
        return progress_data
    
    def convert_video_with_progress(self, input_path: str, output_path: str, settings: Dict[str, Any], conversion_id: str) -> bool:
        """Convert video with real-time progress tracking"""
        try:
            # Get video duration for progress calculation
            duration = self.get_video_duration(input_path)
            if duration == 0:
                logger.error("Could not determine video duration")
                return False
            
            # Build FFmpeg command
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-c:v', 'libvpx-vp9',
                '-crf', str(settings.get('quality', 32)),
                '-b:v', f"{settings.get('bitrate', 1000)}k",
                '-preset', 'medium',
                '-deadline', 'good',
                '-cpu-used', '4',
                '-auto-alt-ref', '0',
                '-f', 'webm',
                '-y',  # Overwrite output file
                output_path
            ]
            
            # Add two-pass encoding if enabled
            if settings.get('twoPass', False):
                # First pass
                first_pass_cmd = cmd[:-2] + ['-pass', '1', '-f', 'null', '-']
                logger.info(f"Starting first pass for {conversion_id}")
                
                process = subprocess.Popen(
                    first_pass_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    bufsize=1
                )
                
                # Monitor first pass progress
                for line in process.stderr:
                    if 'time=' in line:
                        progress_data = self.parse_ffmpeg_progress(line)
                        # First pass is 50% of total progress
                        try:
                            time_parts = progress_data['time'].split(':')
                            hours = float(time_parts[0]) if len(time_parts) > 2 else 0
                            minutes = float(time_parts[1]) if len(time_parts) > 1 else 0
                            seconds = float(time_parts[2] if len(time_parts) > 2 else time_parts[-1])
                            current_time = hours * 3600 + minutes * 60 + seconds
                            progress = min(50, (current_time / duration) * 50)
                        except (ValueError, IndexError):
                            progress = 0
                        
                        conversion_progress[conversion_id] = {
                            'progress': progress,
                            'status': 'processing',
                            'time': progress_data['time'],
                            'fps': progress_data['fps'],
                            'speed': progress_data['speed'],
                            'eta': progress_data.get('eta', '00:00:00')
                        }
                
                process.wait()
                if process.returncode != 0:
                    logger.error(f"First pass failed for {conversion_id}")
                    return False
                
                # Second pass
                second_pass_cmd = cmd[:-2] + ['-pass', '2', output_path]
                logger.info(f"Starting second pass for {conversion_id}")
                
                process = subprocess.Popen(
                    second_pass_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    bufsize=1
                )
                
                # Monitor second pass progress (50% to 100%)
                for line in process.stderr:
                    if 'time=' in line:
                        progress_data = self.parse_ffmpeg_progress(line)
                        try:
                            time_parts = progress_data['time'].split(':')
                            hours = float(time_parts[0]) if len(time_parts) > 2 else 0
                            minutes = float(time_parts[1]) if len(time_parts) > 1 else 0
                            seconds = float(time_parts[2] if len(time_parts) > 2 else time_parts[-1])
                            current_time = hours * 3600 + minutes * 60 + seconds
                            progress = 50 + min(50, (current_time / duration) * 50)
                        except (ValueError, IndexError):
                            progress = 50
                        
                        conversion_progress[conversion_id] = {
                            'progress': progress,
                            'status': 'processing',
                            'time': progress_data['time'],
                            'fps': progress_data['fps'],
                            'speed': progress_data['speed'],
                            'eta': progress_data.get('eta', '00:00:00')
                        }
                
                process.wait()
                return process.returncode == 0
            else:
                # Single pass encoding
                logger.info(f"Starting single pass conversion for {conversion_id}")
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    bufsize=1
                )
                
                # Monitor progress
                for line in process.stderr:
                    if 'time=' in line:
                        progress_data = self.parse_ffmpeg_progress(line)
                        try:
                            time_parts = progress_data['time'].split(':')
                            hours = float(time_parts[0]) if len(time_parts) > 2 else 0
                            minutes = float(time_parts[1]) if len(time_parts) > 1 else 0
                            seconds = float(time_parts[2] if len(time_parts) > 2 else time_parts[-1])
                            current_time = hours * 3600 + minutes * 60 + seconds
                            progress = min(100, (current_time / duration) * 100)
                        except (ValueError, IndexError):
                            progress = 0
                        
                        conversion_progress[conversion_id] = {
                            'progress': progress,
                            'status': 'processing',
                            'time': progress_data['time'],
                            'fps': progress_data['fps'],
                            'speed': progress_data['speed'],
                            'eta': progress_data.get('eta', '00:00:00')
                        }
                
                process.wait()
                return process.returncode == 0
                
        except Exception as e:
            logger.error(f"Error during conversion: {e}")
            return False

converter = SimpleVideoConverter()

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'message': 'Video converter API is running',
        'status': 'healthy'
    })

@app.route('/api/convert', methods=['POST'])
def convert_video():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get conversion settings
        settings = request.form.get('settings', '{}')
        try:
            settings = json.loads(settings)
            # Extract all settings
            conversion_settings = {
                'quality': settings.get('quality', 32),
                'bitrate': settings.get('bitrate', 1000),
                'twoPass': settings.get('twoPass', False),
                'resolution': settings.get('resolution', 'original'),
                'frameRate': settings.get('frameRate', 30),
                'preset': settings.get('preset', 'web-standard')
            }
            # Apply preset logic if not custom
            if conversion_settings['preset'] != 'custom':
                if conversion_settings['preset'] == 'web-standard':
                    conversion_settings.update({'quality': 32, 'bitrate': 2000, 'resolution': 'original', 'frameRate': 30, 'twoPass': False})
                elif conversion_settings['preset'] == 'high-quality':
                    conversion_settings.update({'quality': 18, 'bitrate': 4000, 'resolution': '1920x1080', 'frameRate': 30, 'twoPass': True})
                elif conversion_settings['preset'] == 'max-compression':
                    conversion_settings.update({'quality': 45, 'bitrate': 1000, 'resolution': '854x480', 'frameRate': 24, 'twoPass': True})
        except:
            conversion_settings = {
                'quality': 32,
                'bitrate': 1000,
                'twoPass': False,
                'resolution': 'original',
                'frameRate': 30,
                'preset': 'web-standard'
            }
        
        # Generate unique ID
        conversion_id = str(uuid.uuid4())
        
        # Save uploaded file
        input_filename = f"{conversion_id}_{file.filename}"
        input_path = UPLOAD_DIR / input_filename
        file.save(input_path)
        
        # Set output path
        output_filename = f"{conversion_id}_{Path(file.filename).stem}.webm"
        output_path = OUTPUT_DIR / output_filename
        
        # Initialize progress
        conversion_progress[conversion_id] = {
            'progress': 0,
            'status': 'processing',
            'time': '00:00:00',
            'fps': 0,
            'speed': '0x',
            'eta': '00:00:00'
        }
        
        # Start conversion in background thread
        def conversion_worker():
            try:
                success = converter.convert_video_with_progress(
                    str(input_path), 
                    str(output_path), 
                    conversion_settings, 
                    conversion_id
                )
                
                if success and os.path.exists(output_path):
                    # Get file sizes
                    input_size = os.path.getsize(input_path)
                    output_size = os.path.getsize(output_path)
                    
                    conversion_results[conversion_id] = {
                        'status': 'completed',
                        'output_path': str(output_path),
                        'input_size': input_size,
                        'output_size': output_size,
                        'compression_ratio': (1 - output_size / input_size) * 100
                    }
                    
                    conversion_progress[conversion_id]['status'] = 'completed'
                    conversion_progress[conversion_id]['progress'] = 100
                else:
                    error_msg = "Conversion failed - output file not created"
                    if not success:
                        error_msg = "FFmpeg conversion process failed"
                    
                    conversion_progress[conversion_id]['status'] = 'error'
                    conversion_progress[conversion_id]['progress'] = 0
                    conversion_progress[conversion_id]['error'] = error_msg
                    
            except Exception as e:
                error_msg = f"Conversion error: {str(e)}"
                logger.error(error_msg)
                conversion_progress[conversion_id]['status'] = 'error'
                conversion_progress[conversion_id]['progress'] = 0
                conversion_progress[conversion_id]['error'] = error_msg
        
        thread = threading.Thread(target=conversion_worker)
        thread.start()
        
        return jsonify({
            'conversion_id': conversion_id,
            'message': 'Conversion started'
        })
        
    except Exception as e:
        logger.error(f"Error in convert endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress/<conversion_id>', methods=['GET'])
def get_progress(conversion_id):
    if conversion_id not in conversion_progress:
        return jsonify({'error': 'Conversion not found'}), 404
    
    progress_data = conversion_progress[conversion_id].copy()
    
    # Add result data if completed
    if progress_data['status'] == 'completed' and conversion_id in conversion_results:
        progress_data.update(conversion_results[conversion_id])
    
    return jsonify(progress_data)

@app.route('/api/download/<conversion_id>', methods=['GET'])
def download_video(conversion_id):
    if conversion_id not in conversion_results:
        return jsonify({'error': 'Conversion not found or not completed'}), 404
    
    result = conversion_results[conversion_id]
    output_path = result['output_path']
    
    if not os.path.exists(output_path):
        return jsonify({'error': 'Output file not found'}), 404
    
    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    logger.info("Starting Video Converter API...")
    logger.info(f"Upload directory: {UPLOAD_DIR}")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    app.run(host='0.0.0.0', port=5001, debug=True) 