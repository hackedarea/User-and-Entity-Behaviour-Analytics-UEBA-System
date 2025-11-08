#!/usr/bin/env python3
"""
UEBA System - Enhanced Production Monitoring Dashboard
Comprehensive system monitoring with real-time metrics and alerting
"""

import time
import json
import psutil
import requests
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import threading
import logging
from collections import deque

class UEBAMonitor:
    def __init__(self):
        self.start_time = datetime.now()
        self.metrics_history = deque(maxlen=1000)  # Keep last 1000 metrics
        self.alerts = deque(maxlen=100)  # Keep last 100 alerts
        self.is_running = False
        self.monitoring_thread = None
        
        # Thresholds
        self.thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'disk_usage': 90.0,
            'elasticsearch_response_time': 5.0,  # seconds
            'grafana_response_time': 10.0,  # seconds
            'ml_processing_time': 30.0  # seconds
        }
        
        # Setup logging
        logging.basicConfig(
            filename='logs/monitoring.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Create logs directory if it doesn't exist
        Path('logs').mkdir(exist_ok=True)
    
    def check_system_health(self):
        """Check overall system health"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'system': self._get_system_metrics(),
            'services': self._check_services(),
            'ueba_components': self._check_ueba_components(),
            'storage': self._check_storage(),
            'network': self._check_network()
        }
        
        # Calculate overall health score
        health_score = self._calculate_health_score(metrics)
        metrics['health_score'] = health_score
        metrics['status'] = self._get_status_from_score(health_score)
        
        return metrics
    
    def _get_system_metrics(self):
        """Get system resource metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Check thresholds and create alerts
            if cpu_percent > self.thresholds['cpu_usage']:
                self._create_alert('HIGH_CPU', f'CPU usage: {cpu_percent:.1f}%')
            
            if memory.percent > self.thresholds['memory_usage']:
                self._create_alert('HIGH_MEMORY', f'Memory usage: {memory.percent:.1f}%')
            
            if disk.percent > self.thresholds['disk_usage']:
                self._create_alert('HIGH_DISK', f'Disk usage: {disk.percent:.1f}%')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_total': memory.total,
                'memory_available': memory.available,
                'memory_percent': memory.percent,
                'disk_total': disk.total,
                'disk_free': disk.free,
                'disk_percent': disk.percent,
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            }
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}")
            return {'error': str(e)}
    
    def _check_services(self):
        """Check external services status"""
        services = {}
        
        # Check Elasticsearch
        try:
            start_time = time.time()
            response = requests.get('http://localhost:9200/_cluster/health', timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                services['elasticsearch'] = {
                    'status': 'healthy',
                    'cluster_status': data.get('status', 'unknown'),
                    'response_time': response_time,
                    'nodes': data.get('number_of_nodes', 0),
                    'data_nodes': data.get('number_of_data_nodes', 0)
                }
                
                if response_time > self.thresholds['elasticsearch_response_time']:
                    self._create_alert('SLOW_ELASTICSEARCH', f'Response time: {response_time:.2f}s')
            else:
                services['elasticsearch'] = {'status': 'unhealthy', 'error': f'HTTP {response.status_code}'}
                self._create_alert('ELASTICSEARCH_DOWN', f'HTTP {response.status_code}')
                
        except Exception as e:
            services['elasticsearch'] = {'status': 'unreachable', 'error': str(e)}
            self._create_alert('ELASTICSEARCH_UNREACHABLE', str(e))
        
        # Check Grafana
        try:
            start_time = time.time()
            response = requests.get('http://localhost:3000/api/health', timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                services['grafana'] = {
                    'status': 'healthy',
                    'response_time': response_time
                }
                
                if response_time > self.thresholds['grafana_response_time']:
                    self._create_alert('SLOW_GRAFANA', f'Response time: {response_time:.2f}s')
            else:
                services['grafana'] = {'status': 'unhealthy', 'error': f'HTTP {response.status_code}'}
                self._create_alert('GRAFANA_DOWN', f'HTTP {response.status_code}')
                
        except Exception as e:
            services['grafana'] = {'status': 'unreachable', 'error': str(e)}
            self._create_alert('GRAFANA_UNREACHABLE', str(e))
        
        return services
    
    def _check_ueba_components(self):
        """Check UEBA system components"""
        components = {}
        
        # Check key files exist
        key_files = [
            'analytics-engine/optimized_ueba_system.py',
            'analytics-engine/automl_optimizer.py',
            'analytics-engine/advanced_ml_detector.py',
            'analytics-engine/realtime_ml_monitor.py'
        ]
        
        for file_path in key_files:
            components[Path(file_path).stem] = {
                'exists': Path(file_path).exists(),
                'size': Path(file_path).stat().st_size if Path(file_path).exists() else 0,
                'modified': Path(file_path).stat().st_mtime if Path(file_path).exists() else 0
            }
        
        # Check ML models
        ml_models_dir = Path('ml_models')
        if ml_models_dir.exists():
            model_files = list(ml_models_dir.glob('*.joblib'))
            components['ml_models'] = {
                'count': len(model_files),
                'total_size': sum(f.stat().st_size for f in model_files),
                'latest_model': max(model_files, key=lambda f: f.stat().st_mtime).name if model_files else None
            }
        else:
            components['ml_models'] = {'count': 0, 'total_size': 0, 'latest_model': None}
        
        return components
    
    def _check_storage(self):
        """Check storage usage and log files"""
        storage = {}
        
        # Check logs directory
        logs_dir = Path('logs')
        if logs_dir.exists():
            log_files = list(logs_dir.glob('*.log'))
            storage['logs'] = {
                'count': len(log_files),
                'total_size': sum(f.stat().st_size for f in log_files),
                'oldest_log': min(log_files, key=lambda f: f.stat().st_mtime).name if log_files else None,
                'newest_log': max(log_files, key=lambda f: f.stat().st_mtime).name if log_files else None
            }
        else:
            storage['logs'] = {'count': 0, 'total_size': 0}
        
        # Check data directory
        data_dir = Path('data')
        if data_dir.exists():
            data_size = sum(f.stat().st_size for f in data_dir.rglob('*') if f.is_file())
            storage['data'] = {'total_size': data_size}
        else:
            storage['data'] = {'total_size': 0}
        
        return storage
    
    def _check_network(self):
        """Check network connectivity and interfaces"""
        network = {}
        
        try:
            # Network interfaces
            interfaces = psutil.net_if_addrs()
            network['interfaces'] = {
                name: len(addrs) for name, addrs in interfaces.items()
            }
            
            # Network IO stats
            net_io = psutil.net_io_counters()
            network['io'] = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
            
        except Exception as e:
            network['error'] = str(e)
        
        return network
    
    def _calculate_health_score(self, metrics):
        """Calculate overall health score (0-100)"""
        score = 100
        
        # System metrics impact
        system = metrics.get('system', {})
        if 'cpu_percent' in system:
            if system['cpu_percent'] > 90:
                score -= 20
            elif system['cpu_percent'] > 70:
                score -= 10
        
        if 'memory_percent' in system:
            if system['memory_percent'] > 90:
                score -= 20
            elif system['memory_percent'] > 70:
                score -= 10
        
        if 'disk_percent' in system:
            if system['disk_percent'] > 95:
                score -= 25
            elif system['disk_percent'] > 80:
                score -= 10
        
        # Services impact
        services = metrics.get('services', {})
        for service, status in services.items():
            if status.get('status') == 'unhealthy':
                score -= 15
            elif status.get('status') == 'unreachable':
                score -= 25
        
        return max(0, score)
    
    def _get_status_from_score(self, score):
        """Convert health score to status"""
        if score >= 90:
            return 'EXCELLENT'
        elif score >= 75:
            return 'GOOD'
        elif score >= 60:
            return 'WARNING'
        elif score >= 40:
            return 'CRITICAL'
        else:
            return 'EMERGENCY'
    
    def _create_alert(self, alert_type, message):
        """Create an alert"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'message': message,
            'severity': self._get_alert_severity(alert_type)
        }
        
        self.alerts.append(alert)
        self.logger.warning(f"ALERT: {alert_type} - {message}")
        
        # Print critical alerts immediately
        if alert['severity'] == 'CRITICAL':
            print(f"🚨 CRITICAL ALERT: {alert_type} - {message}")
    
    def _get_alert_severity(self, alert_type):
        """Get alert severity level"""
        critical_alerts = ['ELASTICSEARCH_UNREACHABLE', 'GRAFANA_UNREACHABLE', 'HIGH_DISK']
        warning_alerts = ['HIGH_CPU', 'HIGH_MEMORY', 'SLOW_ELASTICSEARCH', 'SLOW_GRAFANA']
        
        if alert_type in critical_alerts:
            return 'CRITICAL'
        elif alert_type in warning_alerts:
            return 'WARNING'
        else:
            return 'INFO'
    
    def start_monitoring(self, interval=30):
        """Start continuous monitoring"""
        self.is_running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, args=(interval,))
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        print(f"✅ Monitoring started with {interval}s interval")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        print("⏹️ Monitoring stopped")
    
    def _monitoring_loop(self, interval):
        """Main monitoring loop"""
        while self.is_running:
            try:
                metrics = self.check_system_health()
                self.metrics_history.append(metrics)
                
                # Log metrics
                self.logger.info(f"Health check: {metrics['status']} (Score: {metrics['health_score']})")
                
                time.sleep(interval)
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def get_recent_metrics(self, count=10):
        """Get recent metrics"""
        return list(self.metrics_history)[-count:]
    
    def get_recent_alerts(self, count=20):
        """Get recent alerts"""
        return list(self.alerts)[-count:]
    
    def export_metrics(self, filename=None):
        """Export metrics to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/metrics_export_{timestamp}.json"
        
        export_data = {
            'export_time': datetime.now().isoformat(),
            'uptime': str(datetime.now() - self.start_time),
            'metrics_count': len(self.metrics_history),
            'alerts_count': len(self.alerts),
            'recent_metrics': list(self.metrics_history),
            'recent_alerts': list(self.alerts)
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"📊 Metrics exported to: {filename}")
        return filename
    
    def display_dashboard(self):
        """Display live dashboard"""
        try:
            while True:
                # Clear screen
                os.system('cls' if os.name == 'nt' else 'clear')
                
                # Get current metrics
                metrics = self.check_system_health()
                
                # Display header
                print("="*80)
                print("🛡️  UEBA SYSTEM - LIVE MONITORING DASHBOARD")
                print("="*80)
                print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | ⏱️ Uptime: {datetime.now() - self.start_time}")
                print(f"🏥 Health Score: {metrics['health_score']}/100 | Status: {metrics['status']}")
                print()
                
                # System metrics
                system = metrics.get('system', {})
                print("💻 SYSTEM RESOURCES:")
                print(f"   🔥 CPU: {system.get('cpu_percent', 0):.1f}%")
                print(f"   🧠 Memory: {system.get('memory_percent', 0):.1f}%")
                print(f"   💾 Disk: {system.get('disk_percent', 0):.1f}%")
                print()
                
                # Services status
                services = metrics.get('services', {})
                print("🔧 SERVICES STATUS:")
                for service, status in services.items():
                    status_icon = "✅" if status.get('status') == 'healthy' else "❌"
                    response_time = status.get('response_time', 0)
                    print(f"   {status_icon} {service.title()}: {status.get('status', 'unknown')} ({response_time:.2f}s)")
                print()
                
                # Recent alerts
                recent_alerts = self.get_recent_alerts(5)
                print("🚨 RECENT ALERTS:")
                if recent_alerts:
                    for alert in recent_alerts:
                        severity_icon = "🔴" if alert['severity'] == 'CRITICAL' else "🟡" if alert['severity'] == 'WARNING' else "🟢"
                        timestamp = datetime.fromisoformat(alert['timestamp']).strftime('%H:%M:%S')
                        print(f"   {severity_icon} [{timestamp}] {alert['type']}: {alert['message']}")
                else:
                    print("   ✅ No recent alerts")
                print()
                
                print("💡 Press Ctrl+C to exit dashboard")
                print("="*80)
                
                # Wait before next update
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\n👋 Dashboard closed by user")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='UEBA System Enhanced Monitoring')
    parser.add_argument('--mode', choices=['dashboard', 'check', 'monitor', 'export'], 
                       default='dashboard', help='Monitoring mode')
    parser.add_argument('--interval', type=int, default=30, 
                       help='Monitoring interval in seconds')
    parser.add_argument('--duration', type=int, help='Monitor duration in minutes')
    
    args = parser.parse_args()
    
    monitor = UEBAMonitor()
    
    if args.mode == 'check':
        # Single health check
        metrics = monitor.check_system_health()
        print(json.dumps(metrics, indent=2))
    
    elif args.mode == 'monitor':
        # Continuous monitoring
        print("🔄 Starting continuous monitoring...")
        monitor.start_monitoring(args.interval)
        
        try:
            if args.duration:
                time.sleep(args.duration * 60)
                monitor.stop_monitoring()
            else:
                # Run indefinitely
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            monitor.stop_monitoring()
    
    elif args.mode == 'export':
        # Export current metrics
        filename = monitor.export_metrics()
        print(f"✅ Metrics exported to {filename}")
    
    else:
        # Dashboard mode (default)
        monitor.display_dashboard()

if __name__ == "__main__":
    import os
    main()