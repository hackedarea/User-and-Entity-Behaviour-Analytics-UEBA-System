# 📊 Complete Grafana Dashboard Creation Guide for UEBA System

## 🎯 **Overview**
This guide covers multiple ways to create Grafana dashboards for your UEBA cybersecurity system, from automated provisioning to manual creation.

## 🚀 **Method 1: Automated Dashboard Provisioning (Recommended)**

### **Quick Setup:**
```bash
cd d:\ueba-system

# Run the automated dashboard provisioner
python analytics-engine\grafana_dashboard_provisioner.py
```

### **Pre-built Dashboards Created:**
1. **🛡️ SOC Operations Center** - Real-time security monitoring
2. **🔍 Security Analytics & ML** - Machine learning insights
3. **📈 Executive Security Summary** - High-level overview
4. **🎯 Threat Intelligence** - Threat detection and analysis

---

## 🖱️ **Method 2: Manual Dashboard Creation via Grafana UI**

### **Step 1: Access Grafana**
1. Open browser: `http://localhost:3000`
2. Login: `admin` / `admin`
3. Click **"+"** → **"Dashboard"** → **"Add new panel"**

### **Step 2: Configure Data Source**
```json
Data Source: Elasticsearch
URL: http://elasticsearch-ueba:9200
Index: nginx-parsed-logs
Time Field: @timestamp
```

### **Step 3: Sample Panel Configurations**

#### **🔥 Security Events Timeline**
```json
Query Type: Lucene
Query: status_code:404 OR status_code:403 OR status_code:500
Visualization: Time series
Time Range: Last 24 hours
```

#### **🌍 Geographic Attack Map**
```json
Query: geo.country_name:*
Visualization: Geomap
Aggregation: Terms on geo.country_name
Metric: Count
```

#### **👤 Top User Agents**
```json
Query: user_agent:*
Visualization: Bar chart
Group by: user_agent.keyword
Limit: 10
```

#### **📊 Status Code Distribution**
```json
Query: *
Visualization: Pie chart
Group by: status_code
Order by: Count (Descending)
```

---

## 🛠️ **Method 3: Advanced Custom Dashboard Creation**

### **Create Custom Security Dashboard:**

<function_calls>
<invoke name="create_file">
<parameter name="content">#!/usr/bin/env python3
"""
Custom UEBA Dashboard Creator
============================
Create personalized Grafana dashboards for UEBA system
"""

import requests
import json
from datetime import datetime

