#!/usr/bin/env python3
"""
UEBA System Validator and Health Monitor v3.0
==============================================
Comprehensive system validation, health monitoring, and configuration verification.
Replaces multiple status check scripts with a unified, intelligent solution.

Features:
- Real-time system health monitoring
- Configuration validation
- Performance metrics
- Field mapping verification
- Data quality assessment
- Service dependency checking

Author: UEBA System v3.0
Date: October 5, 2025
"""

import requests
import json
import subprocess
import time
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import threading
import argparse

class UEBASystemValidator:
    """
    Comprehensive UEBA system validator and health monitor
    """
    
    def __init__(self):
        self.services = {
            'elasticsearch': {'url': 'http://localhost:9200', 'port': 9200, 'container': 'elasticsearch-ueba'},
            'grafana': {'url': 'http://localhost:3000', 'port': 3000, 'container': 'grafana-ueba'}
        }
        
        self.health_status = {}
        self.performance_metrics = {}
        self.validation_results = {}
        
        # Colors for output
        self.colors = {
            'red': '\033[0;31m',
            'green': '\033[0;32m',
            'yellow': '\033[1;33m',
            'blue': '\033[0;34m',
            'cyan': '\033[0;36m',
            'purple': '\033[0;35m',
            'nc': '\033[0m'
        }
    
    def print_colored(self, message: str, color: str = 'nc'):
        """Print colored message"""
        print(f"{self.colors.get(color, self.colors['nc'])}{message}{self.colors['nc']}")
    
    def print_header(self, title: str):
        """Print section header"""
        self.print_colored(f"\n{'='*60}", 'cyan')
        self.print_colored(f"🛡️ {title}", 'cyan')
        self.print_colored(f"{'='*60}", 'cyan')
    
    def check_container_runtime(self) -> Tuple[bool, str]:
        """Check if Docker or Podman is available"""
        for runtime in ['docker', 'podman']:
            try:
                result = subprocess.run([runtime, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return True, runtime
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        return False, "none"
    
    def check_container_status(self, container_name: str, runtime: str) -> Dict[str, any]:
        """Check individual container status"""
        try:
            # Check if container exists and is running
            result = subprocess.run([runtime, 'ps', '--filter', f'name={container_name}', '--format', 'json'],
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                container_info = json.loads(result.stdout.strip().split('\n')[0])
                return {
                    'running': True,
                    'status': container_info.get('Status', 'unknown'),
                    'created': container_info.get('CreatedAt', 'unknown'),
                    'ports': container_info.get('Ports', 'unknown')
                }
            else:
                return {'running': False, 'status': 'not found'}
                
        except Exception as e:
            return {'running': False, 'status': f'error: {e}'}
    
    def check_service_health(self, service_name: str, service_config: Dict) -> Dict[str, any]:
        """Check individual service health"""
        health_data = {
            'name': service_name,
            'accessible': False,
            'response_time': None,
            'status_code': None,
            'details': {}
        }
        
        try:
            start_time = time.time()
            
            # Basic connectivity check
            if service_name == 'elasticsearch':
                response = requests.get(f"{service_config['url']}/_cluster/health", timeout=10)
                health_data['accessible'] = response.status_code == 200
                health_data['status_code'] = response.status_code
                health_data['response_time'] = time.time() - start_time
                
                if response.status_code == 200:
                    cluster_health = response.json()
                    health_data['details'] = {
                        'cluster_status': cluster_health.get('status', 'unknown'),
                        'number_of_nodes': cluster_health.get('number_of_nodes', 0),
                        'active_shards': cluster_health.get('active_shards', 0)
                    }
            
            elif service_name == 'grafana':
                response = requests.get(f"{service_config['url']}/api/health", timeout=10)
                health_data['accessible'] = response.status_code == 200
                health_data['status_code'] = response.status_code
                health_data['response_time'] = time.time() - start_time
                
                if response.status_code == 200:
                    grafana_health = response.json()
                    health_data['details'] = {
                        'database': grafana_health.get('database', 'unknown'),
                        'version': grafana_health.get('version', 'unknown')
                    }
                    
        except requests.RequestException as e:
            health_data['error'] = str(e)
        
        return health_data
    
    def check_data_availability(self) -> Dict[str, any]:
        """Check data availability and quality"""
        data_status = {
            'indices_exist': False,
            'document_count': 0,
            'recent_data': False,
            'field_mappings_correct': False,
            'details': {}
        }
        
        try:
            # Check if index exists
            response = requests.get("http://localhost:9200/nginx-parsed-logs", timeout=10)
            if response.status_code == 200:
                data_status['indices_exist'] = True
                
                # Get document count
                count_response = requests.get("http://localhost:9200/nginx-parsed-logs/_count", timeout=10)
                if count_response.status_code == 200:
                    count_data = count_response.json()
                    data_status['document_count'] = count_data.get('count', 0)
                
                # Check for recent data (last hour)
                recent_query = {
                    "query": {
                        "range": {
                            "@timestamp": {
                                "gte": "now-1h"
                            }
                        }
                    },
                    "size": 0
                }
                
                recent_response = requests.post("http://localhost:9200/nginx-parsed-logs/_search",
                                              json=recent_query, timeout=10)
                if recent_response.status_code == 200:
                    recent_data = recent_response.json()
                    recent_count = recent_data['hits']['total']['value']
                    data_status['recent_data'] = recent_count > 0
                    data_status['details']['recent_documents'] = recent_count
                
                # Check field mappings
                mapping_response = requests.get("http://localhost:9200/nginx-parsed-logs/_mapping", timeout=10)
                if mapping_response.status_code == 200:
                    mapping_data = mapping_response.json()
                    properties = mapping_data['nginx-parsed-logs']['mappings']['properties']
                    
                    # Check for essential fields
                    essential_fields = ['ip', 'status', 'method', 'url', 'user_agent', 'size', '@timestamp']
                    missing_fields = [field for field in essential_fields if field not in properties]
                    
                    data_status['field_mappings_correct'] = len(missing_fields) == 0
                    data_status['details']['available_fields'] = list(properties.keys())
                    data_status['details']['missing_fields'] = missing_fields
                    
        except Exception as e:
            data_status['error'] = str(e)
        
        return data_status
    
    def check_dashboard_status(self) -> Dict[str, any]:
        """Check Grafana dashboard status"""
        dashboard_status = {
            'grafana_accessible': False,
            'ueba_dashboards': 0,
            'datasource_configured': False,
            'details': {}
        }
        
        try:
            # Check Grafana accessibility
            auth = ('admin', 'admin')
            response = requests.get("http://localhost:3000/api/health", timeout=10)
            dashboard_status['grafana_accessible'] = response.status_code == 200
            
            if response.status_code == 200:
                # Check for UEBA dashboards
                search_response = requests.get("http://localhost:3000/api/search?query=UEBA",
                                             auth=auth, timeout=10)
                if search_response.status_code == 200:
                    dashboards = search_response.json()
                    dashboard_status['ueba_dashboards'] = len(dashboards)
                    dashboard_status['details']['dashboard_titles'] = [d.get('title', 'Unknown') for d in dashboards]
                
                # Check datasource
                datasource_response = requests.get("http://localhost:3000/api/datasources",
                                                 auth=auth, timeout=10)
                if datasource_response.status_code == 200:
                    datasources = datasource_response.json()
                    elasticsearch_sources = [ds for ds in datasources if 'elasticsearch' in ds.get('type', '').lower()]
                    dashboard_status['datasource_configured'] = len(elasticsearch_sources) > 0
                    dashboard_status['details']['datasources'] = len(elasticsearch_sources)
                    
        except Exception as e:
            dashboard_status['error'] = str(e)
        
        return dashboard_status
    
    def get_performance_metrics(self) -> Dict[str, any]:
        """Get system performance metrics"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'elasticsearch': {},
            'system': {}
        }
        
        try:
            # Elasticsearch metrics
            stats_response = requests.get("http://localhost:9200/_nodes/stats", timeout=10)
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                node_stats = list(stats_data['nodes'].values())[0] if stats_data['nodes'] else {}
                
                if node_stats:
                    metrics['elasticsearch'] = {
                        'heap_used_percent': node_stats.get('jvm', {}).get('mem', {}).get('heap_used_percent', 0),
                        'uptime': node_stats.get('jvm', {}).get('uptime_in_millis', 0),
                        'cpu_percent': node_stats.get('process', {}).get('cpu', {}).get('percent', 0)
                    }
            
            # System metrics (basic)
            try:
                # Memory usage
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                    for line in meminfo.split('\n'):
                        if 'MemAvailable:' in line:
                            available_mb = int(line.split()[1]) // 1024
                            metrics['system']['memory_available_mb'] = available_mb
                            break
                
                # Load average
                with open('/proc/loadavg', 'r') as f:
                    load_avg = f.read().split()
                    metrics['system']['load_1min'] = float(load_avg[0])
                    
            except:
                pass  # System metrics are optional
                
        except Exception as e:
            metrics['error'] = str(e)
        
        return metrics
    
    def run_comprehensive_check(self) -> Dict[str, any]:
        """Run comprehensive system validation"""
        self.print_header("UEBA System Comprehensive Validation")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'unknown',
            'container_runtime': {},
            'containers': {},
            'services': {},
            'data': {},
            'dashboards': {},
            'performance': {},
            'recommendations': []
        }
        
        # Check container runtime
        self.print_colored("🔍 Checking container runtime...", 'blue')
        runtime_available, runtime_type = self.check_container_runtime()
        results['container_runtime'] = {
            'available': runtime_available,
            'type': runtime_type
        }
        
        if runtime_available:
            self.print_colored(f"✅ Container runtime: {runtime_type}", 'green')
            
            # Check containers
            self.print_colored("🔍 Checking containers...", 'blue')
            for service_name, service_config in self.services.items():
                container_status = self.check_container_status(service_config['container'], runtime_type)
                results['containers'][service_name] = container_status
                
                if container_status['running']:
                    self.print_colored(f"✅ {service_name} container: Running", 'green')
                else:
                    self.print_colored(f"❌ {service_name} container: {container_status['status']}", 'red')
        else:
            self.print_colored("❌ No container runtime available", 'red')
            results['recommendations'].append("Install Docker or Podman container runtime")
        
        # Check services
        self.print_colored("🔍 Checking service health...", 'blue')
        for service_name, service_config in self.services.items():
            health_data = self.check_service_health(service_name, service_config)
            results['services'][service_name] = health_data
            
            if health_data['accessible']:
                self.print_colored(f"✅ {service_name}: Accessible ({health_data['response_time']:.2f}s)", 'green')
            else:
                self.print_colored(f"❌ {service_name}: Not accessible", 'red')
                results['recommendations'].append(f"Check {service_name} service configuration")
        
        # Check data
        self.print_colored("🔍 Checking data availability...", 'blue')
        data_status = self.check_data_availability()
        results['data'] = data_status
        
        if data_status['indices_exist']:
            self.print_colored(f"✅ Data index exists: {data_status['document_count']} documents", 'green')
            if data_status['recent_data']:
                self.print_colored(f"✅ Recent data available", 'green')
            else:
                self.print_colored(f"⚠️ No recent data (last hour)", 'yellow')
                results['recommendations'].append("Generate fresh data for real-time monitoring")
        else:
            self.print_colored("❌ Data index not found", 'red')
            results['recommendations'].append("Run data generation to create initial dataset")
        
        # Check dashboards
        self.print_colored("🔍 Checking dashboard status...", 'blue')
        dashboard_status = self.check_dashboard_status()
        results['dashboards'] = dashboard_status
        
        if dashboard_status['grafana_accessible']:
            self.print_colored(f"✅ Grafana accessible: {dashboard_status['ueba_dashboards']} UEBA dashboards", 'green')
            if dashboard_status['datasource_configured']:
                self.print_colored("✅ Elasticsearch datasource configured", 'green')
            else:
                self.print_colored("⚠️ Elasticsearch datasource not configured", 'yellow')
                results['recommendations'].append("Configure Elasticsearch datasource in Grafana")
        else:
            self.print_colored("❌ Grafana not accessible", 'red')
            results['recommendations'].append("Check Grafana service status")
        
        # Get performance metrics
        self.print_colored("🔍 Collecting performance metrics...", 'blue')
        performance_metrics = self.get_performance_metrics()
        results['performance'] = performance_metrics
        
        if 'elasticsearch' in performance_metrics:
            es_metrics = performance_metrics['elasticsearch']
            heap_usage = es_metrics.get('heap_used_percent', 0)
            if heap_usage > 0:
                self.print_colored(f"📊 Elasticsearch heap usage: {heap_usage}%", 'blue')
                if heap_usage > 80:
                    results['recommendations'].append("Elasticsearch heap usage is high - consider increasing memory")
        
        # Determine overall status
        critical_issues = 0
        if not results['container_runtime']['available']:
            critical_issues += 1
        if not all(container['running'] for container in results['containers'].values()):
            critical_issues += 1
        if not all(service['accessible'] for service in results['services'].values()):
            critical_issues += 1
        
        if critical_issues == 0:
            results['overall_status'] = 'healthy'
            self.print_colored("\n🎉 Overall Status: HEALTHY", 'green')
        elif critical_issues <= 2:
            results['overall_status'] = 'degraded'
            self.print_colored("\n⚠️ Overall Status: DEGRADED", 'yellow')
        else:
            results['overall_status'] = 'critical'
            self.print_colored("\n❌ Overall Status: CRITICAL", 'red')
        
        # Show recommendations
        if results['recommendations']:
            self.print_colored("\n📋 RECOMMENDATIONS:", 'purple')
            for i, recommendation in enumerate(results['recommendations'], 1):
                self.print_colored(f"   {i}. {recommendation}", 'yellow')
        
        return results
    
    def monitor_continuous(self, interval: int = 30):
        """Run continuous monitoring"""
        self.print_header("UEBA Continuous Monitoring")
        self.print_colored(f"Monitoring every {interval} seconds. Press Ctrl+C to stop.", 'blue')
        
        try:
            while True:
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                # Quick health check
                es_healthy = False
                grafana_healthy = False
                
                try:
                    es_response = requests.get("http://localhost:9200/_cluster/health", timeout=5)
                    es_healthy = es_response.status_code == 200
                except:
                    pass
                
                try:
                    grafana_response = requests.get("http://localhost:3000/api/health", timeout=5)
                    grafana_healthy = grafana_response.status_code == 200
                except:
                    pass
                
                # Status display
                es_status = "🟢" if es_healthy else "🔴"
                grafana_status = "🟢" if grafana_healthy else "🔴"
                
                print(f"\r[{timestamp}] ES: {es_status} | Grafana: {grafana_status} | Status: {'✅ OK' if es_healthy and grafana_healthy else '⚠️ Issues'}", end='', flush=True)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.print_colored("\n\nMonitoring stopped.", 'blue')

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="UEBA System Validator and Health Monitor v3.0")
    parser.add_argument("--check", action="store_true", help="Run comprehensive system check")
    parser.add_argument("--monitor", action="store_true", help="Run continuous monitoring")
    parser.add_argument("--interval", type=int, default=30, help="Monitoring interval in seconds")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    
    args = parser.parse_args()
    
    validator = UEBASystemValidator()
    
    if args.monitor:
        validator.monitor_continuous(args.interval)
    elif args.check or not any([args.monitor]):
        results = validator.run_comprehensive_check()
        
        if args.json:
            print(json.dumps(results, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()