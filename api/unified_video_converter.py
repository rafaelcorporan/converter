#!/usr/bin/env python3
"""
Unified Video Converter API - Consolidates best features from both implementations
"""

import os
import tempfile
import uuid
import subprocess
import re
import threading
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import ffmpeg
import logging

# Import centralized configuration
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global storage for conversion progress and results
conversion_progress = {}
conversion_results = {}

class UnifiedVideoConverter:
    """Unified video converter with multiple conversion methods and real-time progress"""
    
    def __init__(self):
        conv_config = config.get_conversion_config()
        self.supported_formats = conv_config.get('supported_formats', ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'])
        self.presets = conv_config.get('presets', {})
        self.default_settings = conv_config.get('default_settings', {})
    
    def get_video_duration(self, file_path: str) -> float:
        """Get video duration using ffprobe"""
        try:
            probe = ffmpeg.probe(file_path)
            for stream in probe['streams']:
                if 'duration' in stream:
                    return float(stream['duration'])
            
            if 'format' in probe and 'duration' in probe['format']:
                return float(probe['format']['duration'])
            
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 
                'format=duration', '-of', 'csv=p=0', file_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
                
        except Exception as e:
            logger.error(f"Error getting video duration: {e}")
        
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
            time_match = re.search(r'time=(\d{1,2}:\d{2}:\d{2}(?:\.\d{1,2})?)', line)
            if time_match:
                progress_data['time'] = time_match.group(1)
            
            fps_match = re.search(r'fps=(\d+\.?\d*)', line)
            if fps_match:
                try:
                    progress_data['fps'] = float(fps_match.group(1))
                except ValueError:
                    progress_data['fps'] = 0
            
            speed_match = re.search(r'speed=(\d+\.?\d*x)', line)
            if speed_match:
                progress_data['speed'] = speed_match.group(1)
            
            bitrate_match = re.search(r'bitrate=(\d+\.?\d*(?:k|M)?bits/s)', line)
            if bitrate_match:
                progress_data['bitrate'] = bitrate_match.group(1)
                
        except Exception as e:
            logger.warning(f"Error parsing FFmpeg progress line: {e}")
        
        return progress_data
    
    def apply_preset_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Apply preset settings if not using custom preset"""
        preset = settings.get('preset', 'web-standard')
        
        if preset != 'custom' and preset in self.presets:
            preset_settings = self.presets[preset].copy()
            # Override with any explicitly provided settings
            for key, value in settings.items():
                if key != 'preset':
                    preset_settings[key] = value
            preset_settings['preset'] = preset
            return preset_settings
        
        # Use provided settings or defaults
        final_settings = self.default_settings.copy()
        final_settings.update(settings)
        return final_settings
    
    def convert_video_with_progress(self, input_path: str, output_path: str, settings: Dict[str, Any], conversion_id: str) -> bool:
        """Convert video with real-time progress tracking using subprocess"""
        try:
            # Apply preset settings
            final_settings = self.apply_preset_settings(settings)
            
            # Get video duration for progress calculation
            duration = self.get_video_duration(input_path)
            if duration == 0:
                logger.error("Could not determine video duration")
                return False
            
            # Build FFmpeg command
            cmd = self._build_ffmpeg_command(input_path, output_path, final_settings)
            
            # Handle two-pass encoding
            if final_settings.get('twoPass', False):
                return self._convert_two_pass(cmd, conversion_id, duration)
            else:
                return self._convert_single_pass(cmd, conversion_id, duration)
                
        except Exception as e:
            logger.error(f"Error during conversion: {e}")
            return False
    
    def _build_ffmpeg_command(self, input_path: str, output_path: str, settings: Dict[str, Any]) -> List[str]:
        """Build FFmpeg command based on settings"""
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c:v', 'libvpx-vp9',
            '-crf', str(settings.get('quality', 32)),
            '-b:v', f"{settings.get('bitrate', 1000)}k",
            '-deadline', 'good',
            '-cpu-used', '4',
            '-auto-alt-ref', '0'
        ]
        
        # Apply resolution if specified
        resolution = settings.get('resolution', 'original')
        if resolution != 'original':
            if resolution in ['1920x1080', '1280x720', '854x480']:
                width, height = resolution.split('x')
                cmd.extend(['-vf', f'scale={width}:{height}'])
        
        # Apply frame rate
        frame_rate = settings.get('frameRate', 30)
        if frame_rate != 30:
            cmd.extend(['-r', str(frame_rate)])
        
        cmd.extend(['-f', 'webm', '-y', output_path])
        return cmd
    
    def _convert_single_pass(self, cmd: List[str], conversion_id: str, duration: float) -> bool:
        """Execute single-pass conversion with progress monitoring"""
        logger.info(f"Starting single pass conversion for {conversion_id}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
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
    
    def _convert_two_pass(self, base_cmd: List[str], conversion_id: str, duration: float) -> bool:
        """Execute two-pass conversion with progress monitoring"""
        # First pass
        first_pass_cmd = base_cmd[:-2] + ['-pass', '1', '-f', 'null', '-']
        logger.info(f"Starting first pass for {conversion_id}")
        
        process = subprocess.Popen(
            first_pass_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        # Monitor first pass progress (0-50%)
        for line in process.stderr:
            if 'time=' in line:
                progress_data = self.parse_ffmpeg_progress(line)
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
        output_path = base_cmd[-1]
        second_pass_cmd = base_cmd[:-2] + ['-pass', '2', output_path]
        logger.info(f"Starting second pass for {conversion_id}")
        
        process = subprocess.Popen(
            second_pass_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        # Monitor second pass progress (50-100%)
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

# Initialize converter
converter = UnifiedVideoConverter()

# Initialize directories from configuration
dirs_config = config.get_directories_config()
UPLOAD_DIR = Path(dirs_config.get('uploads', 'uploads'))
OUTPUT_DIR = Path(dirs_config.get('outputs', 'outputs'))
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    backend_config = config.get_backend_config()
    return jsonify({
        'status': 'healthy',
        'message': 'Unified Video Converter API is running',
        'version': '2.0.0',
        'config': {
            'port': backend_config.get('port'),
            'supported_formats': converter.supported_formats,
            'presets': list(converter.presets.keys())
        }
    })

@app.route('/api/convert', methods=['POST'])
def convert_video():
    """Convert uploaded video file with unified converter"""
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
        except:
            settings = {}
        
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
                    settings, 
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
            finally:
                # Clean up input file
                try:
                    os.remove(input_path)
                except:
                    pass
        
        thread = threading.Thread(target=conversion_worker)
        thread.start()
        
        return jsonify({
            'conversion_id': conversion_id,
            'message': 'Conversion started with unified converter'
        })
        
    except Exception as e:
        logger.error(f"Error in convert endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress/<conversion_id>', methods=['GET'])
def get_progress(conversion_id):
    """Get conversion progress"""
    if conversion_id not in conversion_progress:
        return jsonify({'error': 'Conversion not found'}), 404
    
    progress_data = conversion_progress[conversion_id].copy()
    
    # Add result data if completed
    if progress_data['status'] == 'completed' and conversion_id in conversion_results:
        progress_data.update(conversion_results[conversion_id])
    
    return jsonify(progress_data)

@app.route('/api/download/<conversion_id>', methods=['GET'])
def download_video(conversion_id):
    """Download converted video file"""
    if conversion_id not in conversion_results:
        return jsonify({'error': 'Conversion not found or not completed'}), 404
    
    result = conversion_results[conversion_id]
    output_path = result['output_path']
    
    if not os.path.exists(output_path):
        return jsonify({'error': 'Output file not found'}), 404
    
    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    # Validate configuration
    if not config.validate_config():
        logger.error("Configuration validation failed")
        exit(1)
    
    backend_config = config.get_backend_config()
    logger.info("Starting Unified Video Converter API...")
    logger.info(f"Upload directory: {UPLOAD_DIR}")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info(f"Configuration loaded from: {config.config_file}")
    
    app.run(
        host=backend_config.get('host', '0.0.0.0'),
        port=backend_config.get('port', 5001),
        debug=backend_config.get('debug', True)
    )