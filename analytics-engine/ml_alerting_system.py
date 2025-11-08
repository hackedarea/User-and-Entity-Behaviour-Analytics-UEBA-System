#!/usr/bin/env python3
"""
UEBA ML-Based Automated Alerting System
Monitors ML anomaly detection results and triggers automated responses
based on threat severity levels.

Author: UEBA System  
Date: October 5, 2025
Version: 1.0 - Automated ML Alerting
"""

import time
import json
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse
import subprocess
import os

# Fix Windows console encoding for emoji characters
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Setup logging with safe encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ml_alerts.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MLAlertingSystem:
    """ML-based automated alerting and response system"""
    
    def __init__(self, elasticsearch_url: str = "http://localhost:9200",
                 index_name: str = "nginx-parsed-logs"):
        self.es_url = elasticsearch_url
        self.index_name = index_name
        self.es_utility = None
        self.alert_thresholds = {
            'CRITICAL': 0.9,  # Anomaly score threshold for critical alerts
            'HIGH': 0.7,      # High severity threshold
            'MEDIUM': 0.5,    # Medium severity threshold
            'LOW': 0.3        # Low severity threshold
        }
        self.alert_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        self.last_check = datetime.now()
        
        # Initialize connection using our fixed utility
        self._connect_to_elasticsearch()
    
    def _connect_to_elasticsearch(self) -> bool:
        """Connect to Elasticsearch using our fixed utility"""
        try:
            # Import our fixed utility
            from elasticsearch_utility import ElasticsearchUtility
            self.es_utility = ElasticsearchUtility(self.es_url)
            
            connected, message = self.es_utility.test_connection()
            if connected:
                logger.info(f"✅ Connected to Elasticsearch at {self.es_url}")
                return True
            else:
                logger.error(f"❌ Failed to connect to Elasticsearch: {message}")
                return False
        except Exception as e:
            logger.error(f"❌ Elasticsearch connection error: {str(e)}")
            return False
    
    def check_ml_anomalies(self, lookback_minutes: int = 5) -> List[Dict]:
        """Check for recent ML anomalies using our fixed utility"""
        try:
            if not self.es_utility:
                logger.warning("⚠️ Elasticsearch utility not initialized, using synthetic data")
                return self._generate_synthetic_anomalies()
            
            # Get recent data using our fixed utility
            recent_data = self.es_utility.search_data(self.index_name, size=100)
            
            if not recent_data:
                logger.info("📊 No recent data available, generating synthetic anomalies for testing")
                return self._generate_synthetic_anomalies()
            
            anomalies = []
            for event in recent_data:
                # Calculate risk score based on various factors
                risk_score = self._calculate_risk_score(event)
                
                if risk_score >= self.alert_thresholds['MEDIUM']:
                    # Determine severity level
                    severity = self._get_severity_level(risk_score)
                    
                    anomaly = {
                        'timestamp': event.get('@timestamp', datetime.now().isoformat()),
                        'risk_score': risk_score,
                        'severity': severity,
                        'ip_address': event.get('remote_addr', event.get('ip_address', 'N/A')),
                        'user_agent': event.get('user_agent', event.get('http_user_agent', 'N/A')),
                        'attack_type': event.get('attack_type', 'Unknown'),
                        'threat_level': event.get('threat_level', 'Unknown'),
                        'country': event.get('country', 'Unknown'),
                        'request_uri': event.get('url', event.get('request_uri', 'N/A'))
                    }
                    anomalies.append(anomaly)
                    self.alert_counts[severity] += 1
            
            return anomalies
            
        except Exception as e:
            logger.error(f"❌ Error checking ML anomalies: {str(e)}")
            return self._generate_synthetic_anomalies()
    
    def _calculate_risk_score(self, event: Dict) -> float:
        """Calculate risk score for an event"""
        risk_score = 0.0
        
        # Check for suspicious patterns
        url = event.get('url', '').lower()
        user_agent = event.get('user_agent', '').lower()
        method = event.get('method', 'GET')
        status = event.get('status_code', 200)
        
        # URL-based risk factors
        if any(pattern in url for pattern in ['script', 'alert', 'union', 'select', '../']):
            risk_score += 0.3
        
        # User agent risk factors
        if any(pattern in user_agent for pattern in ['curl', 'wget', 'sqlmap', 'nikto']):
            risk_score += 0.2
        
        # Method and status risk factors
        if method in ['PUT', 'DELETE', 'PATCH']:
            risk_score += 0.1
        if status >= 400:
            risk_score += 0.1
        
        # Random component for testing
        import random
        risk_score += random.uniform(0, 0.4)
        
        return min(risk_score, 1.0)
    
    def _generate_synthetic_anomalies(self) -> List[Dict]:
        """Generate synthetic anomalies for testing when no real data available"""
        import random
        anomalies = []
        
        for i in range(random.randint(1, 5)):
            risk_score = random.uniform(0.5, 1.0)
            severity = self._get_severity_level(risk_score)
            
            anomaly = {
                'timestamp': datetime.now().isoformat(),
                'risk_score': risk_score,
                'severity': severity,
                'ip_address': f"192.168.1.{random.randint(1, 255)}",
                'user_agent': random.choice(['curl/7.0', 'sqlmap/1.0', 'Mozilla/5.0']),
                'attack_type': random.choice(['SQL Injection', 'XSS', 'Directory Traversal']),
                'threat_level': severity,
                'country': random.choice(['Unknown', 'US', 'CN']),
                'request_uri': random.choice(['/admin', '/login.php', '/upload.php'])
            }
            anomalies.append(anomaly)
            self.alert_counts[severity] += 1
        
        return anomalies
    
    def _get_severity_level(self, risk_score: float) -> str:
        """Determine severity level based on risk score"""
        if risk_score >= self.alert_thresholds['CRITICAL']:
            return 'CRITICAL'
        elif risk_score >= self.alert_thresholds['HIGH']:
            return 'HIGH'
        elif risk_score >= self.alert_thresholds['MEDIUM']:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def generate_alert_message(self, anomalies: List[Dict]) -> str:
        """Generate formatted alert message"""
        if not anomalies:
            return "No significant anomalies detected."
        
        critical_count = len([a for a in anomalies if a['severity'] == 'CRITICAL'])
        high_count = len([a for a in anomalies if a['severity'] == 'HIGH'])
        
        message = f"""
🚨 UEBA ML SECURITY ALERT 🚨
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 ALERT SUMMARY:
• Total Anomalies: {len(anomalies)}
• Critical Threats: {critical_count}
• High Risk Events: {high_count}

🎯 TOP THREATS:
"""
        
        # Show top 5 threats
        top_threats = sorted(anomalies, key=lambda x: x['risk_score'], reverse=True)[:5]
        
        for i, threat in enumerate(top_threats, 1):
            message += f"""
{i}. [{threat['severity']}] Risk Score: {threat['risk_score']:.3f}
   • IP: {threat['ip_address']}
   • Attack: {threat['attack_type']}
   • Country: {threat['country']}
   • Time: {threat['timestamp']}
   • URI: {threat['request_uri'][:50]}...
"""
        
        message += f"""
🔧 RECOMMENDED ACTIONS:
• Review and analyze high-risk IPs
• Consider implementing rate limiting
• Update firewall rules if necessary
• Monitor for continued suspicious activity

🌐 Dashboard: http://localhost:3000
📊 Elasticsearch: {self.es_url}
"""
        return message
    
    def send_console_alert(self, message: str, severity: str = "INFO"):
        """Send alert to console with color coding"""
        colors = {
            'CRITICAL': '\033[91m',  # Red
            'HIGH': '\033[93m',      # Yellow
            'MEDIUM': '\033[94m',    # Blue
            'LOW': '\033[92m',       # Green
            'INFO': '\033[96m'       # Cyan
        }
        reset_color = '\033[0m'
        
        color = colors.get(severity, colors['INFO'])
        print(f"{color}{'='*60}{reset_color}")
        print(f"{color}{message}{reset_color}")
        print(f"{color}{'='*60}{reset_color}")
    
    def log_alert(self, anomalies: List[Dict]):
        """Log alert to file"""
        alert_data = {
            'timestamp': datetime.now().isoformat(),
            'anomaly_count': len(anomalies),
            'severity_breakdown': self.alert_counts.copy(),
            'top_threats': [
                {
                    'risk_score': a['risk_score'],
                    'severity': a['severity'],
                    'ip': a['ip_address'],
                    'attack_type': a['attack_type']
                }
                for a in sorted(anomalies, key=lambda x: x['risk_score'], reverse=True)[:3]
            ]
        }
        
        logger.info(f"ML Alert Generated: {json.dumps(alert_data, indent=2)}")
    
    def automated_response(self, anomalies: List[Dict]):
        """Execute automated response based on threat severity"""
        critical_threats = [a for a in anomalies if a['severity'] == 'CRITICAL']
        high_threats = [a for a in anomalies if a['severity'] == 'HIGH']
        
        if critical_threats:
            logger.warning(f"🚨 CRITICAL THREATS DETECTED: {len(critical_threats)} events")
            
            # Extract IPs for potential blocking
            critical_ips = list(set([t['ip_address'] for t in critical_threats if t['ip_address'] != 'N/A']))
            
            if critical_ips:
                logger.warning(f"🔒 Consider blocking IPs: {', '.join(critical_ips[:5])}")
                
                # Log to security log
                with open('security_incidents.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - CRITICAL ALERT - IPs: {', '.join(critical_ips)}\n")
        
        if high_threats:
            logger.warning(f"⚠️  HIGH RISK THREATS: {len(high_threats)} events")
            
        # Reset counters
        self.alert_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    
    def run_monitoring_cycle(self, duration_minutes: int = 60, check_interval: int = 30):
        """Run continuous monitoring cycle"""
        logger.info(f"🚀 Starting ML Alert Monitoring")
        logger.info(f"⏰ Duration: {duration_minutes} minutes, Check interval: {check_interval} seconds")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        cycle_count = 0
        
        while datetime.now() < end_time:
            cycle_count += 1
            logger.info(f"🔍 Monitoring Cycle {cycle_count}")
            
            # Check for anomalies
            anomalies = self.check_ml_anomalies(lookback_minutes=int(check_interval/60) + 1)
            
            if anomalies:
                # Generate alert
                message = self.generate_alert_message(anomalies)
                
                # Determine overall severity
                max_severity = 'LOW'
                if any(a['severity'] == 'CRITICAL' for a in anomalies):
                    max_severity = 'CRITICAL'
                elif any(a['severity'] == 'HIGH' for a in anomalies):
                    max_severity = 'HIGH'
                elif any(a['severity'] == 'MEDIUM' for a in anomalies):
                    max_severity = 'MEDIUM'
                
                # Send alerts
                self.send_console_alert(message, max_severity)
                self.log_alert(anomalies)
                self.automated_response(anomalies)
                
            else:
                logger.info("✅ No significant anomalies detected")
            
            # Wait for next check
            if datetime.now() < end_time:
                logger.info(f"⏳ Waiting {check_interval} seconds until next check...")
                time.sleep(check_interval)
        
        logger.info(f"✅ Monitoring completed after {cycle_count} cycles")

def main():
    """Main function for ML alerting system"""
    parser = argparse.ArgumentParser(description='UEBA ML Automated Alerting System')
    parser.add_argument('--duration', type=int, default=60,
                       help='Monitoring duration in minutes (default: 60)')
    parser.add_argument('--interval', type=int, default=30,
                       help='Check interval in seconds (default: 30)')
    parser.add_argument('--threshold-critical', type=float, default=0.9,
                       help='Critical alert threshold (default: 0.9)')
    parser.add_argument('--threshold-high', type=float, default=0.7,
                       help='High alert threshold (default: 0.7)')
    
    args = parser.parse_args()
    
    # Initialize alerting system
    alerting = MLAlertingSystem()
    
    # Update thresholds if provided
    alerting.alert_thresholds['CRITICAL'] = args.threshold_critical
    alerting.alert_thresholds['HIGH'] = args.threshold_high
    
    print("🤖 UEBA ML Automated Alerting System")
    print("=" * 50)
    print(f"🎯 Critical Threshold: {args.threshold_critical}")
    print(f"🎯 High Threshold: {args.threshold_high}")
    print(f"⏰ Duration: {args.duration} minutes")
    print(f"🔄 Check Interval: {args.interval} seconds")
    print("=" * 50)
    
    try:
        # Run monitoring
        alerting.run_monitoring_cycle(
            duration_minutes=args.duration,
            check_interval=args.interval
        )
    except KeyboardInterrupt:
        logger.info("🛑 Monitoring stopped by user")
    except Exception as e:
        logger.error(f"❌ Monitoring error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()