#!/usr/bin/env python3
"""
UEBA System Authentication Module
Provides basic authentication and user session management
"""

import hashlib
import json
import os
import getpass
from datetime import datetime, timedelta
from pathlib import Path

class UEBAAuth:
    def __init__(self, config_file="config/users.json"):
        self.config_file = config_file
        self.session_file = "config/current_session.json"
        self.users = {}
        self.current_user = None
        self.session_timeout = 8  # hours
        
        # Create config directory if it doesn't exist
        Path("config").mkdir(exist_ok=True)
        
        # Load users or create default admin
        self._load_users()
        
    def _hash_password(self, password):
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _load_users(self):
        """Load users from config file"""
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.users = data.get('users', {})
            else:
                # Create default admin user
                self._create_default_admin()
        except Exception as e:
            print(f"⚠️ Error loading users: {e}")
            self._create_default_admin()
    
    def _create_default_admin(self):
        """Create default admin user"""
        default_password = "ueba2025!"
        self.users = {
            "admin": {
                "password_hash": self._hash_password(default_password),
                "role": "administrator",
                "created": datetime.now().isoformat(),
                "last_login": None
            }
        }
        self._save_users()
        print("🔐 Default admin user created!")
        print(f"   Username: admin")
        print(f"   Password: {default_password}")
        print("   ⚠️ Please change the default password after first login!")
    
    def _save_users(self):
        """Save users to config file"""
        try:
            data = {
                "users": self.users,
                "last_updated": datetime.now().isoformat()
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving users: {e}")
    
    def _save_session(self, username):
        """Save current session"""
        try:
            session = {
                "username": username,
                "login_time": datetime.now().isoformat(),
                "expires": (datetime.now() + timedelta(hours=self.session_timeout)).isoformat()
            }
            with open(self.session_file, 'w') as f:
                json.dump(session, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving session: {e}")
    
    def _load_session(self):
        """Load and validate current session"""
        try:
            if Path(self.session_file).exists():
                with open(self.session_file, 'r') as f:
                    session = json.load(f)
                
                expires = datetime.fromisoformat(session['expires'])
                if datetime.now() < expires:
                    self.current_user = session['username']
                    return True
                else:
                    # Session expired
                    os.remove(self.session_file)
                    return False
            return False
        except Exception as e:
            print(f"⚠️ Error loading session: {e}")
            return False
    
    def login(self, username=None, password=None):
        """Login user with username and password"""
        if username is None:
            username = input("👤 Username: ")
        
        if password is None:
            password = getpass.getpass("🔐 Password: ")
        
        if username in self.users:
            password_hash = self._hash_password(password)
            if self.users[username]["password_hash"] == password_hash:
                self.current_user = username
                self.users[username]["last_login"] = datetime.now().isoformat()
                self._save_users()
                self._save_session(username)
                print(f"✅ Welcome, {username}!")
                return True
            else:
                print("❌ Invalid password!")
                return False
        else:
            print("❌ User not found!")
            return False
    
    def logout(self):
        """Logout current user"""
        if Path(self.session_file).exists():
            os.remove(self.session_file)
        
        user = self.current_user
        self.current_user = None
        print(f"👋 Goodbye, {user}!")
    
    def is_authenticated(self):
        """Check if user is authenticated"""
        if self.current_user:
            return True
        return self._load_session()
    
    def require_auth(self):
        """Require authentication, prompt if not logged in"""
        if not self.is_authenticated():
            print("\n🔐 Authentication Required")
            print("="*50)
            return self.login()
        return True
    
    def change_password(self, old_password=None, new_password=None):
        """Change password for current user"""
        if not self.current_user:
            print("❌ Please login first!")
            return False
        
        if old_password is None:
            old_password = getpass.getpass("🔐 Current password: ")
        
        old_hash = self._hash_password(old_password)
        if self.users[self.current_user]["password_hash"] != old_hash:
            print("❌ Current password incorrect!")
            return False
        
        if new_password is None:
            new_password = getpass.getpass("🔐 New password: ")
            confirm_password = getpass.getpass("🔐 Confirm new password: ")
            
            if new_password != confirm_password:
                print("❌ Passwords don't match!")
                return False
        
        if len(new_password) < 8:
            print("❌ Password must be at least 8 characters!")
            return False
        
        self.users[self.current_user]["password_hash"] = self._hash_password(new_password)
        self.users[self.current_user]["password_changed"] = datetime.now().isoformat()
        self._save_users()
        print("✅ Password changed successfully!")
        return True
    
    def add_user(self, username, password, role="user"):
        """Add new user (admin only)"""
        if not self.current_user or self.users.get(self.current_user, {}).get("role") != "administrator":
            print("❌ Admin privileges required!")
            return False
        
        if username in self.users:
            print("❌ User already exists!")
            return False
        
        if len(password) < 8:
            print("❌ Password must be at least 8 characters!")
            return False
        
        self.users[username] = {
            "password_hash": self._hash_password(password),
            "role": role,
            "created": datetime.now().isoformat(),
            "created_by": self.current_user,
            "last_login": None
        }
        self._save_users()
        print(f"✅ User '{username}' created successfully!")
        return True
    
    def get_user_info(self):
        """Get current user information"""
        if self.current_user and self.current_user in self.users:
            user_info = self.users[self.current_user].copy()
            user_info.pop('password_hash', None)  # Don't return password hash
            user_info['username'] = self.current_user
            return user_info
        return None
    
    def list_users(self):
        """List all users (admin only)"""
        if not self.current_user or self.users.get(self.current_user, {}).get("role") != "administrator":
            print("❌ Admin privileges required!")
            return []
        
        users_list = []
        for username, user_data in self.users.items():
            user_info = {
                "username": username,
                "role": user_data.get("role", "user"),
                "created": user_data.get("created", "Unknown"),
                "last_login": user_data.get("last_login", "Never")
            }
            users_list.append(user_info)
        
        return users_list

# Global authentication instance
auth = UEBAAuth()

def require_authentication():
    """Decorator to require authentication"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if auth.require_auth():
                return func(*args, **kwargs)
            else:
                print("❌ Authentication failed!")
                return False
        return wrapper
    return decorator

if __name__ == "__main__":
    # Test authentication system
    print("🔐 UEBA Authentication System Test")
    print("="*50)
    
    # Test login
    if auth.require_auth():
        print(f"✅ Authenticated as: {auth.current_user}")
        
        # Show user info
        user_info = auth.get_user_info()
        if user_info:
            print(f"👤 Role: {user_info.get('role', 'Unknown')}")
            print(f"📅 Created: {user_info.get('created', 'Unknown')}")
            print(f"🕐 Last Login: {user_info.get('last_login', 'Never')}")
        
        # Test logout
        auth.logout()
    else:
        print("❌ Authentication failed!")