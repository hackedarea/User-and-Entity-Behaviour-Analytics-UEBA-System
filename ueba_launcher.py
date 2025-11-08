#!/usr/bin/env python3
"""
UEBA System v3.1 - Main Launcher with Authentication
Optimized, Clean, Fast & User-Friendly Entry Point with Enterprise Security
Fixed version for production use
"""

import sys
import os
import argparse
import subprocess
import shlex
from pathlib import Path

# Global auth variable
auth = None
AUTH_AVAILABLE = False

def initialize_auth():
    """Initialize authentication system"""
    global auth, AUTH_AVAILABLE
    
    try:
        # Add analytics-engine to path if needed
        analytics_path = Path(__file__).parent / "analytics-engine"
        if str(analytics_path) not in sys.path:
            sys.path.insert(0, str(analytics_path))
        
        from auth_system import auth as auth_module
        auth = auth_module
        AUTH_AVAILABLE = True
        return True
    except ImportError as e:
        AUTH_AVAILABLE = False
        print(f"[!] Authentication system not available - running in open mode")
        return False

def print_banner():
    """Clean, professional banner with authentication status"""
    print("\n" + "="*70)
    print("[>]  UEBA SYSTEM v3.1 - CYBERSECURITY PLATFORM")
    print("="*70)
    print("🚀 Optimized • 🧹 Clean • ⚡ Fast • 👤 User-Friendly")
    if AUTH_AVAILABLE and auth and auth.current_user:
        try:
            user_info = auth.get_user_info()
            role = user_info.get('role', 'user') if user_info else 'unknown'
            print(f"👤 Logged in as: {auth.current_user} ({role})")
        except:
            print("👤 Authentication status unclear")
    print("="*70)

def print_main_menu():
    """Display main menu options based on authentication status"""
    print("\n🎯 MAIN MENU - Choose Your Operation:")
    print()
    print("   [>] QUICK ACTIONS:")
    print("   1. [>] Quick Deploy (Start everything)")
    print("   2. [~] System Health Check")
    print("   3. [✓] Fast Security Analysis")
    print()
    print("   [ML] ANALYSIS OPTIONS:")
    print("   4. [IML] Interactive ML Analysis")
    
    # Show advanced options based on authentication
    if AUTH_AVAILABLE and auth and auth.is_authenticated():
        print("   5. [ML] AutoML Optimization")
        print("   6. [NL] Neural Network Training")
        print("   7. [AML] Advanced ML Detection")
        print()
        print("   [T] ADVANCED OPTIONS:")
        print("   8. [D] Generate Sample Data")
        print("   9. [!] ML Alerting System")
        print("   10. [D] View Results")
        print("   11. [~] Real-time ML Monitoring")
    else:
        print("   [x] Advanced features require authentication")
        if AUTH_AVAILABLE:
            print("   [Auth] Use option 12 to login for full access")
    
    print()
    if AUTH_AVAILABLE:
        if auth and auth.current_user:
            print("   [⚷ꗃ] AUTHENTICATION:")
            print("   12. [PASS] Change Password")
            try:
                user_info = auth.get_user_info()
                if user_info and user_info.get('role') == 'administrator':
                    print("   13. 👥 User Management")
            except:
                pass
            print("   14. [Bye] Logout")
        else:
            print("   [⚷ꗃ] AUTHENTICATION:")
            print("   12. [Hi] Login")
        print()
    
    print("   [x] 0. Exit")

def run_command(command, description):
    """Run a command with user feedback"""
    print(f"\n[-] {description}...")
    try:
        if isinstance(command, str):
            command_list = shlex.split(command)
        else:
            command_list = command
            
        result = subprocess.run(command_list, check=True)
        print(f"[✓] {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[x] {description} failed: {e}")
        return False
    except FileNotFoundError as e:
        print(f"[x] {description} failed: Command not found - {e}")
        return False
    except KeyboardInterrupt:
        print(f"\n[!] {description} cancelled by user")
        return False

