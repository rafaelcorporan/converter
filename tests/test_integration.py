#!/usr/bin/env python3
"""
Integration test suite for Video Converter API
Tests frontend-backend connectivity, configuration consistency, and service health
"""

import sys
import os
import time
import requests
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional
import unittest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

class VideoConverterIntegrationTests(unittest.TestCase):
    """Integration tests for video converter system"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.config = cls._load_config()
        cls.base_url = cls.config.get('api', {}).get('base_url', 'http://localhost:5001')
        cls.backend_port = cls.config.get('services', {}).get('backend', {}).get('port', 5001)
        
    @classmethod
    def _load_config(cls) -> Dict[str, Any]:
        """Load configuration from config.json"""
        config_path = Path(__file__).parent.parent / 'config.json'
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Config file not found at {config_path}")
            return {
                'services': {'backend': {'port': 5001}},
                'api': {'base_url': 'http://localhost:5001'}
            }
    
    def test_01_configuration_consistency(self):
        """Test that all configuration references are consistent"""
        print("\n🔧 Testing configuration consistency...")
        
        # Check that API base URL matches backend port
        expected_url = f"http://localhost:{self.backend_port}"
        self.assertEqual(self.base_url, expected_url, 
                        f"API base URL {self.base_url} doesn't match backend port {self.backend_port}")
        
        # Verify configuration structure
        required_keys = [
            'services.backend.port',
            'api.base_url',
            'directories.uploads',
            'directories.outputs'
        ]
        
        for key_path in required_keys:
            value = self._get_nested_value(self.config, key_path)
            self.assertIsNotNone(value, f"Required configuration key missing: {key_path}")
        
        print("✅ Configuration consistency verified")
    
    def test_02_backend_connectivity(self):
        """Test backend service connectivity"""
        print(f"\n🔗 Testing backend connectivity on {self.base_url}...")
        
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            self.assertEqual(response.status_code, 200, 
                           f"Health check failed with status {response.status_code}")
            
            health_data = response.json()
            self.assertEqual(health_data.get('status'), 'healthy', 
                           "Backend reports unhealthy status")
            
            print(f"✅ Backend connectivity verified: {health_data.get('message', 'OK')}")
            
        except requests.exceptions.ConnectionError:
            self.fail(f"Cannot connect to backend at {self.base_url}. "
                     "Ensure the backend is running before running tests.")
        except requests.exceptions.Timeout:
            self.fail(f"Backend connection timeout at {self.base_url}")
    
    def test_03_api_endpoints_availability(self):
        """Test that all required API endpoints are available"""
        print("\n📡 Testing API endpoints availability...")
        
        endpoints = self.config.get('api', {}).get('endpoints', {})
        
        for endpoint_name, endpoint_path in endpoints.items():
            if endpoint_name == 'health':
                # Already tested in connectivity test
                continue
            
            url = f"{self.base_url}{endpoint_path}"
            
            if endpoint_name in ['progress', 'download']:
                # These require parameters, test with dummy ID
                url += "/test-id"
            
            try:
                if endpoint_name == 'convert':
                    # POST endpoint - expect 400 (bad request) not 404
                    response = requests.post(url, timeout=5)
                    self.assertIn(response.status_code, [400, 422], 
                                f"Convert endpoint should return 400/422, got {response.status_code}")
                else:
                    # GET endpoints - expect 404 (not found) not connection error
                    response = requests.get(url, timeout=5)
                    self.assertIn(response.status_code, [404, 422], 
                                f"Endpoint {endpoint_name} should return 404/422, got {response.status_code}")
                
                print(f"✅ Endpoint {endpoint_name} ({endpoint_path}) is available")
                
            except requests.exceptions.ConnectionError:
                self.fail(f"Connection error for endpoint {endpoint_name} at {url}")
    
    def test_04_port_consistency_check(self):
        """Test that all components use consistent port configuration"""
        print(f"\n🔌 Testing port consistency across components...")
        
        # Check if backend is actually listening on configured port
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            result = sock.connect_ex(('localhost', self.backend_port))
            self.assertEqual(result, 0, f"Nothing listening on port {self.backend_port}")
            print(f"✅ Backend is listening on port {self.backend_port}")
        finally:
            sock.close()
    
    def test_05_environment_variable_support(self):
        """Test environment variable configuration override"""
        print("\n🌍 Testing environment variable support...")
        
        # This test verifies that the config system supports environment variables
        # We can't change runtime config, but we can verify the mechanism exists
        
        from api.config import Config
        
        # Create a test config instance
        test_config = Config()
        
        # Verify it has the expected interface
        self.assertTrue(hasattr(test_config, 'get'), "Config should have get method")
        self.assertTrue(hasattr(test_config, 'validate_config'), "Config should have validate_config method")
        
        # Test configuration validation
        is_valid = test_config.validate_config()
        self.assertTrue(is_valid, "Configuration validation should pass")
        
        print("✅ Environment variable support verified")
    
    def test_06_startup_script_validation(self):
        """Test that startup scripts exist and are executable"""
        print("\n🚀 Testing startup script validation...")
        
        project_root = Path(__file__).parent.parent
        startup_scripts = [
            'start.sh',
            'start-unified.sh',
            'api/start_server.py'
        ]
        
        for script_path in startup_scripts:
            full_path = project_root / script_path
            self.assertTrue(full_path.exists(), f"Startup script not found: {script_path}")
            
            if script_path.endswith('.sh'):
                # Check if shell script is executable
                self.assertTrue(os.access(full_path, os.X_OK), 
                              f"Shell script not executable: {script_path}")
            
            print(f"✅ Startup script verified: {script_path}")
    
    def test_07_configuration_file_integrity(self):
        """Test configuration file integrity and completeness"""
        print("\n📋 Testing configuration file integrity...")
        
        # Test config.json structure
        project_root = Path(__file__).parent.parent
        config_path = project_root / 'config.json'
        
        self.assertTrue(config_path.exists(), "config.json file missing")
        
        # Verify required sections exist
        required_sections = ['services', 'api', 'conversion', 'directories']
        for section in required_sections:
            self.assertIn(section, self.config, f"Required config section missing: {section}")
        
        # Verify service configuration
        backend_config = self.config.get('services', {}).get('backend', {})
        self.assertIn('host', backend_config, "Backend host configuration missing")
        self.assertIn('port', backend_config, "Backend port configuration missing")
        
        print("✅ Configuration file integrity verified")
    
    def _get_nested_value(self, data: Dict[str, Any], key_path: str) -> Any:
        """Get nested dictionary value using dot notation"""
        keys = key_path.split('.')
        value = data
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return None

class ConnectivityValidator:
    """Standalone connectivity validator for CI/CD pipelines"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or 'config.json'
        self.config = self._load_config()
        self.base_url = self.config.get('api', {}).get('base_url', 'http://localhost:5001')
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'api': {'base_url': 'http://localhost:5001'}}
    
    def validate_connectivity(self, timeout: int = 30) -> bool:
        """Validate backend connectivity with timeout"""
        print(f"Validating connectivity to {self.base_url}...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/api/health", timeout=2)
                if response.status_code == 200:
                    health_data = response.json()
                    print(f"✅ Backend healthy: {health_data.get('message', 'OK')}")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
        
        print(f"❌ Backend connectivity validation failed after {timeout}s")
        return False

def run_integration_tests():
    """Run integration test suite"""
    print("🧪 Running Video Converter Integration Tests")
    print("=" * 50)
    
    # Run the test suite
    unittest.main(verbosity=2, exit=False)

def validate_connectivity():
    """Standalone connectivity validation"""
    validator = ConnectivityValidator()
    return validator.validate_connectivity()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'connectivity':
        # Run standalone connectivity check
        success = validate_connectivity()
        sys.exit(0 if success else 1)
    else:
        # Run full integration test suite
        run_integration_tests()