#!/usr/bin/env python3
"""
UEBA Real-time Dashboard Data Streamer
Continuously generates realistic security events for dashboard visualization

Prerequisites:
    - UEBA system running
    - Elasticsearch accessible
    - Grafana dashboards deployed

Author: UEBA System
Date: October 4, 2025
Version: 1.0 - Real-time Data Streaming
"""

import requests
import time
import random
import json
from datetime import datetime, timedelta
import threading
import sys
import argparse
from typing import List, Dict

class UEBADataStreamer:
    """
    Real-time data streaming for UEBA dashboards
    """
    
    def __init__(self, nginx_url: str = "http://localhost:8080"):
        """
        Initialize data streamer
        
        Args:
            nginx_url (str): Nginx server URL for generating traffic
        """
        self.nginx_url = nginx_url
        self.running = False
        
        # Attack patterns for realistic security events
        self.attack_patterns = [
            "/admin",
            "/admin/login",
            "/wp-admin", 
            "/phpmyadmin",
            "/config",
            "/backup",
            "/.env",
            "/etc/passwd",
            "/../../../etc/passwd",
            "/login?user=admin'OR'1'='1",
            "/search?q=<script>alert(1)</script>",
            "/api/users?id=1'UNION SELECT * FROM users--",
            "/uploads/shell.php",
            "/cgi-bin/test-cgi",
        ]
        
        # Normal traffic patterns
        self.normal_patterns = [
            "/",
            "/index.html",
            "/about",
            "/contact", 
            "/products",
            "/services",
            "/blog",
            "/static/css/style.css",
            "/static/js/app.js",
            "/images/logo.png",
            "/api/status",
            "/healthcheck"
        ]
        
        # User agents
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "curl/7.68.0",
            "sqlmap/1.4.9",
            "Nikto/2.1.6",
            "python-requests/2.25.1",
            "Googlebot/2.1",
            "bingbot/2.0"
        ]
    
    def generate_normal_traffic(self):
        """Generate normal user traffic"""
        try:
            path = random.choice(self.normal_patterns)
            user_agent = random.choice(self.user_agents[:4])  # Normal user agents
            
            headers = {'User-Agent': user_agent}
            response = requests.get(f"{self.nginx_url}{path}", 
                                  headers=headers, timeout=5)
            
            print(f"✅ Normal: {path} -> {response.status_code}")
            
        except Exception as e:
            print(f"⚠️  Normal traffic error: {str(e)}")
    
    def generate_attack_traffic(self):
        """Generate attack/suspicious traffic"""
        try:
            path = random.choice(self.attack_patterns)
            user_agent = random.choice(self.user_agents)  # Mix of user agents
            
            headers = {'User-Agent': user_agent}
            response = requests.get(f"{self.nginx_url}{path}", 
                                  headers=headers, timeout=5)
            
            print(f"🚨 Attack: {path} -> {response.status_code}")
            
        except Exception as e:
            print(f"⚠️  Attack traffic error: {str(e)}")
    
    def generate_burst_attack(self):
        """Generate burst of attack traffic (simulating automated tools)"""
        print("💥 Generating attack burst...")
        
        for _ in range(random.randint(5, 15)):
            self.generate_attack_traffic()
            time.sleep(random.uniform(0.1, 0.5))
    
    def generate_scan_sequence(self):
        """Generate directory/vulnerability scanning sequence"""
        print("🔍 Generating scan sequence...")
        
        scan_paths = [
            "/admin", "/admin/login", "/admin/config",
            "/wp-admin", "/wp-content", "/wp-includes",
            "/.env", "/config", "/backup", "/database",
            "/phpmyadmin", "/mysql", "/sql",
            "/cgi-bin", "/scripts", "/test"
        ]
        
        user_agent = "Nikto/2.1.6"
        
        for path in scan_paths:
            try:
                headers = {'User-Agent': user_agent}
                response = requests.get(f"{self.nginx_url}{path}", 
                                      headers=headers, timeout=5)
                print(f"🔍 Scan: {path} -> {response.status_code}")
                time.sleep(random.uniform(0.2, 1.0))
            except:
                pass
    
    def start_streaming(self, duration_minutes: int = 60, 
                       normal_rate: int = 10, attack_rate: int = 3):
        """
        Start continuous data streaming
        
        Args:
            duration_minutes (int): How long to stream data
            normal_rate (int): Normal requests per minute
            attack_rate (int): Attack requests per minute
        """
        print(f"🚀 Starting UEBA Real-time Data Streaming")
        print(f"⏱️  Duration: {duration_minutes} minutes")
        print(f"📊 Normal traffic rate: {normal_rate} requests/minute")
        print(f"🚨 Attack traffic rate: {attack_rate} requests/minute")
        print("=" * 60)
        
        self.running = True
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Calculate intervals
        normal_interval = 60.0 / normal_rate if normal_rate > 0 else 60
        attack_interval = 60.0 / attack_rate if attack_rate > 0 else 60
        
        last_normal = time.time()
        last_attack = time.time()
        last_burst = time.time()
        last_scan = time.time()
        
        try:
            while self.running and datetime.now() < end_time:
                current_time = time.time()
                
                # Generate normal traffic
                if current_time - last_normal >= normal_interval:
                    self.generate_normal_traffic()
                    last_normal = current_time
                
                # Generate attack traffic
                if current_time - last_attack >= attack_interval:
                    self.generate_attack_traffic()
                    last_attack = current_time
                
                # Random attack bursts (every 5-15 minutes)
                if current_time - last_burst >= random.randint(300, 900):
                    self.generate_burst_attack()
                    last_burst = current_time
                
                # Random scanning sequences (every 10-30 minutes)
                if current_time - last_scan >= random.randint(600, 1800):
                    self.generate_scan_sequence()
                    last_scan = current_time
                
                # Brief pause to prevent overwhelming
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n⏹️  Streaming stopped by user")
        except Exception as e:
            print(f"\n❌ Streaming error: {str(e)}")
        finally:
            self.running = False
            elapsed = (datetime.now() - start_time).total_seconds() / 60
            print(f"\n✅ Streaming completed. Duration: {elapsed:.1f} minutes")
    
    def test_connection(self) -> bool:
        """Test connection to Nginx server"""
        try:
            response = requests.get(self.nginx_url, timeout=5)
            if response.status_code in [200, 404]:  # 404 is expected for root
                print(f"✅ Connected to Nginx at {self.nginx_url}")
                return True
            else:
                print(f"❌ Unexpected response from Nginx: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to Nginx: {str(e)}")
            return False