def handle_auth_choice(choice):
    """Handle authentication-related choices"""
    if not AUTH_AVAILABLE or not auth:
        print("[x] Authentication system not available")
        return False
    
    try:
        if choice == '12':
            if auth.current_user:
                # Change password
                print("\n[PASS] Change Password")
                print("="*30)
                try:
                    current_password = input("Enter current password: ").strip()
                    if not current_password:
                        print("[x] Current password cannot be empty")
                        return False
                    
                    new_password = input("Enter new password: ").strip()
                    if not new_password:
                        print("[x] New password cannot be empty")
                        return False
                    
                    if len(new_password) < 8:
                        print("[x] New password must be at least 8 characters long")
                        return False
                    
                    confirm_password = input("Confirm new password: ").strip()
                    if new_password != confirm_password:
                        print("[x] Passwords do not match")
                        return False
                    
                    # Call change_password with proper parameters
                    result = auth.change_password(current_password, new_password)
                    if result:
                        print("[✓] Password changed successfully!")
                        return True
                    else:
                        print("[x] Password change failed. Please check your current password.")
                        return False
                        
                except KeyboardInterrupt:
                    print("\n[x] Password change cancelled")
                    return False
                except Exception as e:
                    print(f"[x] Error changing password: {e}")
                    return False
            else:
                # Login
                return auth.login()
        
        elif choice == '13':
            # User management (admin only)
            if not auth.current_user:
                print("[x] Please login first")
                return False
            
            user_info = auth.get_user_info()
            if not user_info or user_info.get('role') != 'administrator':
                print("[x] Administrator privileges required")
                return False
            
            print("\n👥 User Management")
            print("1. List all users")
            print("2. Add new user")
            print("3. Back to main menu")
            
            sub_choice = input("Choose option: ").strip()
            
            if sub_choice == '1':
                users = auth.list_users()
                print(f"\n[^] Total users: {len(users)}")
                for user in users:
                    print(f"   👤 {user['username']} ({user['role']}) - Last login: {user['last_login']}")
            
            elif sub_choice == '2':
                username = input("Enter username: ").strip()
                if not username:
                    print("[x] Username cannot be empty")
                    return False
                
                password = input("Enter password: ").strip()
                if len(password) < 8:
                    print("[x] Password must be at least 8 characters")
                    return False
                
                role = input("Enter role (user/administrator): ").strip()
                if role not in ['user', 'administrator']:
                    role = 'user'
                
                return auth.add_user(username, password, role)
            
            return True
        
        elif choice == '14':
            # Logout
            if auth.current_user:
                auth.logout()
            return True
            
    except Exception as e:
        print(f"[x] Authentication error: {e}")
        return False
    
    return False

def handle_choice(choice):
    """Handle user menu choice with authentication checks"""
    
    # Handle authentication choices first
    if AUTH_AVAILABLE and choice in ['12', '13', '14']:
        return handle_auth_choice(choice)
    
    # Check if authentication is required for restricted operations
    if AUTH_AVAILABLE and auth and choice in ['5', '6', '7', '8', '9', '11']:
        if not auth.is_authenticated():
            print("[⚷ꗃ] This operation requires authentication")
            print("Please use option 12 to login first")
            return False
    
    commands = {
        '1': {
            'cmd': [sys.executable, "analytics-engine/quick_deploy_optimized.py", "--start-services"],
            'desc': "Quick deployment"
        },
        '2': {
            'cmd': [sys.executable, "analytics-engine/system_health_checker.py"],
            'desc': "System health check"
        },
        '3': {
            'cmd': [sys.executable, "analytics-engine/optimized_ueba_system.py", "--mode", "auto", "--size", "300", "--fast"],
            'desc': "Fast security analysis"
        },
        '4': {
            'cmd': [sys.executable, "analytics-engine/optimized_ueba_system.py", "--mode", "interactive"],
            'desc': "Interactive ML analysis"
        },
        '5': {
            'cmd': [sys.executable, "analytics-engine/automl_optimizer.py", "--size", "250"],
            'desc': "AutoML optimization"
        },
        '6': {
            'cmd': [sys.executable, "analytics-engine/advanced_neural_detector.py", "--size", "250", "--models", "lstm", "cnn"],
            'desc': "Neural network training"
        },
        '7': {
            'cmd': [sys.executable, "analytics-engine/advanced_ml_detector.py", "--size", "300", "--save-models"],
            'desc': "Advanced ML detection"
        },
        '8': {
            'cmd': [sys.executable, "analytics-engine/sample_data_generator.py", "--events", "500"],
            'desc': "Sample data generation"
        },
        '9': {
            'cmd': [sys.executable, "analytics-engine/ml_alerting_system.py", "--duration", "30"],
            'desc': "ML alerting system"
        },
        '10': {
            'cmd': [sys.executable, "analytics-engine/results_viewer.py"],
            'desc': "View results"
        },
        '11': {
            'cmd': [sys.executable, "analytics-engine/realtime_ml_monitor.py", "--duration", "60", "--model-dir", "ml_models"],
            'desc': "Real-time ML monitoring"
        }
    }
    
    if choice in commands:
        cmd_info = commands[choice]
        return run_command(cmd_info['cmd'], cmd_info['desc'])
    else:
        print("[x] Invalid choice. Please try again.")
        return False

