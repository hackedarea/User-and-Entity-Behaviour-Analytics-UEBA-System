#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UEBA Quick Deploy - Optimized & User-Friendly
Fast deployment with intelligent error handling
"""

import subprocess
import sys
import time
import argparse
import json
from pathlib import Path

def print_status(message, status="INFO"):
    """Clean status output"""
    icons = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️", "PROCESSING": "🔄"}
    icon = icons.get(status, "ℹ️")
    print(f"{icon} {message}")

def print_header():
    """Print deployment header"""
    print("\n" + "="*70)
    print("🚀 UEBA SYSTEM QUICK DEPLOY")
    print("="*70)
    print("⚡ Fast • 🛡️ Secure • 📊 Analytics • 🤖 AI-Powered")
    print("="*70)

def check_python_environment():
    """Check Python and core packages"""
    print_status("Checking Python environment...", "PROCESSING")
    
    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print_status(f"Python {python_version}", "SUCCESS")
    
    # Check critical packages
    required_packages = ['pandas', 'numpy', 'sklearn', 'requests']
    optional_packages = ['tensorflow', 'elasticsearch', 'joblib']
    
    for package in required_packages:
        try:
            __import__(package)
            print_status(f"Package {package} - Available", "SUCCESS")
        except ImportError:
            print_status(f"Package {package} - Missing (Required)", "ERROR")
            return False
            
    for package in optional_packages:
        try:
            __import__(package)
            print_status(f"Package {package} - Available", "SUCCESS")
        except ImportError:
            print_status(f"Package {package} - Missing (Optional)", "WARNING")
    
    return True

def check_file_structure():
    """Verify essential files and directories"""
    print_status("Checking file structure...", "PROCESSING")
    
    essential_files = [
        "ueba_launcher.py",
        "analytics-engine/auth_system.py",
        "analytics-engine/automl_optimizer.py",
        "analytics-engine/advanced_ml_detector.py",
        "analytics-engine/system_health_checker.py"
    ]
    
    essential_dirs = ["analytics-engine", "config", "ml_models", "logs"]
    
    all_good = True
    
    # Check files
    for file_path in essential_files:
        if Path(file_path).exists():
            print_status(f"File {file_path}", "SUCCESS")
        else:
            print_status(f"File {file_path} - Missing", "ERROR")
            all_good = False
    
    # Check directories
    for dir_path in essential_dirs:
        if Path(dir_path).exists():
            print_status(f"Directory {dir_path}", "SUCCESS")
        else:
            print_status(f"Directory {dir_path} - Missing", "ERROR")
            all_good = False
    
    return all_good

def check_docker_daemon():
    """Check and start Docker daemon if needed"""
    print_status("Checking Docker daemon...", "PROCESSING")
    
    try:
        # Check Docker version first
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print_status("Docker not installed", "ERROR")
            return False
            
        # Try to connect to Docker daemon
        result = subprocess.run(['docker', 'info'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print_status("Docker daemon running", "SUCCESS")
            return True
        else:
            # Try to start Docker service on Windows
            print_status("Starting Docker Desktop service...", "PROCESSING")
            try:
                if sys.platform == "win32":
                    subprocess.run(['net', 'start', 'com.docker.service'], 
                                 capture_output=True, text=True, timeout=30)
                    time.sleep(5)  # Wait for service to start
                    
                    # Check again
                    result = subprocess.run(['docker', 'info'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        print_status("Docker daemon started successfully", "SUCCESS")
                        return True
                        
                print_status("Please start Docker Desktop manually", "WARNING")
                return False
            except Exception as e:
                print_status(f"Failed to start Docker: {str(e)}", "ERROR")
                return False
                
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print_status("Docker not available", "ERROR")
        return False

def create_docker_network():
    """Create UEBA Docker network if it doesn't exist"""
    try:
        # Check if network exists
        result = subprocess.run(['docker', 'network', 'ls'], 
                              capture_output=True, text=True, timeout=10)
        if 'ueba-net' not in result.stdout:
            print_status("Creating Docker network 'ueba-net'...", "PROCESSING")
            subprocess.run(['docker', 'network', 'create', 'ueba-net'], 
                         capture_output=True, text=True, timeout=10)
            print_status("Docker network created", "SUCCESS")
        return True
    except Exception:
        return False

