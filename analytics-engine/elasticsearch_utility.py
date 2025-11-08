#!/usr/bin/env python3
"""
Elasticsearch Connection Utility
Handles version compatibility and provides fallback mechanisms
"""

import json
import requests
from datetime import datetime
import warnings

class ElasticsearchUtility:
    def __init__(self, host="http://localhost:9200"):
        self.host = host
        self.connected = False
        self.version = None
        
    def test_connection(self):
        """Test Elasticsearch connection and get version info"""
        try:
            # Use simple HTTP request to avoid client compatibility issues
            response = requests.get(self.host, timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.version = data.get('version', {}).get('number', 'unknown')
                self.connected = True
                return True, f"Elasticsearch {self.version} connected"
            else:
                return False, f"HTTP {response.status_code}"
        except Exception as e:
            return False, str(e)
    
    def get_data_count(self, index="nginx-parsed-logs"):
        """Get document count from index using HTTP API"""
        if not self.connected:
            return 0
        
        try:
            # Use direct HTTP API to avoid client issues
            url = f"{self.host}/{index}/_count"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('count', 0)
            else:
                return 0
        except:
            return 0
    
    def search_data(self, index="nginx-parsed-logs", size=100):
        """Search data using HTTP API to avoid client compatibility issues"""
        if not self.connected:
            return []
        
        try:
            # Use simple search query
            url = f"{self.host}/{index}/_search"
            query = {
                "size": size,
                "query": {"match_all": {}},
                "sort": [{"@timestamp": {"order": "desc"}}]
            }
            
            response = requests.post(url, 
                                   json=query, 
                                   headers={"Content-Type": "application/json"},
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                hits = data.get('hits', {}).get('hits', [])
                return [hit['_source'] for hit in hits]
            else:
                print(f"Search failed with status {response.status_code}")
                return []
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def get_sample_data(self, size=100):
        """Get sample data with fallback to synthetic data"""
        # First try to get real data
        real_data = self.search_data(size=size)
        
        if real_data and len(real_data) > 10:
            print(f"✅ Retrieved {len(real_data)} real events from Elasticsearch")
            return real_data
        else:
            print(f"⚠️ Limited real data ({len(real_data)} events), generating synthetic data")
            return self.generate_synthetic_data(size)
    
    def generate_synthetic_data(self, size=100):
        """Generate synthetic security data for testing"""
        import numpy as np
        from datetime import timedelta
        
        np.random.seed(42)  # Reproducible results
        
        # Attack patterns
        attack_patterns = [
            {"url": "/admin/../../../etc/passwd", "type": "directory_traversal", "severity": "high"},
            {"url": "/search?q=<script>alert('xss')</script>", "type": "xss", "severity": "medium"},
            {"url": "/login.php?id=1' OR '1'='1", "type": "sql_injection", "severity": "high"},
            {"url": "/upload.php?file=http://evil.com/shell.txt", "type": "rfi", "severity": "high"},
            {"url": "/wp-admin/admin-ajax.php?action=revslider_show_image&img=../wp-config.php", "type": "lfi", "severity": "medium"}
        ]
        
        normal_patterns = [
            "/home", "/about", "/contact", "/products", "/services",
            "/search?q=python", "/user/profile", "/api/data", "/dashboard",
            "/login", "/register", "/help", "/documentation"
        ]
        
        data = []
        attack_count = int(size * 0.15)  # 15% attacks
        
        # Generate attacks
        for i in range(attack_count):
            pattern = np.random.choice(attack_patterns)
            event = {
                '@timestamp': (datetime.now() - timedelta(minutes=np.random.randint(0, 1440))).isoformat(),
                'url': pattern['url'],
                'method': np.random.choice(['GET', 'POST'], p=[0.6, 0.4]),
                'status_code': np.random.choice([200, 403, 500], p=[0.3, 0.5, 0.2]),
                'response_size': np.random.randint(100, 2000),
                'user_agent': np.random.choice(['curl/7.0', 'sqlmap/1.0', 'nikto/2.0']),
                'remote_addr': f"192.168.1.{np.random.randint(1, 255)}",
                'attack_type': pattern['type'],
                'is_attack': True,
                'severity': pattern['severity']
            }
            data.append(event)
        
        # Generate normal traffic
        for i in range(size - attack_count):
            event = {
                '@timestamp': (datetime.now() - timedelta(minutes=np.random.randint(0, 1440))).isoformat(),
                'url': np.random.choice(normal_patterns),
                'method': np.random.choice(['GET', 'POST'], p=[0.8, 0.2]),
                'status_code': np.random.choice([200, 404, 301], p=[0.7, 0.2, 0.1]),
                'response_size': np.random.randint(500, 5000),
                'user_agent': np.random.choice([
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                ]),
                'remote_addr': f"10.0.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}",
                'is_attack': False
            }
            data.append(event)
        
        return data

    def search_with_query(self, index="nginx-parsed-logs", query=None):
        """Search data with custom query using HTTP API"""
        if not self.connected:
            return {"hits": {"hits": []}}
        
        try:
            url = f"{self.host}/{index}/_search"
            
            # Default query if none provided
            if query is None:
                query = {"size": 100, "query": {"match_all": {}}}
            
            response = requests.post(url, 
                                   json=query, 
                                   headers={"Content-Type": "application/json"},
                                   timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Search failed with status {response.status_code}")
                return {"hits": {"hits": []}}
        except Exception as e:
            print(f"Search error: {e}")
            return {"hits": {"hits": []}}

# Global utility instance
es_util = ElasticsearchUtility()

def get_elasticsearch_data(size=100, fallback_to_synthetic=True):
    """
    Get data from Elasticsearch with fallback to synthetic data
    This is the main function other components should use
    """
    global es_util
    
    # Test connection if not already done
    if not es_util.connected:
        connected, message = es_util.test_connection()
        if connected:
            print(f"✅ {message}")
        else:
            print(f"⚠️ Elasticsearch connection failed: {message}")
            if fallback_to_synthetic:
                print("🔄 Falling back to synthetic data generation")
                return es_util.generate_synthetic_data(size)
            else:
                return []
    
    # Try to get real data
    if es_util.connected:
        return es_util.get_sample_data(size)
    elif fallback_to_synthetic:
        return es_util.generate_synthetic_data(size)
    else:
        return []

def test_elasticsearch_utility():
    """Test the utility functions"""
    print("🔍 Testing Elasticsearch Utility")
    print("-" * 50)
    
    # Test connection
    connected, message = es_util.test_connection()
    print(f"Connection: {message}")
    
    if connected:
        # Test count
        count = es_util.get_data_count()
        print(f"Document count: {count}")
        
        # Test search
        sample = es_util.search_data(size=5)
        print(f"Sample data: {len(sample)} documents")
    
    # Test synthetic data
    synthetic = es_util.generate_synthetic_data(10)
    print(f"Synthetic data: {len(synthetic)} documents")
    
    print("✅ Utility test complete")

if __name__ == "__main__":
    test_elasticsearch_utility()