class CustomDashboardCreator:
    def __init__(self):
        self.grafana_url = "http://localhost:3000"
        self.auth = ("admin", "admin")
        self.headers = {"Content-Type": "application/json"}
    
    def create_custom_security_dashboard(self, dashboard_name="My Security Dashboard"):
        """Create a custom security monitoring dashboard"""
        
        dashboard = {
            "dashboard": {
                "id": None,
                "uid": None,
                "title": f"🔒 {dashboard_name}",
                "description": f"Custom security dashboard created on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "tags": ["ueba", "custom", "security"],
                "timezone": "browser",
                "time": {"from": "now-24h", "to": "now"},
                "refresh": "30s",
                "panels": [
                    # Panel 1: Security Events Over Time
                    {
                        "id": 1,
                        "title": "🚨 Security Events Timeline",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                        "targets": [{
                            "refId": "A",
                            "query": "status_code:(404 OR 403 OR 500)",
                            "timeField": "@timestamp",
                            "metrics": [{"type": "count", "id": "1"}],
                            "bucketAggs": [{
                                "type": "date_histogram",
                                "id": "2",
                                "settings": {"interval": "auto"}
                            }]
                        }],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "custom": {"drawStyle": "line", "lineInterpolation": "linear"}
                            }
                        }
                    },
                    
                    # Panel 2: Top Source IPs
                    {
                        "id": 2,
                        "title": "🌐 Top Source IPs",
                        "type": "table",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                        "targets": [{
                            "refId": "B",
                            "query": "*",
                            "timeField": "@timestamp",
                            "metrics": [{"type": "count", "id": "1"}],
                            "bucketAggs": [{
                                "type": "terms",
                                "id": "2",
                                "settings": {"field": "remote_addr.keyword", "size": 10}
                            }]
                        }]
                    },
                    
                    # Panel 3: HTTP Methods Distribution
                    {
                        "id": 3,
                        "title": "📊 HTTP Methods",
                        "type": "piechart",
                        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 8},
                        "targets": [{
                            "refId": "C",
                            "query": "*",
                            "timeField": "@timestamp",
                            "metrics": [{"type": "count", "id": "1"}],
                            "bucketAggs": [{
                                "type": "terms",
                                "id": "2",
                                "settings": {"field": "method.keyword", "size": 10}
                            }]
                        }]
                    },
                    
                    # Panel 4: Response Size Trends
                    {
                        "id": 4,
                        "title": "📈 Response Size Trends",
                        "type": "stat",
                        "gridPos": {"h": 8, "w": 6, "x": 6, "y": 8},
                        "targets": [{
                            "refId": "D",
                            "query": "*",
                            "timeField": "@timestamp",
                            "metrics": [{"type": "avg", "id": "1", "field": "bytes_sent"}]
                        }],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "bytes",
                                "color": {"mode": "thresholds"},
                                "thresholds": {
                                    "steps": [
                                        {"color": "green", "value": None},
                                        {"color": "yellow", "value": 1000},
                                        {"color": "red", "value": 10000}
                                    ]
                                }
                            }
                        }
                    },
                    
                    # Panel 5: Real-time Status Codes
                    {
                        "id": 5,
                        "title": "🔥 Real-time Status Codes",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                        "targets": [{
                            "refId": "E",
                            "query": "*",
                            "timeField": "@timestamp",
                            "metrics": [{"type": "count", "id": "1"}],
                            "bucketAggs": [
                                {
                                    "type": "terms",
                                    "id": "2",
                                    "settings": {"field": "status_code", "size": 5}
                                },
                                {
                                    "type": "date_histogram",
                                    "id": "3",
                                    "settings": {"interval": "30s"}
                                }
                            ]
                        }]
                    }
                ]
            },
            "overwrite": True
        }
        
        # Create the dashboard
        try:
            response = requests.post(
                f"{self.grafana_url}/api/dashboards/db",
                json=dashboard,
                auth=self.auth,
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Custom dashboard '{dashboard_name}' created successfully!")
                print(f"🔗 URL: {self.grafana_url}/d/{result.get('uid', '')}")
                return True
            else:
                print(f"❌ Failed to create dashboard: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating dashboard: {e}")
            return False
    
    def create_ml_monitoring_dashboard(self):
        """Create ML-specific monitoring dashboard"""
        dashboard_name = "UEBA ML Monitoring"
        
        dashboard = {
            "dashboard": {
                "id": None,
                "uid": "ueba-ml-monitoring",
                "title": f"🤖 {dashboard_name}",
                "description": "Machine Learning model performance and anomaly detection",
                "tags": ["ueba", "ml", "monitoring", "ai"],
                "timezone": "browser",
                "time": {"from": "now-6h", "to": "now"},
                "refresh": "1m",
                "panels": [
                    # ML Anomaly Detection
                    {
                        "id": 1,
                        "title": "🚨 ML Anomaly Alerts",
                        "type": "stat",
                        "gridPos": {"h": 6, "w": 8, "x": 0, "y": 0},
                        "targets": [{
                            "refId": "A",
                            "query": "anomaly_score:>0.7",
                            "timeField": "@timestamp",
                            "metrics": [{"type": "count", "id": "1"}]
                        }],
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "thresholds"},
                                "thresholds": {
                                    "steps": [
                                        {"color": "green", "value": None},
                                        {"color": "yellow", "value": 5},
                                        {"color": "red", "value": 20}
                                    ]
                                }
                            }
                        }
                    },
                    
                    # Model Performance
                    {
                        "id": 2,
                        "title": "📊 Model Performance",
                        "type": "timeseries",
                        "gridPos": {"h": 6, "w": 16, "x": 8, "y": 0},
                        "targets": [{
                            "refId": "B",
                            "query": "model_name:*",
                            "timeField": "@timestamp",
                            "metrics": [{"type": "avg", "id": "1", "field": "confidence_score"}],
                            "bucketAggs": [
                                {
                                    "type": "terms",
                                    "id": "2",
                                    "settings": {"field": "model_name.keyword", "size": 5}
                                },
                                {
                                    "type": "date_histogram",
                                    "id": "3",
                                    "settings": {"interval": "5m"}
                                }
                            ]
                        }]
                    }
                ]
            },
            "overwrite": True
        }
        
        # Create the dashboard
        try:
            response = requests.post(
                f"{self.grafana_url}/api/dashboards/db",
                json=dashboard,
                auth=self.auth,
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ ML monitoring dashboard created successfully!")
                print(f"🔗 URL: {self.grafana_url}/d/{result.get('uid', '')}")
                return True
            else:
                print(f"❌ Failed to create ML dashboard: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating ML dashboard: {e}")
            return False

def main():
    """Main dashboard creation function"""
    print("🎨 UEBA Custom Dashboard Creator")
    print("=" * 40)
    
    creator = CustomDashboardCreator()
    
    print("\n1. Creating custom security dashboard...")
    creator.create_custom_security_dashboard("My Custom Security Monitor")
    
    print("\n2. Creating ML monitoring dashboard...")
    creator.create_ml_monitoring_dashboard()
    
    print("\n🎉 Custom dashboards created!")
    print("🌐 Access Grafana: http://localhost:3000")

if __name__ == "__main__":
    main()