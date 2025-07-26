#!/usr/bin/env python3
"""
Configuration validation script for Video Converter
Validates configuration consistency across all components and files
"""

import sys
import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import subprocess

class ConfigValidator:
    """Configuration validator for Video Converter system"""
    
    def __init__(self, project_root: Optional[str] = None):
        """Initialize configuration validator"""
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.config_file = self.project_root / "config.json"
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load main configuration file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.errors.append(f"Configuration file not found: {self.config_file}")
            return {}
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in configuration file: {e}")
            return {}
    
    def validate_config_structure(self) -> bool:
        """Validate configuration file structure"""
        print("🔧 Validating configuration structure...")
        
        if not self.config:
            return False
        
        # Required top-level sections
        required_sections = ['services', 'api', 'conversion', 'directories']
        for section in required_sections:
            if section not in self.config:
                self.errors.append(f"Missing required configuration section: {section}")
        
        # Validate services section
        if 'services' in self.config:
            services = self.config['services']
            if 'backend' not in services:
                self.errors.append("Missing backend configuration in services section")
            else:
                backend = services['backend']
                required_backend_keys = ['host', 'port', 'debug']
                for key in required_backend_keys:
                    if key not in backend:
                        self.errors.append(f"Missing backend configuration key: {key}")
        
        # Validate API section
        if 'api' in self.config:
            api = self.config['api']
            if 'base_url' not in api:
                self.errors.append("Missing base_url in api configuration")
            if 'endpoints' not in api:
                self.errors.append("Missing endpoints in api configuration")
        
        # Validate directories section
        if 'directories' in self.config:
            directories = self.config['directories']
            required_dirs = ['uploads', 'outputs']
            for dir_key in required_dirs:
                if dir_key not in directories:
                    self.errors.append(f"Missing directory configuration: {dir_key}")
        
        if not self.errors:
            print("✅ Configuration structure is valid")
            return True
        else:
            print(f"❌ Configuration structure validation failed")
            return False
    
    def validate_port_consistency(self) -> bool:
        """Validate port consistency across all files"""
        print("🔌 Validating port consistency...")
        
        if 'services' not in self.config or 'backend' not in self.config['services']:
            self.errors.append("Cannot validate ports - backend configuration missing")
            return False
        
        expected_port = self.config['services']['backend']['port']
        expected_url = f"http://localhost:{expected_port}"
        
        # Check API base URL consistency
        actual_url = self.config.get('api', {}).get('base_url', '')
        if actual_url != expected_url:
            self.errors.append(f"API base_url '{actual_url}' doesn't match backend port {expected_port}")
        
        # Files to check for port references
        files_to_check = [
            ('api/video_converter.py', rf'port\s*=\s*{expected_port}'),
            ('api/simple_video_converter.py', rf'port\s*=\s*{expected_port}'),
            ('api/unified_video_converter.py', rf'port.*{expected_port}'),
            ('lib/video-api.ts', rf'localhost:{expected_port}'),
            ('start.sh', rf'localhost:{expected_port}'),
            ('test-connection.js', rf'localhost:{expected_port}'),
            ('README.md', rf'localhost:{expected_port}')
        ]
        
        for file_path, pattern in files_to_check:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r') as f:
                        content = f.read()
                    
                    if not re.search(pattern, content):
                        self.warnings.append(f"Port {expected_port} not found in {file_path}")
                except Exception as e:
                    self.warnings.append(f"Could not check {file_path}: {e}")
            else:
                self.warnings.append(f"File not found for port check: {file_path}")
        
        if not self.errors:
            print(f"✅ Port consistency validated (port {expected_port})")
            return True
        else:
            print(f"❌ Port consistency validation failed")
            return False
    
    def validate_file_existence(self) -> bool:
        """Validate that all referenced files exist"""
        print("📁 Validating file existence...")
        
        # Required files
        required_files = [
            'config.json',
            'api/config.py',
            'api/unified_video_converter.py',
            'lib/video-api.ts',
            'start.sh',
            'start-unified.sh',
            '.env.example'
        ]
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                self.errors.append(f"Required file missing: {file_path}")
        
        # Check if directories exist
        directories = self.config.get('directories', {})
        for dir_name, dir_path in directories.items():
            full_dir_path = self.project_root / dir_path
            if not full_dir_path.exists():
                self.warnings.append(f"Directory '{dir_name}' does not exist: {dir_path}")
        
        if not self.errors:
            print("✅ File existence validated")
            return True
        else:
            print("❌ File existence validation failed")
            return False
    
    def validate_python_imports(self) -> bool:
        """Validate that Python files can import required modules"""
        print("🐍 Validating Python imports...")
        
        python_files = [
            'api/config.py',
            'api/unified_video_converter.py',
            'tests/test_integration.py',
            'monitor/health_monitor.py'
        ]
        
        for file_path in python_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    # Check syntax by compiling
                    with open(full_path, 'r') as f:
                        source = f.read()
                    
                    compile(source, str(full_path), 'exec')
                    
                except SyntaxError as e:
                    self.errors.append(f"Syntax error in {file_path}: {e}")
                except Exception as e:
                    self.warnings.append(f"Could not validate {file_path}: {e}")
        
        if not self.errors:
            print("✅ Python syntax validated")
            return True
        else:
            print("❌ Python syntax validation failed")
            return False
    
    def validate_environment_variables(self) -> bool:
        """Validate environment variable configuration"""
        print("🌍 Validating environment variables...")
        
        env_example_path = self.project_root / ".env.example"
        if not env_example_path.exists():
            self.errors.append(".env.example file missing")
            return False
        
        try:
            with open(env_example_path, 'r') as f:
                env_content = f.read()
            
            # Check for required environment variables
            required_env_vars = [
                'BACKEND_HOST',
                'BACKEND_PORT',
                'BACKEND_DEBUG',
                'API_BASE_URL',
                'NEXT_PUBLIC_API_URL'
            ]
            
            for env_var in required_env_vars:
                if env_var not in env_content:
                    self.warnings.append(f"Environment variable not in .env.example: {env_var}")
            
            # Validate that BACKEND_PORT matches config
            expected_port = self.config.get('services', {}).get('backend', {}).get('port')
            if expected_port:
                port_pattern = rf'BACKEND_PORT\s*=\s*{expected_port}'
                if not re.search(port_pattern, env_content):
                    self.warnings.append(f"BACKEND_PORT in .env.example doesn't match config ({expected_port})")
        
        except Exception as e:
            self.errors.append(f"Could not validate .env.example: {e}")
            return False
        
        if not self.errors:
            print("✅ Environment variables validated")
            return True
        else:
            print("❌ Environment variable validation failed")
            return False
    
    def validate_startup_scripts(self) -> bool:
        """Validate startup scripts"""
        print("🚀 Validating startup scripts...")
        
        scripts = [
            'start.sh',
            'start-unified.sh'
        ]
        
        for script in scripts:
            script_path = self.project_root / script
            if script_path.exists():
                # Check if executable
                if not os.access(script_path, os.X_OK):
                    self.warnings.append(f"Startup script not executable: {script}")
                
                # Check for basic syntax
                try:
                    result = subprocess.run(['bash', '-n', str(script_path)], 
                                          capture_output=True, text=True)
                    if result.returncode != 0:
                        self.errors.append(f"Bash syntax error in {script}: {result.stderr}")
                except Exception as e:
                    self.warnings.append(f"Could not validate {script}: {e}")
        
        if not self.errors:
            print("✅ Startup scripts validated")
            return True
        else:
            print("❌ Startup script validation failed")
            return False
    
    def validate_all(self) -> bool:
        """Run all validation checks"""
        print("🔍 Running comprehensive configuration validation...")
        print("=" * 60)
        
        validations = [
            self.validate_config_structure,
            self.validate_port_consistency,
            self.validate_file_existence,
            self.validate_python_imports,
            self.validate_environment_variables,
            self.validate_startup_scripts
        ]
        
        all_passed = True
        for validation in validations:
            try:
                if not validation():
                    all_passed = False
            except Exception as e:
                self.errors.append(f"Validation error: {e}")
                all_passed = False
            print()  # Add spacing between checks
        
        return all_passed
    
    def print_summary(self):
        """Print validation summary"""
        print("📋 VALIDATION SUMMARY")
        print("=" * 60)
        
        if not self.errors and not self.warnings:
            print("✅ All validations passed! Configuration is consistent.")
        else:
            if self.errors:
                print(f"❌ ERRORS ({len(self.errors)}):")
                for i, error in enumerate(self.errors, 1):
                    print(f"  {i}. {error}")
                print()
            
            if self.warnings:
                print(f"⚠️  WARNINGS ({len(self.warnings)}):")
                for i, warning in enumerate(self.warnings, 1):
                    print(f"  {i}. {warning}")
                print()
        
        # Configuration summary
        if self.config:
            backend_port = self.config.get('services', {}).get('backend', {}).get('port', 'unknown')
            api_url = self.config.get('api', {}).get('base_url', 'unknown')
            print(f"📊 CONFIGURATION SUMMARY:")
            print(f"  Backend Port: {backend_port}")
            print(f"  API Base URL: {api_url}")
            print(f"  Config File: {self.config_file}")

def main():
    """Main validation script"""
    print("⚙️  Video Converter Configuration Validator")
    print("=" * 60)
    
    # Allow custom project root as command line argument
    project_root = sys.argv[1] if len(sys.argv) > 1 else None
    
    validator = ConfigValidator(project_root)
    success = validator.validate_all()
    validator.print_summary()
    
    # Exit with appropriate code
    if success and not validator.errors:
        print("\n🎉 Configuration validation completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Configuration validation failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()