def main():
    """Main function for data streaming"""
    parser = argparse.ArgumentParser(description='UEBA Real-time Dashboard Data Streamer')
    parser.add_argument('--duration', type=int, default=60,
                       help='Streaming duration in minutes (default: 60)')
    parser.add_argument('--normal-rate', type=int, default=10,
                       help='Normal requests per minute (default: 10)')
    parser.add_argument('--attack-rate', type=int, default=3,
                       help='Attack requests per minute (default: 3)')
    parser.add_argument('--nginx-url', default='http://localhost:8080',
                       help='Nginx server URL (default: http://localhost:8080)')
    parser.add_argument('--test-only', action='store_true',
                       help='Only test connection, do not stream data')
    
    args = parser.parse_args()
    
    # Initialize streamer
    streamer = UEBADataStreamer(nginx_url=args.nginx_url)
    
    # Test connection
    if not streamer.test_connection():
        print("❌ Connection test failed. Please ensure UEBA system is running.")
        sys.exit(1)
    
    if args.test_only:
        print("✅ Connection test successful!")
        sys.exit(0)
    
    # Start streaming
    streamer.start_streaming(
        duration_minutes=args.duration,
        normal_rate=args.normal_rate,
        attack_rate=args.attack_rate
    )


if __name__ == "__main__":
    main()