def start_elasticsearch():
    """Start Elasticsearch container"""
    print_status("Starting Elasticsearch...", "PROCESSING")
    
    try:
        # Check if already running
        result = subprocess.run(['docker', 'ps'], 
                              capture_output=True, text=True, timeout=10)
        if 'elasticsearch-ueba' in result.stdout:
            print_status("Elasticsearch already running", "SUCCESS")
            return True
            
        # Remove existing stopped container
        subprocess.run(['docker', 'rm', '-f', 'elasticsearch-ueba'], 
                      capture_output=True, text=True, timeout=10)
        
        # Start new container
        cmd = [
            'docker', 'run', '-d',
            '--name', 'elasticsearch-ueba',
            '--network', 'ueba-net',
            '-p', '9200:9200',
            '-p', '9300:9300',
            '-e', 'discovery.type=single-node',
            '-e', 'xpack.security.enabled=false',
            '-e', 'ES_JAVA_OPTS=-Xms512m -Xmx512m',
            '-e', 'cluster.routing.allocation.disk.threshold_enabled=false',
            'docker.elastic.co/elasticsearch/elasticsearch:8.10.2'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print_status("Elasticsearch container started", "SUCCESS")
            
            # Wait for Elasticsearch to be ready
            print_status("Waiting for Elasticsearch to initialize...", "PROCESSING")
            for i in range(30):  # 60 seconds timeout
                try:
                    import requests
                    response = requests.get('http://localhost:9200/_cluster/health', timeout=2)
                    if response.status_code == 200:
                        print_status("Elasticsearch is ready", "SUCCESS")
                        return True
                except:
                    pass
                time.sleep(2)
                
            print_status("Elasticsearch started but may need more time", "WARNING")
            return True
        else:
            print_status(f"Failed to start Elasticsearch: {result.stderr}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Error starting Elasticsearch: {str(e)}", "ERROR")
        return False

def start_grafana():
    """Start Grafana container"""
    print_status("Starting Grafana...", "PROCESSING")
    
    try:
        # Check if already running
        result = subprocess.run(['docker', 'ps'], 
                              capture_output=True, text=True, timeout=10)
        if 'grafana-ueba-new' in result.stdout:
            print_status("Grafana already running", "SUCCESS")
            return True
            
        # Remove existing stopped container
        subprocess.run(['docker', 'rm', '-f', 'grafana-ueba-new'], 
                      capture_output=True, text=True, timeout=10)
        
        # Start new container
        cmd = [
            'docker', 'run', '-d',
            '--name', 'grafana-ueba-new',
            '--network', 'ueba-net',
            '-p', '3000:3000',
            '-e', 'GF_SECURITY_ADMIN_PASSWORD=admin',
            'grafana/grafana:latest'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print_status("Grafana container started", "SUCCESS")
            
            # Wait for Grafana to be ready
            print_status("Waiting for Grafana to initialize...", "PROCESSING")
            for i in range(15):  # 30 seconds timeout
                try:
                    import requests
                    response = requests.get('http://localhost:3000/api/health', timeout=2)
                    if response.status_code == 200:
                        print_status("Grafana is ready", "SUCCESS")
                        return True
                except:
                    pass
                time.sleep(2)
                
            print_status("Grafana started but may need more time", "WARNING")
            return True
        else:
            print_status(f"Failed to start Grafana: {result.stderr}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Error starting Grafana: {str(e)}", "ERROR")
        return False

def check_docker_services():
    """Check and start Docker services if needed"""
    print_status("Checking Docker services...", "PROCESSING")
    
    # First check Docker daemon
    if not check_docker_daemon():
        return False
        
    # Create network if needed
    create_docker_network()
    
    # Start services
    elasticsearch_ok = start_elasticsearch()
    grafana_ok = start_grafana()
    
    if elasticsearch_ok and grafana_ok:
        print_status("All Docker services running", "SUCCESS")
        return True
    elif elasticsearch_ok or grafana_ok:
        print_status("Some Docker services running", "WARNING")
        return True
    else:
        print_status("Docker services failed to start", "ERROR")
        return False

def check_ml_models():
    """Check ML models availability"""
    print_status("Checking ML models...", "PROCESSING")
    
    ml_dir = Path("ml_models")
    if not ml_dir.exists():
        print_status("ML models directory missing", "ERROR")
        return False
    
    model_files = list(ml_dir.glob("*.joblib")) + list(ml_dir.glob("*.h5"))
    
    if len(model_files) >= 10:
        print_status(f"ML models: {len(model_files)} found", "SUCCESS")
        return True
    elif len(model_files) > 0:
        print_status(f"ML models: {len(model_files)} found (minimal set)", "WARNING")
        return True
    else:
        print_status("No ML models found", "ERROR")
        return False

def check_authentication():
    """Check authentication system"""
    print_status("Checking authentication system...", "PROCESSING")
    
    try:
        # Add analytics-engine to path temporarily
        analytics_path = Path("analytics-engine")
        if str(analytics_path) not in sys.path:
            sys.path.insert(0, str(analytics_path))
        
        # Try to import auth system
        from auth_system import auth
        print_status("Authentication system", "SUCCESS")
        
        # Check user database
        users_file = Path("config/users.json")
        if users_file.exists():
            with open(users_file, 'r') as f:
                data = json.load(f)
            user_count = len(data.get('users', {}))
            print_status(f"User database: {user_count} users", "SUCCESS")
        else:
            print_status("User database - Will be created", "WARNING")
        
        return True
        
    except Exception as e:
        print_status(f"Authentication system error: {e}", "ERROR")
        return False

def run_deployment_check(services_only=False, start_services=True):
    """Run complete deployment check"""
    start_time = time.time()
    print_header()
    
    # Store original function for check-only mode
    global original_check_docker_services
    if not hasattr(run_deployment_check, 'original_saved'):
        original_check_docker_services = check_docker_services
        run_deployment_check.original_saved = True
    
    checks = [
        ("Python Environment", check_python_environment),
        ("File Structure", check_file_structure),
        ("ML Models", check_ml_models),
        ("Authentication", check_authentication)
    ]
    
    if not services_only:
        if start_services:
            checks.append(("Docker Services", check_docker_services))
        else:
            # For check-only mode, use a simpler check function
            def check_docker_status():
                """Simple Docker status check without starting services"""
                print_status("Checking Docker status (check-only mode)...", "PROCESSING")
                try:
                    result = subprocess.run(['docker', 'ps'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        containers = result.stdout
                        elasticsearch_running = 'elasticsearch-ueba' in containers
                        grafana_running = 'grafana-ueba-new' in containers
                        
                        if elasticsearch_running and grafana_running:
                            print_status("All Docker services running", "SUCCESS")
                            return True
                        elif elasticsearch_running or grafana_running:
                            print_status("Some Docker services running", "WARNING")
                            return False
                        else:
                            print_status("No Docker services running", "WARNING")
                            return False
                    else:
                        print_status("Docker daemon not running", "ERROR")
                        return False
                except Exception:
                    print_status("Docker not available", "ERROR")
                    return False
            
            checks.append(("Docker Services", check_docker_status))
    
    print(f"\n🔍 Running {len(checks)} deployment checks...")
    if start_services:
        print("🚀 Auto-starting services as needed...")
    else:
        print("👀 Check-only mode (no services will be started)")
    print("-" * 50)
    
    results = {}
    
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print_status(f"{check_name} - Error: {e}", "ERROR")
            results[check_name] = False
        print()  # Add spacing between checks
    
    # Summary
    print("="*70)
    print("📊 DEPLOYMENT SUMMARY")
    print("="*70)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for check_name, result in results.items():
        status = "SUCCESS" if result else "ERROR"
        print_status(f"{check_name}", status)
    
    print(f"\n📈 Results: {passed}/{total} checks passed")
    
    # Overall status
    if passed == total:
        print_status("🎉 SYSTEM READY FOR DEPLOYMENT!", "SUCCESS")
        print_deployment_info(start_time)
        return True
    elif passed >= total * 0.75:  # 75% success rate
        print_status("⚠️ System mostly ready - some warnings", "WARNING")
        print_deployment_info(start_time)
        return True
    else:
        print_status("❌ System not ready - fix errors first", "ERROR")
        return False

def print_deployment_info(start_time):
    """Print deployment information"""
    duration = time.time() - start_time
    
    print(f"\n⏱️ Deploy check completed in {duration:.1f}s")
    print("\n🌐 ACCESS POINTS:")
    print("   📊 Grafana Dashboard: http://localhost:3000")
    print("      Username: admin | Password: admin")
    print("   📡 Elasticsearch: http://localhost:9200")
    print("   🚀 UEBA Launcher: python ueba_launcher.py")
    
    print("\n💡 NEXT STEPS:")
    print("   1. Start main system: python ueba_launcher.py")
    print("   2. Login with: admin / SecureNewPass123!")
    print("   3. Access advanced features (options 5-11)")
    print("   4. Monitor via Grafana dashboard")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='UEBA Quick Deploy')
    parser.add_argument('--services-only', action='store_true', 
                       help='Check only services, skip Docker')
    parser.add_argument('--start-services', action='store_true',
                       help='Start Docker services if not running (default behavior)')
    parser.add_argument('--check-only', action='store_true',
                       help='Only check status, do not start services')
    
    args = parser.parse_args()
    
    # Default behavior is to start services unless check-only is specified
    start_services = not args.check_only
    
    success = run_deployment_check(services_only=args.services_only, start_services=start_services)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
