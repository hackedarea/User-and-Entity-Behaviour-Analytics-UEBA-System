#!/usr/bin/env python3
"""
Enhanced Grafana Dashboard with ML Integration - FIXED VERSION
Creates dashboards that display machine learning anomaly detection results
alongside traditional security metrics.

Author: UEBA System
Date: October 5, 2025
Version: 2.1 - Field Mapping Fix
"""

import requests
import json
import time
import sys
from datetime import datetime
import os

class MLEnhancedDashboardProvisioner:
    """Enhanced dashboard provisioner with ML integration"""
    
    def __init__(self, grafana_url="http://localhost:3000", username="admin", password="admin"):
        self.grafana_url = grafana_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.auth = (username, password)
        
    def wait_for_grafana(self, max_attempts=30):
        """Wait for Grafana to be available"""
        for attempt in range(max_attempts):
            try:
                response = self.session.get(f"{self.grafana_url}/api/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Grafana is accessible")
                    return True
            except:
                pass
            
            if attempt < max_attempts - 1:
                print(f"⏳ Waiting for Grafana... (attempt {attempt + 1}/{max_attempts})")
                time.sleep(2)
        
        print("❌ Could not connect to Grafana")
        return False
    
    def create_datasource(self):
        """Create Elasticsearch datasource"""
        datasource_config = {
            "name": "UEBA-Elasticsearch",
            "type": "elasticsearch", 
            "url": "http://elasticsearch-ueba:9200",
            "access": "proxy",
            "isDefault": True,
            "database": "nginx-parsed-logs",
            "jsonData": {
                "timeField": "@timestamp",
                "interval": "Daily",
                "esVersion": "8.0.0"
            }
        }
        
        try:
            response = self.session.post(
                f"{self.grafana_url}/api/datasources",
                headers={"Content-Type": "application/json"},
                json=datasource_config,
                timeout=10
            )
            
            if response.status_code in [200, 409]:  # 409 = already exists
                print("✅ Elasticsearch datasource configured")
                return True
            else:
                print(f"⚠️  Datasource response: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Datasource creation failed: {str(e)}")
            return False
    
    def delete_existing_ml_dashboards(self):
        """Delete existing ML dashboards"""
        try:
            # Get all dashboards
            response = self.session.get(f"{self.grafana_url}/api/search?type=dash-db")
            if response.status_code == 200:
                dashboards = response.json()
                ml_dashboards = [d for d in dashboards if "ML" in d.get("title", "") or "Real-time" in d.get("title", "")]
                
                for dashboard in ml_dashboards:
                    delete_response = self.session.delete(f"{self.grafana_url}/api/dashboards/uid/{dashboard['uid']}")
                    if delete_response.status_code == 200:
                        print(f"🗑️  Deleted existing ML dashboard: {dashboard['title']}")
                
                return True
            return False
        except Exception as e:
            print(f"⚠️  Could not delete existing dashboards: {str(e)}")
            return False
    
    def create_ml_security_dashboard(self):
        """Create advanced ML Security Analytics Dashboard with FIXED queries"""
        dashboard_config = {
            "dashboard": {
                "id": None,
                "title": "🤖 ML Security Analytics & Threat Detection",
                "tags": ["ml", "security", "anomaly", "ueba"],
                "timezone": "browser",
                "time": {"from": "now-24h", "to": "now"},
                "refresh": "30s",
                "panels": [
                    {
                        "id": 1,
                        "title": "🚨 ML Anomaly Detection Alert",
                        "type": "stat",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                        "targets": [
                            {
                                "datasource": "UEBA-Elasticsearch",
                                "query": "severity:high OR threat_detected:true",
                                "metrics": [{"type": "count", "id": "1"}],
                                "bucketAggs": [
                                    {
                                        "type": "date_histogram",
                                        "field": "@timestamp",
                                        "id": "2",
                                        "settings": {"interval": "auto"}
                                    }
                                ]
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "thresholds"},
                                "thresholds": {
                                    "steps": [
                                        {"color": "green", "value": None},
                                        {"color": "yellow", "value": 5},
                                        {"color": "red", "value": 10}
                                    ]
                                }
                            }
                        }
                    },
                    {
                        "id": 2,
                        "title": "🎯 ML Algorithm Performance",
                        "type": "table",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                        "targets": [
                            {
                                "datasource": "UEBA-Elasticsearch",
                                "query": "*",
                                "metrics": [{"type": "count", "id": "1"}],
                                "bucketAggs": [
                                    {
                                        "type": "terms",
                                        "field": "attack_type.keyword",
                                        "id": "2",
                                        "settings": {"size": "10", "order": "desc", "orderBy": "_count"}
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "id": 3,
                        "title": "📊 Anomaly Score Distribution",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8},
                        "targets": [
                            {
                                "datasource": "UEBA-Elasticsearch",
                                "query": "*",
                                "metrics": [{"type": "count", "id": "1"}],
                                "bucketAggs": [
                                    {
                                        "type": "histogram",
                                        "field": "risk_score",
                                        "id": "2",
                                        "settings": {"interval": "10"}
                                    },
                                    {
                                        "type": "date_histogram",
                                        "field": "@timestamp",
                                        "id": "3",
                                        "settings": {"interval": "auto"}
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "id": 4,
                        "title": "🌍 Geographic Threat Intelligence",
                        "type": "table",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
                        "targets": [
                            {
                                "datasource": "UEBA-Elasticsearch",
                                "query": "*",
                                "metrics": [{"type": "count", "id": "1"}],
                                "bucketAggs": [
                                    {
                                        "type": "terms",
                                        "field": "country.keyword",
                                        "id": "2",
                                        "settings": {"size": "10", "order": "desc", "orderBy": "_count"}
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "id": 5,
                        "title": "⏰ Real-time ML Processing",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
                        "targets": [
                            {
                                "datasource": "UEBA-Elasticsearch",
                                "query": "*",
                                "metrics": [{"type": "count", "id": "1"}],
                                "bucketAggs": [
                                    {
                                        "type": "date_histogram",
                                        "field": "@timestamp",
                                        "id": "2",
                                        "settings": {"interval": "5m"}
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        
        try:
            response = self.session.post(
                f"{self.grafana_url}/api/dashboards/db",
                headers={"Content-Type": "application/json"},
                json=dashboard_config,
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ ML Security Analytics Dashboard created")
                return True
            else:
                print(f"⚠️  ML Dashboard creation response: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ ML Dashboard creation failed: {str(e)}")
            return False
    
    def create_ml_realtime_dashboard(self):
        """Create Real-time ML Monitoring Dashboard"""
        dashboard_config = {
            "dashboard": {
                "id": None,
                "title": "⚡ Real-time ML Threat Monitoring",
                "tags": ["realtime", "ml", "monitoring", "live"],
                "timezone": "browser",
                "time": {"from": "now-1h", "to": "now"},
                "refresh": "5s",
                "panels": [
                    {
                        "id": 1,
                        "title": "🚨 Live Threat Detection",
                        "type": "stat",
                        "gridPos": {"h": 6, "w": 8, "x": 0, "y": 0},
                        "targets": [
                            {
                                "datasource": "UEBA-Elasticsearch",
                                "query": "severity:high OR threat_detected:true",
                                "metrics": [{"type": "count", "id": "1"}],
                                "bucketAggs": [
                                    {
                                        "type": "date_histogram",
                                        "field": "@timestamp",
                                        "id": "2",
                                        "settings": {"interval": "auto"}
                                    }
                                ]
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "thresholds"},
                                "thresholds": {
                                    "steps": [
                                        {"color": "green", "value": None},
                                        {"color": "orange", "value": 1},
                                        {"color": "red", "value": 5}
                                    ]
                                }
                            }
                        }
                    },
                    {
                        "id": 2,
                        "title": "🎯 ML Model Confidence",
                        "type": "stat",
                        "gridPos": {"h": 6, "w": 8, "x": 8, "y": 0},
                        "targets": [
                            {
                                "datasource": "UEBA-Elasticsearch",
                                "query": "*",
                                "metrics": [{"type": "avg", "field": "risk_score", "id": "1"}],
                                "bucketAggs": [
                                    {
                                        "type": "date_histogram",
                                        "field": "@timestamp",
                                        "id": "2",
                                        "settings": {"interval": "auto"}
                                    }
                                ]
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "thresholds"},
                                "thresholds": {
                                    "steps": [
                                        {"color": "green", "value": None},
                                        {"color": "yellow", "value": 50},
                                        {"color": "red", "value": 80}
                                    ]
                                },
                                "unit": "short",
                                "min": 0,
                                "max": 100
                            }
                        }
                    },
                    {
                        "id": 3,
                        "title": "📈 Processing Rate",
                        "type": "stat",
                        "gridPos": {"h": 6, "w": 8, "x": 16, "y": 0},
                        "targets": [
                            {
                                "datasource": "UEBA-Elasticsearch",
                                "query": "*",
                                "metrics": [{"type": "count", "id": "1"}],
                                "bucketAggs": [
                                    {
                                        "type": "date_histogram",
                                        "field": "@timestamp",
                                        "id": "2",
                                        "settings": {"interval": "1m"}
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        
        try:
            response = self.session.post(
                f"{self.grafana_url}/api/dashboards/db",
                headers={"Content-Type": "application/json"},
                json=dashboard_config,
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ Real-time ML Monitoring Dashboard created")
                return True
            else:
                print(f"⚠️  Real-time Dashboard creation response: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Real-time Dashboard creation failed: {str(e)}")
            return False

    def run(self):
        """Execute the dashboard creation process"""
        print("🚀 Creating ML-Enhanced Security Dashboards")
        print("=" * 56)
        
        # Wait for Grafana
        if not self.wait_for_grafana():
            return False
        
        # Create datasource
        if not self.create_datasource():
            return False
        
        # Clean existing dashboards
        print("🧹 Cleaning existing ML dashboards...")
        self.delete_existing_ml_dashboards()
        
        # Create new dashboards
        ml_created = self.create_ml_security_dashboard()
        realtime_created = self.create_ml_realtime_dashboard()
        
        if ml_created and realtime_created:
            print("\n🎉 ML-Enhanced Dashboards Created Successfully!")
            print("📊 Available Dashboards:")
            print("   • 🤖 ML Security Analytics & Threat Detection")
            print("   • ⚡ Real-time ML Threat Monitoring")
            print("🌐 Access: http://localhost:3000")
            return True
        else:
            print("❌ Dashboard creation failed")
            return False

if __name__ == "__main__":
    provisioner = MLEnhancedDashboardProvisioner()
    success = provisioner.run()
    sys.exit(0 if success else 1)