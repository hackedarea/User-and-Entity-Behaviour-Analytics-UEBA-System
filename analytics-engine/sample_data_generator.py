#!/usr/bin/env python3
"""
UEBA Sample Data Generator
Generates initial realistic security events for UEBA system

Usage:
    python sample_data_generator.py --events 200
    python sample_data_generator.py --events 500 --index custom-logs
"""

import requests
import json
import sys
import argparse
from datetime import datetime, timedelta
import random


class UEBASampleDataGenerator:
    """Generates realistic sample security data for UEBA system"""
    
    def __init__(self, es_url="http://localhost:9200", index_name="nginx-parsed-logs"):
        self.es_url = es_url
        self.index_name = index_name
        
        # Sample data patterns for realistic events
        self.internal_ips = [f'192.168.1.{i}' for i in range(1, 101)]
        self.external_ips = [f'10.0.0.{i}' for i in range(1, 51)]
        self.suspicious_ips = ['185.220.100.240', '45.32.105.239', '198.98.51.189']
        
        self.normal_urls = ['/', '/home', '/about', '/contact', '/services', '/products', '/dashboard', '/profile']
        self.admin_urls = ['/admin', '/admin/login', '/wp-admin', '/control-panel', '/management']
        self.attack_urls = [
            '/../../etc/passwd', 
            "/admin'; DROP TABLE users;--", 
            '/<script>alert("xss")</script>',
            '/wp-admin/../../../etc/passwd',
            '/.env',
            '/config.php',
            '/backup.sql'
        ]
        
        self.methods = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS']
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'curl/7.68.0', 
            'Python-requests/2.28.1', 
            'sqlmap/1.4.7',
            'Nikto/2.1.6'
        ]
        
        self.attack_types = ['normal', 'sql_injection', 'xss', 'brute_force', 'directory_traversal', 'dos_attack', 'privilege_escalation']
        self.countries = ['US', 'GB', 'DE', 'FR', 'CN', 'RU', 'JP', 'IN', 'BR', 'CA', 'AU', 'IT', 'ES', 'NL']
        self.cities = ['New York', 'London', 'Berlin', 'Paris', 'Beijing', 'Moscow', 'Tokyo', 'Mumbai', 'São Paulo', 'Toronto']
        
    def generate_event(self, attack_probability=0.25):
        """Generate a single realistic security event"""
        timestamp = datetime.now() - timedelta(minutes=random.randint(0, 2880))  # Last 2 days
        
        # Determine if this is an attack
        is_attack = random.random() < attack_probability
        
        if is_attack:
            attack_type = random.choice(self.attack_types[1:])  # Exclude 'normal'
            ip = random.choice(self.external_ips + self.suspicious_ips)
            url = random.choice(self.admin_urls + self.attack_urls)
            status = random.choice([400, 401, 403, 404, 500, 503])
            risk_score = random.uniform(60, 95)
            user_agent = random.choice(self.user_agents[-3:])  # More suspicious agents
            method = random.choice(['POST', 'GET', 'PUT']) if attack_type == 'sql_injection' else random.choice(self.methods)
        else:
            attack_type = 'normal'
            ip = random.choice(self.internal_ips + self.external_ips[:30])
            url = random.choice(self.normal_urls + self.admin_urls[:2])
            status = random.choice([200, 201, 301, 302, 304])
            risk_score = random.uniform(0, 30)
            user_agent = random.choice(self.user_agents[:3])  # Normal browsers
            method = random.choice(['GET', 'POST'])
        
        # Generate additional realistic fields
        size = random.randint(500, 50000)
        country = random.choice(self.countries)
        city = random.choice(self.cities)
        severity = 'high' if risk_score > 80 else 'medium' if risk_score > 60 else 'low'
        
        # Create the event document
        event = {
            '@timestamp': timestamp.isoformat(),
            'timestamp': timestamp.strftime('%d/%b/%Y:%H:%M:%S +0000'),
            'ip': ip,
            'method': method,
            'url': url,
            'status': status,
            'size': size,
            'user_agent': user_agent,
            'risk_score': round(risk_score, 2),
            'attack_type': attack_type,
            'country': country,
            'city': city,
            'threat_detected': is_attack,
            'severity': severity,
            'session_id': f"sess_{random.randint(100000, 999999)}",
            'response_time': random.randint(10, 5000),  # milliseconds
            'bytes_sent': size,
            'bytes_received': random.randint(100, 2000)
        }
        
        return event
    
    def generate_batch_data(self, num_events=200, attack_probability=0.25):
        """Generate a batch of realistic security events"""
        print(f"🔄 Generating {num_events} realistic security events...")
        
        events = []
        success_count = 0
        
        for i in range(num_events):
            try:
                event = self.generate_event(attack_probability)
                
                # Send to Elasticsearch
                response = requests.post(
                    f'{self.es_url}/{self.index_name}/_doc',
                    headers={'Content-Type': 'application/json'},
                    data=json.dumps(event),
                    timeout=5
                )
                
                if response.status_code in [200, 201]:
                    success_count += 1
                    events.append(event)
                else:
                    print(f"⚠️  Failed to index event {i+1}: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error generating event {i+1}: {e}")
                
        print(f"✅ Successfully generated {success_count}/{num_events} security events")
        
        # Refresh index for immediate availability
        try:
            refresh_response = requests.post(f'{self.es_url}/{self.index_name}/_refresh')
            if refresh_response.status_code == 200:
                print("✅ Index refreshed for immediate availability")
        except:
            print("⚠️  Could not refresh index")
            
        return events, success_count
    
    def verify_data(self):
        """Verify that data was successfully indexed"""
        try:
            response = requests.get(f'{self.es_url}/{self.index_name}/_count')
            if response.status_code == 200:
                count = response.json().get('count', 0)
                print(f"📊 Total documents in {self.index_name}: {count}")
                return count
            else:
                print(f"❌ Could not verify data: {response.status_code}")
                return 0
        except Exception as e:
            print(f"❌ Error verifying data: {e}")
            return 0


def main():
    """Main function with command line arguments"""
    parser = argparse.ArgumentParser(description='UEBA Sample Data Generator')
    parser.add_argument('--events', type=int, default=200,
                       help='Number of events to generate (default: 200)')
    parser.add_argument('--index', type=str, default='nginx-parsed-logs',
                       help='Elasticsearch index name (default: nginx-parsed-logs)')
    parser.add_argument('--es-url', type=str, default='http://localhost:9200',
                       help='Elasticsearch URL (default: http://localhost:9200)')
    parser.add_argument('--attack-rate', type=float, default=0.25,
                       help='Probability of attack events (default: 0.25)')
    parser.add_argument('--verify-only', action='store_true',
                       help='Only verify existing data count')
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = UEBASampleDataGenerator(
        es_url=args.es_url,
        index_name=args.index
    )
    
    if args.verify_only:
        count = generator.verify_data()
        sys.exit(0)
    
    # Generate data
    events, success_count = generator.generate_batch_data(
        num_events=args.events,
        attack_probability=args.attack_rate
    )
    
    # Verify results
    final_count = generator.verify_data()
    
    if success_count > 0:
        print(f"🎉 Sample data generation completed successfully!")
        print(f"📈 Attack events: ~{int(success_count * args.attack_rate)}")
        print(f"🛡️  Normal events: ~{success_count - int(success_count * args.attack_rate)}")
        sys.exit(0)
    else:
        print("❌ Sample data generation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()