#!/usr/bin/env python3
"""
Centralized configuration management for Video Converter API
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    """Centralized configuration manager with environment variable support"""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration from file and environment variables"""
        self.config_file = config_file or self._find_config_file()
        self._config = self._load_config()
        self._apply_env_overrides()
    
    def _find_config_file(self) -> str:
        """Find configuration file in project hierarchy"""
        current_dir = Path(__file__).parent
        
        # Try current directory first (api/)
        config_path = current_dir / "config.json"
        if config_path.exists():
            return str(config_path)
        
        # Try parent directory (project root)
        config_path = current_dir.parent / "config.json"
        if config_path.exists():
            return str(config_path)
        
        # Default fallback
        return str(current_dir.parent / "config.json")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load config file {self.config_file}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if file is missing"""
        return {
            "services": {
                "backend": {"host": "0.0.0.0", "port": 5001, "debug": True},
                "frontend": {"host": "localhost", "port": 3000}
            },
            "api": {
                "base_url": "http://localhost:5001",
                "endpoints": {
                    "health": "/api/health",
                    "convert": "/api/convert",
                    "progress": "/api/progress",
                    "download": "/api/download"
                }
            },
            "conversion": {
                "supported_formats": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"],
                "default_settings": {
                    "quality": 32,
                    "bitrate": 1000,
                    "resolution": "original",
                    "frameRate": 30,
                    "preset": "web-standard",
                    "twoPass": False
                }
            },
            "directories": {
                "uploads": "uploads",
                "outputs": "outputs"
            }
        }
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides"""
        # Service configuration
        if os.getenv('BACKEND_HOST'):
            self._config['services']['backend']['host'] = os.getenv('BACKEND_HOST')
        if os.getenv('BACKEND_PORT'):
            self._config['services']['backend']['port'] = int(os.getenv('BACKEND_PORT'))
        if os.getenv('BACKEND_DEBUG'):
            self._config['services']['backend']['debug'] = os.getenv('BACKEND_DEBUG').lower() == 'true'
        
        # API configuration
        if os.getenv('API_BASE_URL'):
            self._config['api']['base_url'] = os.getenv('API_BASE_URL')
        
        # Directory configuration
        if os.getenv('UPLOAD_DIR'):
            self._config['directories']['uploads'] = os.getenv('UPLOAD_DIR')
        if os.getenv('OUTPUT_DIR'):
            self._config['directories']['outputs'] = os.getenv('OUTPUT_DIR')
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'services.backend.port')"""
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_backend_config(self) -> Dict[str, Any]:
        """Get backend service configuration"""
        return self._config.get('services', {}).get('backend', {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration"""
        return self._config.get('api', {})
    
    def get_conversion_config(self) -> Dict[str, Any]:
        """Get conversion configuration"""
        return self._config.get('conversion', {})
    
    def get_directories_config(self) -> Dict[str, Any]:
        """Get directories configuration"""
        return self._config.get('directories', {})
    
    def validate_config(self) -> bool:
        """Validate configuration integrity"""
        required_keys = [
            'services.backend.host',
            'services.backend.port',
            'api.base_url',
            'directories.uploads',
            'directories.outputs'
        ]
        
        for key_path in required_keys:
            if self.get(key_path) is None:
                print(f"Error: Missing required configuration: {key_path}")
                return False
        
        return True

# Global configuration instance
config = Config()