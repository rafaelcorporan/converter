#!/usr/bin/env python3
"""
Health monitoring system for Video Converter API
Provides continuous health checking, alerting, and service dependency validation
"""

import sys
import os
import time
import requests
import json
import logging
import threading
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))

@dataclass
class HealthStatus:
    """Health status data structure"""
    service_name: str
    is_healthy: bool
    response_time_ms: float
    status_code: Optional[int]
    timestamp: str
    error_message: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None

class HealthMonitor:
    """Continuous health monitoring system"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize health monitor"""
        self.config_path = config_path or self._find_config_file()
        self.config = self._load_config()
        self.base_url = self.config.get('api', {}).get('base_url', 'http://localhost:5001')
        
        # Monitoring configuration
        self.check_interval = 30  # seconds
        self.alert_threshold = 3  # consecutive failures before alert
        self.timeout = 5  # request timeout
        
        # State tracking
        self.consecutive_failures = 0
        self.last_successful_check = None
        self.health_history: List[HealthStatus] = []
        self.max_history = 100
        
        # Callbacks for alerts
        self.alert_callbacks: List[Callable[[HealthStatus], None]] = []
        
        # Setup logging
        self._setup_logging()
        
        # Monitoring thread
        self.monitoring_active = False
        self.monitor_thread = None
    
    def _find_config_file(self) -> str:
        """Find configuration file"""
        current_dir = Path(__file__).parent
        
        # Try parent directory (project root)
        config_path = current_dir.parent / "config.json"
        if config_path.exists():
            return str(config_path)
        
        # Try current directory
        config_path = current_dir / "config.json"
        if config_path.exists():
            return str(config_path)
        
        return str(current_dir.parent / "config.json")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.warning(f"Could not load config file {self.config_path}: {e}")
            return {
                'api': {'base_url': 'http://localhost:5001'},
                'services': {'backend': {'port': 5001}}
            }
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "health_monitor.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def add_alert_callback(self, callback: Callable[[HealthStatus], None]):
        """Add callback function for health alerts"""
        self.alert_callbacks.append(callback)
    
    def check_health(self) -> HealthStatus:
        """Perform single health check"""
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        try:
            response = requests.get(
                f"{self.base_url}/api/health", 
                timeout=self.timeout
            )
            response_time_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                health_data = response.json()
                
                status = HealthStatus(
                    service_name="video_converter_backend",
                    is_healthy=True,
                    response_time_ms=response_time_ms,
                    status_code=response.status_code,
                    timestamp=timestamp,
                    additional_info=health_data
                )
                
                self.consecutive_failures = 0
                self.last_successful_check = datetime.now()
                self.logger.info(f"Health check passed ({response_time_ms:.1f}ms)")
                
            else:
                status = HealthStatus(
                    service_name="video_converter_backend",
                    is_healthy=False,
                    response_time_ms=response_time_ms,
                    status_code=response.status_code,
                    timestamp=timestamp,
                    error_message=f"HTTP {response.status_code}: {response.text}"
                )
                
                self.consecutive_failures += 1
                self.logger.warning(f"Health check failed: HTTP {response.status_code}")
        
        except requests.exceptions.ConnectionError:
            response_time_ms = (time.time() - start_time) * 1000
            status = HealthStatus(
                service_name="video_converter_backend",
                is_healthy=False,
                response_time_ms=response_time_ms,
                status_code=None,
                timestamp=timestamp,
                error_message="Connection refused - service may be down"
            )
            
            self.consecutive_failures += 1
            self.logger.error("Health check failed: Connection refused")
        
        except requests.exceptions.Timeout:
            response_time_ms = self.timeout * 1000
            status = HealthStatus(
                service_name="video_converter_backend",
                is_healthy=False,
                response_time_ms=response_time_ms,
                status_code=None,
                timestamp=timestamp,
                error_message=f"Request timeout after {self.timeout}s"
            )
            
            self.consecutive_failures += 1
            self.logger.error(f"Health check failed: Timeout after {self.timeout}s")
        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            status = HealthStatus(
                service_name="video_converter_backend",
                is_healthy=False,
                response_time_ms=response_time_ms,
                status_code=None,
                timestamp=timestamp,
                error_message=f"Unexpected error: {str(e)}"
            )
            
            self.consecutive_failures += 1
            self.logger.error(f"Health check failed: {str(e)}")
        
        # Add to history
        self.health_history.append(status)
        if len(self.health_history) > self.max_history:
            self.health_history.pop(0)
        
        # Check if we should trigger alerts
        if not status.is_healthy and self.consecutive_failures >= self.alert_threshold:
            self._trigger_alerts(status)
        
        return status
    
    def _trigger_alerts(self, status: HealthStatus):
        """Trigger alert callbacks"""
        self.logger.critical(f"ALERT: Service unhealthy for {self.consecutive_failures} consecutive checks")
        
        for callback in self.alert_callbacks:
            try:
                callback(status)
            except Exception as e:
                self.logger.error(f"Alert callback failed: {e}")
    
    def start_monitoring(self):
        """Start continuous monitoring in background thread"""
        if self.monitoring_active:
            self.logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.logger.info(f"Health monitoring started (interval: {self.check_interval}s)")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self.logger.info("Health monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self.check_health()
                time.sleep(self.check_interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Monitor loop error: {e}")
                time.sleep(self.check_interval)
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health monitoring summary"""
        if not self.health_history:
            return {"status": "no_data", "message": "No health checks performed yet"}
        
        recent_checks = self.health_history[-10:]  # Last 10 checks
        healthy_count = sum(1 for check in recent_checks if check.is_healthy)
        avg_response_time = sum(check.response_time_ms for check in recent_checks) / len(recent_checks)
        
        last_check = self.health_history[-1]
        
        summary = {
            "current_status": "healthy" if last_check.is_healthy else "unhealthy",
            "last_check": last_check.timestamp,
            "consecutive_failures": self.consecutive_failures,
            "success_rate_recent": f"{(healthy_count / len(recent_checks)) * 100:.1f}%",
            "avg_response_time_ms": f"{avg_response_time:.1f}",
            "total_checks": len(self.health_history),
            "monitoring_active": self.monitoring_active,
            "last_error": last_check.error_message if not last_check.is_healthy else None,
            "last_successful_check": self.last_successful_check.isoformat() if self.last_successful_check else None
        }
        
        return summary
    
    def export_health_data(self, filepath: str):
        """Export health monitoring data to JSON file"""
        data = {
            "export_timestamp": datetime.now().isoformat(),
            "config": {
                "base_url": self.base_url,
                "check_interval": self.check_interval,
                "alert_threshold": self.alert_threshold
            },
            "summary": self.get_health_summary(),
            "health_history": [asdict(status) for status in self.health_history]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Health data exported to {filepath}")

def console_alert_callback(status: HealthStatus):
    """Simple console alert callback"""
    print(f"\n🚨 HEALTH ALERT 🚨")
    print(f"Service: {status.service_name}")
    print(f"Status: {'HEALTHY' if status.is_healthy else 'UNHEALTHY'}")
    print(f"Error: {status.error_message}")
    print(f"Time: {status.timestamp}")
    print("=" * 40)

def email_alert_callback(status: HealthStatus):
    """Email alert callback (placeholder - implement with your email service)"""
    # This is a placeholder - implement with your preferred email service
    print(f"📧 Would send email alert for {status.service_name} failure")

def slack_alert_callback(status: HealthStatus):
    """Slack alert callback (placeholder - implement with your Slack webhook)"""
    # This is a placeholder - implement with your Slack webhook URL
    print(f"💬 Would send Slack alert for {status.service_name} failure")

def main():
    """Main monitoring application"""
    print("🏥 Video Converter Health Monitor")
    print("=" * 40)
    
    monitor = HealthMonitor()
    
    # Add alert callbacks
    monitor.add_alert_callback(console_alert_callback)
    # monitor.add_alert_callback(email_alert_callback)  # Uncomment when implemented
    # monitor.add_alert_callback(slack_alert_callback)  # Uncomment when implemented
    
    try:
        # Perform initial health check
        print("Performing initial health check...")
        initial_status = monitor.check_health()
        
        if initial_status.is_healthy:
            print(f"✅ Service is healthy ({initial_status.response_time_ms:.1f}ms)")
        else:
            print(f"❌ Service is unhealthy: {initial_status.error_message}")
        
        # Start continuous monitoring
        print(f"\nStarting continuous monitoring (every {monitor.check_interval}s)...")
        print("Press Ctrl+C to stop monitoring")
        
        monitor.start_monitoring()
        
        # Keep running until interrupted
        while monitor.monitoring_active:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n📊 Health Monitoring Summary:")
        summary = monitor.get_health_summary()
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        # Export health data
        export_path = Path(__file__).parent.parent / "logs" / "health_export.json"
        monitor.export_health_data(str(export_path))
        
        monitor.stop_monitoring()
        print("\nHealth monitoring stopped.")

if __name__ == '__main__':
    main()