def check_environment():
    """Quick environment check"""
    print("\n🔍 Environment Check:")
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 8):
        print(f"[✓] Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"[!] Python {python_version.major}.{python_version.minor} (3.8+ recommended)")
    
    # Check if in correct directory
    if Path('analytics-engine').exists():
        print("[✓] Analytics engine directory found")
    else:
        print("[x] Analytics engine directory not found")
        print("   Please run from the UEBA system root directory")
        return False
    
    # Check key files
    key_files = [
        'analytics-engine/optimized_ueba_system.py',
        'analytics-engine/automl_optimizer.py',
        'analytics-engine/advanced_ml_detector.py',
        'analytics-engine/advanced_neural_detector.py',
        'analytics-engine/ml_alerting_system.py',
        'analytics-engine/realtime_ml_monitor.py',
        'analytics-engine/quick_deploy_optimized.py'
    ]
    
    missing_files = [f for f in key_files if not Path(f).exists()]
    if missing_files:
        print(f"[x] Missing files: {', '.join(missing_files)}")
        return False
    else:
        print("[✓] All key files present")
    
    # Check authentication system
    if AUTH_AVAILABLE:
        print("[✓] Authentication system loaded")
    else:
        print("[!] Authentication system not available")
    
    return True

def main():
    """Main launcher function with authentication support"""
    # Initialize authentication first
    initialize_auth()
    
    parser = argparse.ArgumentParser(description='UEBA System v3.1 Main Launcher')
    parser.add_argument('--auto', type=str, help='Auto-run specific option (1-11)')
    parser.add_argument('--quick', action='store_true', help='Quick deploy and exit')
    parser.add_argument('--daemon', action='store_true', help='Run in daemon mode')
    parser.add_argument('--no-auth', action='store_true', help='Skip authentication')
    
    args = parser.parse_args()
    
    # Show banner
    print_banner()
    
    # Environment check
    if not check_environment():
        print("\n[x] Environment check failed. Please fix issues and try again.")
        sys.exit(1)
    
    # Handle special modes
    if args.daemon:
        print("\n[Daemon] Starting in daemon mode...")
        print("[✓] Daemon mode started (placeholder)")
        return
    
    if args.quick:
        print("\n[^] Quick Deploy Mode")
        if run_command([sys.executable, "analytics-engine/quick_deploy_optimized.py", "--start-services"], "Quick deployment"):
            print("\n[+] UEBA System is ready!")
            print("🌐 Access Grafana: http://localhost:3000 (admin/admin)")
            print("🌐 Elasticsearch: http://localhost:9200")
        sys.exit(0)
    
    if args.auto:
        print(f"\n[Auto] Auto-running option {args.auto}")
        success = handle_choice(args.auto)
        sys.exit(0 if success else 1)
    
    # Interactive mode
    print("\n[Hi] Welcome to UEBA System v3.1!")
    if AUTH_AVAILABLE:
        print("[⚷ꗃ] Enhanced with Enterprise Authentication")
    print("[-] Tip: Use Ctrl+C to cancel any operation")
    
    while True:
        try:
            print_main_menu()
            
            # Determine max option based on authentication
            max_option = "14" if AUTH_AVAILABLE else "11"
            choice = input(f"\n==> Enter your choice (0-{max_option}): ").strip()
            
            if choice == '0':
                print("\n[Bye] Thank you for using UEBA System v3.1!")
                if AUTH_AVAILABLE and auth and auth.current_user:
                    auth.logout()
                print("[⚷ꗃ] Stay secure!")
                break
            
            success = handle_choice(choice)
            
            # Ask if user wants to continue (except for interactive modes and auth actions)
            if choice not in ['4', '12', '13', '14']:
                continue_choice = input("\n❓ Continue with another operation? (y/n): ").strip().lower()
                if continue_choice not in ['y', 'yes']:
                    print("\n[Bye] Thank you for using UEBA System v3.1!")
                    if AUTH_AVAILABLE and auth and auth.current_user:
                        auth.logout()
                    break
        
        except KeyboardInterrupt:
            print("\n\n[Bye] UEBA System session ended by user")
            if AUTH_AVAILABLE and auth and auth.current_user:
                auth.logout()
            break
        except Exception as e:
            print(f"\n[x] Unexpected error: {e}")
            print("[<] Returning to main menu...")

if __name__ == "__main__":
    main()