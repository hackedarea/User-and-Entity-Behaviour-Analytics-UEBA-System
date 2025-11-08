#!/usr/bin/env python3
"""
UEBA System Health Checker - Standalone diagnostic tool
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Suppress TensorFlow warnings for cleaner output
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

def print_header():
    """Clean header"""
    print("\n" + "="*70)
    print("🏥 UEBA SYSTEM HEALTH CHECKER")
    print("="*70)
    print("🔍 Comprehensive System Diagnostic")
    print("="*70 + "\n")

def print_status(message, status="INFO"):
    """Status messaging"""
    icons = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️", "PROCESSING": "🔄"}
    icon = icons.get(status, "ℹ️")
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {icon} {message}")

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version >= (3, 8):
        print_status(f"Python {version.major}.{version.minor}.{version.micro}", "SUCCESS")
        return True
    else:
        print_status(f"Python {version.major}.{version.minor} (3.8+ recommended)", "WARNING")
        return False

def check_required_packages():
    """Check required Python packages"""
    packages = {
        'pandas': 'Data manipulation',
        'numpy': 'Numerical computing',
        'sklearn': 'Machine learning',
        'requests': 'HTTP requests',
        'tensorflow': 'Deep learning',
        'elasticsearch': 'Elasticsearch client'
    }
    
    results = {}
    for package, description in packages.items():
        try:
            __import__(package)
            print_status(f"{package} - {description}", "SUCCESS")
            results[package] = True
        except ImportError:
            print_status(f"{package} - {description} (MISSING)", "ERROR")
            results[package] = False
    
    return results

def check_docker_services():
    """Check Docker containers"""
    try:
        result = subprocess.run(['docker', 'ps', '--format', '{{.Names}} {{.Status}}'], 
                               capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 0 and lines[0]:  # Has output
                containers = {}
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            name = parts[0]
                            status = ' '.join(parts[1:])
                            containers[name] = 'Up' in status
                
                # Check for UEBA containers (flexible matching)
                ueba_containers_found = []
                elasticsearch_found = False
                grafana_found = False
                
                for container_name in containers:
                    # Check for Elasticsearch containers
                    if 'elasticsearch' in container_name.lower():
                        status = "SUCCESS" if containers[container_name] else "ERROR"
                        print_status(f"Docker Container: {container_name}", status)
                        elasticsearch_found = True
                        ueba_containers_found.append(container_name)
                    
                    # Check for Grafana containers
                    elif 'grafana' in container_name.lower():
                        status = "SUCCESS" if containers[container_name] else "ERROR"
                        print_status(f"Docker Container: {container_name}", status)
                        grafana_found = True
                        ueba_containers_found.append(container_name)
                
                if not ueba_containers_found:
                    print_status("No UEBA containers found", "WARNING")
                    return False
                
                # Check if we have both essential services
                if elasticsearch_found and grafana_found:
                    return True
                else:
                    missing = []
                    if not elasticsearch_found:
                        missing.append("Elasticsearch")
                    if not grafana_found:
                        missing.append("Grafana")
                    print_status(f"Missing containers: {', '.join(missing)}", "WARNING")
                    return False
            else:
                print_status("No Docker containers running", "WARNING")
                return False
        else:
            print_status("Docker not accessible", "ERROR")
            return False
    except FileNotFoundError:
        print_status("Docker not installed", "ERROR")
        return False
    except subprocess.TimeoutExpired:
        print_status("Docker check timeout", "ERROR")
        return False
    except Exception as e:
        print_status(f"Docker check failed: {e}", "ERROR")
        return False

def check_elasticsearch():
    """Check Elasticsearch connection"""
    try:
        import requests
        response = requests.get('http://localhost:9200', timeout=5)
        if response.status_code == 200:
            data = response.json()
            version = data.get('version', {}).get('number', 'unknown')
            print_status(f"Elasticsearch {version} - Connected", "SUCCESS")
            return True
        else:
            print_status(f"Elasticsearch - HTTP {response.status_code}", "ERROR")
            return False
    except Exception as e:
        print_status(f"Elasticsearch - Connection failed: {e}", "ERROR")
        return False

def check_grafana():
    """Check Grafana connection"""
    try:
        import requests
        response = requests.get('http://localhost:3000', timeout=5)
        if response.status_code == 200:
            print_status("Grafana - Connected", "SUCCESS")
            return True
        else:
            print_status(f"Grafana - HTTP {response.status_code}", "ERROR")
            return False
    except Exception as e:
        print_status(f"Grafana - Connection failed: {e}", "ERROR")
        return False

def check_file_structure():
    """Check UEBA file structure"""
    required_files = [
        'ueba_launcher.py',
        'analytics-engine/quick_deploy_optimized.py',
        'analytics-engine/optimized_ueba_system.py',
        'analytics-engine/automl_optimizer.py',
        'analytics-engine/advanced_ml_detector.py',
        'analytics-engine/advanced_neural_detector.py',
        'analytics-engine/results_viewer.py'
    ]
    
    required_dirs = [
        'analytics-engine',
        'ml_models',
        'results',
        'config',
        'data'
    ]
    
    file_status = True
    for file_path in required_files:
        if Path(file_path).exists():
            print_status(f"File: {file_path}", "SUCCESS")
        else:
            print_status(f"File: {file_path} (MISSING)", "ERROR")
            file_status = False
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print_status(f"Directory: {dir_path}", "SUCCESS")
        else:
            print_status(f"Directory: {dir_path} (MISSING)", "WARNING")
    
    return file_status

def check_ml_models():
    """Check ML models"""
    model_dir = Path('ml_models')
    if model_dir.exists():
        model_files = list(model_dir.glob('*.joblib')) + list(model_dir.glob('*.h5'))
        if model_files:
            print_status(f"ML Models: {len(model_files)} found", "SUCCESS")
            return True
        else:
            print_status("ML Models: No trained models found", "WARNING")
            return False
    else:
        print_status("ML Models: Directory not found", "WARNING")
        return False

def check_results():
    """Check results directory"""
    results_dir = Path('results')
    if results_dir.exists():
        result_files = list(results_dir.glob('*.json'))
        if result_files:
            print_status(f"Results: {len(result_files)} files found", "SUCCESS")
            return True
        else:
            print_status("Results: No result files found", "WARNING")
            return False
    else:
        print_status("Results: Directory not found", "WARNING")
        return False

def main():
    """Main health check function"""
    print_header()
    
    print("🔍 SYSTEM CHECKS:")
    print("-" * 50)
    
    # Core system checks
    python_ok = check_python_version()
    
    print("\n🐍 PYTHON PACKAGES:")
    print("-" * 50)
    packages = check_required_packages()
    
    print("\n🐳 DOCKER SERVICES:")
    print("-" * 50)
    docker_ok = check_docker_services()
    
    print("\n🌐 SERVICE CONNECTIONS:")
    print("-" * 50)
    elasticsearch_ok = check_elasticsearch()
    grafana_ok = check_grafana()
    
    print("\n📁 FILE STRUCTURE:")
    print("-" * 50)
    files_ok = check_file_structure()
    
    print("\n🤖 ML COMPONENTS:")
    print("-" * 50)
    models_ok = check_ml_models()
    results_ok = check_results()
    
    # Overall assessment
    print("\n" + "="*70)
    print("📊 OVERALL SYSTEM STATUS")
    print("="*70)
    
    critical_checks = [python_ok, files_ok, all(packages[pkg] for pkg in ['pandas', 'numpy', 'sklearn'])]
    service_checks = [docker_ok, elasticsearch_ok, grafana_ok]
    
    if all(critical_checks):
        if all(service_checks):
            print_status("System Status: EXCELLENT ✨", "SUCCESS")
            print_status("All critical components operational", "SUCCESS")
        else:
            print_status("System Status: GOOD (services need attention)", "WARNING")
            print_status("Core system ready, some services down", "WARNING")
    else:
        print_status("System Status: NEEDS ATTENTION", "ERROR")
        print_status("Critical components missing", "ERROR")
    
    print("\n💡 RECOMMENDATIONS:")
    if not all(service_checks):
        print("   • Run: python ueba_launcher.py --quick")
        print("   • Check Docker Desktop is running")
    
    if not models_ok:
        print("   • Train ML models with option 3 or 4")
    
    if not packages['tensorflow']:
        print("   • Install TensorFlow: pip install tensorflow")
    
    print("\n🌐 ACCESS POINTS:")
    print(f"   📊 Grafana: http://localhost:3000 (admin/admin)")
    print(f"   📡 Elasticsearch: http://localhost:9200")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()