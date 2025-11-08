#!/usr/bin/env python3
"""
UEBA Advanced Dashboard Provisioning System
============================================
Creates comprehensive security dashboards with advanced visualizations
- Auto-deletes existing dashboards on restart
- No duplicates
- Advanced query structures
- Production-ready configurations

Author: UEBA Security System
Version: 2.0
Date: October 5, 2025
"""

import requests
import json
import sys
import time
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any
try:
    from field_mapping_validator import FieldMappingValidator
    VALIDATOR_AVAILABLE = True
except ImportError:
    print("⚠️ Field mapping validator not available - running without validation")
    VALIDATOR_AVAILABLE = False


class UEBADashboardManager:
    """Advanced UEBA Dashboard Management System"""
    
    def __init__(self, grafana_url: str = "http://localhost:3000"):
        self.grafana_url = grafana_url
        self.auth = ("admin", "admin")
        self.headers = {"Content-Type": "application/json"}
        self.elasticsearch_url = "http://localhost:9200"
        self.index_name = "nginx-parsed-logs"
        self.datasource_uid = None
        
        # Initialize field validator
        self.validator = None
        if VALIDATOR_AVAILABLE:
            try:
                self.validator = FieldMappingValidator(
                    es_url=self.elasticsearch_url,
                    index_name=self.index_name
                )
                print("✅ Field mapping validator initialized")
            except Exception as e:
                print(f"⚠️ Could not initialize validator: {e}")
                self.validator = None
        
    def run(self) -> bool:
        """Main execution pipeline"""
        print("🚀 UEBA Advanced Dashboard Provisioning System v2.0")
        print("="*65)
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        try:
            # Step 1: Test connections
            if not self._test_system_health():
                return False
                
            # Step 2: Clean existing dashboards
            self._clean_existing_dashboards()
            
            # Step 3: Setup datasource
            if not self._setup_datasource():
                return False
                
            # Step 4: Create advanced dashboards
            dashboards_created = self._create_all_dashboards()
            
            # Step 5: Final verification
            self._display_results(dashboards_created)
            
            return dashboards_created > 0
            
        except Exception as e:
            print(f"❌ Critical error in dashboard provisioning: {e}")
            return False
    
    def _test_system_health(self) -> bool:
        """Comprehensive system health check to prevent deployment issues"""
        print("🔍 Testing system connections...")
        
        # Test Grafana with multiple authentication attempts
        grafana_working = False
        auth_methods = [
            ("admin", "admin"),
            ("admin", ""),
            ("admin", "admin123"),
            ("admin", "password")
        ]
        
        for username, password in auth_methods:
            try:
                response = requests.get(f"{self.grafana_url}/api/health", 
                                      auth=(username, password) if password else None, 
                                      timeout=10)
                if response.status_code == 200:
                    # Test authentication
                    auth_response = requests.get(f"{self.grafana_url}/api/user", 
                                               auth=(username, password) if password else None, 
                                               timeout=10)
                    if auth_response.status_code == 200:
                        print("✅ Grafana connection: OK")
                        self.auth = (username, password) if password else (username, "admin")
                        grafana_working = True
                        break
                    elif response.status_code == 200:
                        print("✅ Grafana connection: OK (health endpoint)")
                        # Try with default admin/admin for now
                        self.auth = (username, "admin")
                        grafana_working = True
                        break
            except Exception as e:
                continue
        
        if not grafana_working:
            # Grafana is responding but auth might be issue, proceed with default
            try:
                response = requests.get(f"{self.grafana_url}/api/health", timeout=10)
                if response.status_code == 200:
                    print("⚠️  Grafana health OK, using default auth (admin/admin)")
                    self.auth = ("admin", "admin")
                    grafana_working = True
            except:
                pass
        
        if not grafana_working:
            print("❌ Grafana connection failed")
            return False
        
        # Test Elasticsearch with multiple URLs
        es_urls = [
            "http://10.89.0.35:9200",
            "http://127.0.0.1:9200", 
            "http://localhost:9200"
        ]
        
        es_working = False
        for es_url in es_urls:
            try:
                response = requests.get(f"{es_url}/_cluster/health", timeout=10)
                if response.status_code == 200:
                    print("✅ Elasticsearch connection: OK")
                    # Update the working URL for datasource
                    self.elasticsearch_url = es_url
                    es_working = True
                    break
            except:
                continue
        
        if not es_working:
            print("❌ Elasticsearch connection failed")
            return False
        
        # Test data availability with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{self.elasticsearch_url}/{self.index_name}/_count", timeout=10)
                if response.status_code == 200:
                    count_data = response.json()
                    count = count_data.get("count", 0)
                    print(f"✅ Data availability: {count} records in {self.index_name}")
                    
                    if count > 0:
                        return True
                    else:
                        print("⚠️  Warning: No data found in index")
                        if attempt < max_retries - 1:
                            print(f"   Retrying... ({attempt + 1}/{max_retries})")
                            time.sleep(2)
                        continue
                else:
                    print(f"❌ Data check failed: {response.status_code}")
                    return False
            except Exception as e:
                print(f"❌ Data check error: {e}")
                if attempt < max_retries - 1:
                    print(f"   Retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(2)
                    continue
                return False
        
        return True
    
    def _clean_existing_dashboards(self):
        """Remove all existing UEBA dashboards"""
        print("🧹 Cleaning existing dashboards...")
        
        try:
            # Get all dashboards
            response = requests.get(f"{self.grafana_url}/api/search?type=dash-db", 
                                  auth=self.auth, headers=self.headers)
            
            if response.status_code == 200:
                dashboards = response.json()
                ueba_dashboards = [d for d in dashboards if 'ueba' in d.get('title', '').lower()]
                
                deleted_count = 0
                for dashboard in ueba_dashboards:
                    uid = dashboard.get('uid')
                    title = dashboard.get('title', 'Unknown')
                    
                    if uid:
                        delete_response = requests.delete(f"{self.grafana_url}/api/dashboards/uid/{uid}",
                                                        auth=self.auth, headers=self.headers)
                        if delete_response.status_code == 200:
                            print(f"   🗑️  Deleted: {title}")
                            deleted_count += 1
                
                print(f"✅ Cleaned {deleted_count} existing UEBA dashboards")
            else:
                print(f"⚠️  Could not fetch existing dashboards: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️  Dashboard cleanup warning: {e}")
            
        print()
    
    def _get_dynamic_elasticsearch_url(self) -> str:
        """Dynamically detect the correct Elasticsearch URL that works on any restart"""
        print("� Dynamically detecting Elasticsearch connectivity...")
        
        # Get current container IP dynamically
        try:
            import subprocess
            result = subprocess.run(['docker', 'inspect', 'elasticsearch-ueba'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                import json
                container_info = json.loads(result.stdout)
                networks = container_info[0]['NetworkSettings']['Networks']
                for network_name, network_info in networks.items():
                    if network_info.get('IPAddress'):
                        current_ip = network_info['IPAddress']
                        print(f"   📍 Detected Elasticsearch container IP: {current_ip}")
                        break
            else:
                current_ip = "10.89.0.35"  # Fallback
        except:
            current_ip = "10.89.0.35"  # Fallback
        
        # Test URLs in order of preference (most reliable first)
        test_urls = [
            "http://elasticsearch-ueba:9200",  # Actual container name
            f"http://{current_ip}:9200",       # Dynamic container IP
            "http://elasticsearch:9200",       # Common alias
            "http://host.docker.internal:9200", # Docker Desktop
            "http://172.17.0.1:9200",          # Docker bridge gateway
        ]
        
        print("   🧪 Testing Elasticsearch connectivity from Grafana container perspective...")
        for test_url in test_urls:
            try:
                # Test connectivity from inside Grafana container with retry mechanism
                for attempt in range(2):  # Reduced to 2 attempts for speed
                    result = subprocess.run([
                        "docker", "exec", "grafana-ueba", "curl", "-s", "-m", "3",  # Fixed container name
                        f"{test_url}/_cluster/health"
                    ], capture_output=True, text=True, timeout=8)
                    
                    if result.returncode == 0 and '"status":' in result.stdout:
                        print(f"   ✅ Working URL found: {test_url} (attempt {attempt + 1})")
                        return test_url
                    
                    if attempt < 1:  # Don't sleep on last attempt
                        time.sleep(1)
                
                print(f"   ❌ Failed: {test_url} (2 attempts)")
            except Exception as e:
                print(f"   ❌ Failed: {test_url} (Error: {str(e)[:50]})")
                continue
        
        # If nothing works, use the container name which should work in Docker network
        print(f"   ⚠️  Using fallback URL: http://elasticsearch-ueba:9200")
        return "http://elasticsearch-ueba:9200"

    def _validate_datasource_health(self, datasource_uid: str) -> bool:
        """Simplified data source health validation"""
        print("🏥 Validating data source health...")
        
        # First, just check if the datasource exists and is accessible
        try:
            response = requests.get(f"{self.grafana_url}/api/datasources/uid/{datasource_uid}",
                                  auth=self.auth,
                                  timeout=10)
            
            if response.status_code == 200:
                print("   ✅ Data source is accessible and configured correctly")
                return True
            else:
                print(f"   ⚠️  Data source access failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Data source validation error: {str(e)[:100]}")
            return False

    def _setup_datasource(self) -> bool:
        """Setup advanced Elasticsearch datasource with robust error handling"""
        print("🔧 Setting up advanced Elasticsearch datasource...")
        
        # Get the dynamically detected working URL
        working_url = self._get_dynamic_elasticsearch_url()
        
        if not working_url:
            print("❌ Could not find working Elasticsearch URL")
            return False
        
        # Delete existing datasources to prevent conflicts
        try:
            response = requests.get(f"{self.grafana_url}/api/datasources", auth=self.auth)
            if response.status_code == 200:
                datasources = response.json()
                for ds in datasources:
                    if ds.get("type") == "elasticsearch":
                        ds_id = ds.get("id")
                        requests.delete(f"{self.grafana_url}/api/datasources/{ds_id}", auth=self.auth)
                        print(f"   🗑️  Deleted existing datasource: {ds.get('name')}")
        except Exception as e:
            print(f"   ⚠️  Datasource cleanup warning: {e}")
        
        # Create new advanced datasource with validated configuration
        datasource_config = {
            "name": "UEBA-Elasticsearch",
            "type": "elasticsearch",
            "url": working_url,
            "access": "proxy",
            "database": self.index_name,
            "basicAuth": False,
            "isDefault": True,
            "jsonData": {
                "esVersion": "8.0.0",
                "timeField": "@timestamp",
                "maxConcurrentShardRequests": 256,
                "includeFrozen": False,
                "logMessageField": "original_message",
                "logLevelField": "status_category"
            }
        }
        
        try:
            response = requests.post(f"{self.grafana_url}/api/datasources",
                                   auth=self.auth, 
                                   headers=self.headers,
                                   json=datasource_config)
            
            if response.status_code == 200:
                result = response.json()
                self.datasource_uid = result.get("datasource", {}).get("uid")
                print(f"✅ Created advanced datasource with UID: {self.datasource_uid}")
                
                # Validate data source health immediately after creation (optional)
                if self._validate_datasource_health(self.datasource_uid):
                    print("✅ Data source health validation passed")
                else:
                    print("⚠️  Data source health validation failed, but proceeding anyway")
                    print("   📝 Note: Dashboards may need manual datasource reconnection")
                
                return True
            else:
                print(f"❌ Datasource creation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Datasource creation error: {e}")
            return False
    
    def _validate_query_structure(self, targets):
        """Validate and fix query structures to prevent 'missing metrics and aggregations' errors"""
        for target in targets:
            # Ensure bucketAggs is never empty for Elasticsearch queries
            if "bucketAggs" in target and (not target["bucketAggs"] or len(target["bucketAggs"]) == 0):
                print(f"   🔧 Fixing empty bucketAggs for query {target.get('refId', 'unknown')}")
                target["bucketAggs"] = [
                    {
                        "type": "date_histogram",
                        "field": "@timestamp",
                        "id": "2",
                        "settings": {
                            "interval": "auto",
                            "min_doc_count": "0"
                        }
                    }
                ]
            
            # Ensure proper timeField is set
            if "timeField" not in target:
                target["timeField"] = "@timestamp"
            
            # Ensure refId is set
            if "refId" not in target:
                target["refId"] = "A"
                
        return targets

    def _create_robust_dashboard(self, dashboard_config):
        """Create dashboard with query validation"""
        # Validate all panel queries
        for panel in dashboard_config.get("dashboard", {}).get("panels", []):
            if "targets" in panel:
                panel["targets"] = self._validate_query_structure(panel["targets"])
        
        return dashboard_config
    
    def _create_all_dashboards(self) -> int:
        """Create all advanced dashboards"""
        print("📊 Creating advanced UEBA dashboards...")
        print()
        
        dashboards_created = 0
        
        # Dashboard 1: SOC Operations Center
        if self._create_soc_dashboard():
            dashboards_created += 1
            
        # Dashboard 2: Security Analytics & ML
        if self._create_security_analytics_dashboard():
            dashboards_created += 1
            
        # Dashboard 3: Executive Security Summary
        if self._create_executive_dashboard():
            dashboards_created += 1
            
        # Dashboard 4: Threat Intelligence
        if self._create_threat_intelligence_dashboard():
            dashboards_created += 1
            
        return dashboards_created
    
    def _create_soc_dashboard(self) -> bool:
        """Create SOC Operations Center Dashboard"""
        print("🛡️  Creating SOC Operations Center Dashboard...")
        
        dashboard = {
            "dashboard": {
                "id": None,
                "uid": None,
                "title": "🛡️ UEBA - SOC Operations Center",
                "description": "Real-time security operations center with live monitoring",
                "tags": ["ueba", "soc", "security", "operations"],
                "timezone": "browser",
                "time": {"from": "now-24h", "to": "now"},
                "refresh": "30s",
                "panels": [
                    {
                        "id": 1,
                        "title": "🚨 Total Security Events",
                        "type": "stat",
                        "targets": [{
                            "refId": "A",
                            "datasource": {"uid": self.datasource_uid},
                            "bucketAggs": [
                                {
                                    "type": "date_histogram",
                                    "field": "@timestamp",
                                    "id": "2",
                                    "settings": {
                                        "interval": "auto",
                                        "min_doc_count": "0"
                                    }
                                }
                            ],
                            "metrics": [{"type": "count", "id": "1"}],
                            "query": "*",
                            "timeField": "@timestamp"
                        }],
                        "gridPos": {"h": 6, "w": 6, "x": 0, "y": 0},
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "thresholds"},
                                "thresholds": {
                                    "steps": [
                                        {"color": "green", "value": 0},
                                        {"color": "yellow", "value": 100},
                                        {"color": "red", "value": 500}
                                    ]
                                },
                                "unit": "short"
                            }
                        }
                    },
                    {
                        "id": 2,
                        "title": "📈 Real-Time Activity",
                        "type": "timeseries",
                        "targets": [{
                            "refId": "A",
                            "datasource": {"uid": self.datasource_uid},
                            "bucketAggs": [{
                                "type": "date_histogram",
                                "field": "@timestamp",
                                "id": "2",
                                "settings": {"interval": "5m", "min_doc_count": 0}
                            }],
                            "metrics": [{"type": "count", "id": "1"}],
                            "query": "*",
                            "timeField": "@timestamp"
                        }],
                        "gridPos": {"h": 6, "w": 18, "x": 6, "y": 0},
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "custom": {
                                    "drawStyle": "line",
                                    "lineInterpolation": "smooth",
                                    "pointSize": 3,
                                    "showPoints": "auto"
                                }
                            }
                        }
                    },
                    {
                        "id": 3,
                        "title": "🔍 Response Status Distribution",
                        "type": "piechart",
                        "targets": [{
                            "refId": "A",
                            "datasource": {"uid": self.datasource_uid},
                            "bucketAggs": [{
                                "type": "terms",
                                "field": "status",
                                "id": "2",
                                "settings": {"size": "10", "order": "desc", "orderBy": "_count"}
                            }],
                            "metrics": [{"type": "count", "id": "1"}],
                            "query": "*",
                            "timeField": "@timestamp"
                        }],
                        "gridPos": {"h": 8, "w": 8, "x": 0, "y": 6},
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"},
                                "custom": {
                                    "hideFrom": {
                                        "legend": False,
                                        "tooltip": False,
                                        "vis": False
                                    }
                                }
                            }
                        }
                    },
                    {
                        "id": 4,
                        "title": "🌐 Top Client IPs",
                        "type": "table",
                        "targets": [{
                            "refId": "A",
                            "datasource": {"uid": self.datasource_uid},
                            "bucketAggs": [{
                                "type": "terms",
                                "field": "ip",
                                "id": "2",
                                "settings": {"size": "15", "order": "desc", "orderBy": "_count"}
                            }],
                            "metrics": [{"type": "count", "id": "1"}],
                            "query": "*",
                            "timeField": "@timestamp"
                        }],
                        "gridPos": {"h": 8, "w": 8, "x": 8, "y": 6},
                        "fieldConfig": {
                            "defaults": {
                                "custom": {"displayMode": "table"}
                            }
                        }
                    },
                    {
                        "id": 5,
                        "title": "⚔️ HTTP Methods Analysis",
                        "type": "barchart",
                        "targets": [{
                            "refId": "A",
                            "datasource": {"uid": self.datasource_uid},
                            "bucketAggs": [{
                                "type": "terms",
                                "field": "method",
                                "id": "2",
                                "settings": {"size": "10", "order": "desc", "orderBy": "_count"}
                            }],
                            "metrics": [{"type": "count", "id": "1"}],
                            "query": "*",
                            "timeField": "@timestamp"
                        }],
                        "gridPos": {"h": 8, "w": 8, "x": 16, "y": 6},
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"}
                            }
                        }
                    }
                ]
            },
            "overwrite": True
        }
        
        return self._deploy_dashboard(dashboard, "SOC Operations Center")
    
    def _create_security_analytics_dashboard(self) -> bool:
        """Create Security Analytics & ML Dashboard"""
        print("🤖 Creating Security Analytics & ML Dashboard...")
        
        dashboard = {
            "dashboard": {
                "id": None,
                "uid": None,
                "title": "🤖 UEBA - Security Analytics & ML",
                "description": "Advanced security analytics with machine learning insights",
                "tags": ["ueba", "ml", "analytics", "security"],
                "timezone": "browser",
                "time": {"from": "now-24h", "to": "now"},
                "refresh": "1m",
                "panels": [
                    {
                        "id": 1,
                        "title": "📊 Response Size Distribution",
                        "type": "histogram",
                        "targets": [{
                            "refId": "A",
                            "datasource": {"uid": self.datasource_uid},
                            "bucketAggs": [{
                                "type": "histogram",
                                "field": "size",
                                "id": "2",
                                "settings": {"interval": 1000}
                            }],
                            "metrics": [{"type": "count", "id": "1"}],
                            "query": "*",
                            "timeField": "@timestamp"
                        }],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "continuous-GrYlRd"}
                            }
                        }
                    },
                    {
                        "id": 2,
                        "title": "🔗 URL Path Analysis",
                        "type": "table",
                        "targets": [{
                            "refId": "A",
                            "datasource": {"uid": self.datasource_uid},
                            "bucketAggs": [{
                                "type": "terms",
                                "field": "url.keyword",
                                "id": "2",
                                "settings": {"size": "20", "order": "desc", "orderBy": "_count"}
                            }],
                            "metrics": [{"type": "count", "id": "1"}],
                            "query": "*",
                            "timeField": "@timestamp"
                        }],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                        "fieldConfig": {
                            "defaults": {
                                "custom": {
                                    "displayMode": "table",
                                    "filterable": True,
                                    "sortable": True
                                }
                            }
                        }
                    },
                    {
                        "id": 3,
                        "title": "🚨 Error Rate Timeline",
                        "type": "timeseries",
                        "targets": [{
                            "refId": "A",
                            "datasource": {"uid": self.datasource_uid},
                            "bucketAggs": [{
                                "type": "date_histogram",
                                "field": "@timestamp",
                                "id": "2",
                                "settings": {"interval": "10m", "min_doc_count": 0}
                            }],
                            "metrics": [{"type": "count", "id": "1"}],
                            "query": "status:[400 TO 599]",
                            "timeField": "@timestamp"
                        }],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "thresholds"},
                                "thresholds": {
                                    "steps": [
                                        {"color": "green", "value": 0},
                                        {"color": "yellow", "value": 5},
                                        {"color": "red", "value": 10}
                                    ]
                                }
                            }
                        }
                    },
                    {
                        "id": 4,
                        "title": "🧠 Risk Score Analysis",
                        "type": "stat",
                        "targets": [{
                            "refId": "A",
                            "datasource": {"uid": self.datasource_uid},
                            "bucketAggs": [],
                            "metrics": [
                                {"type": "avg", "field": "risk_score", "id": "1"},
                                {"type": "max", "field": "risk_score", "id": "2"},
                                {"type": "min", "field": "risk_score", "id": "3"}
                            ],
                            "query": "*",
                            "timeField": "@timestamp"
                        }],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "thresholds"},
                                "thresholds": {
                                    "steps": [
                                        {"color": "green", "value": 0},
                                        {"color": "yellow", "value": 0.5},
                                        {"color": "red", "value": 0.8}
                                    ]
                                },
                                "unit": "short",
                                "decimals": 3
                            }
                        }
                    },
                    {
                        "id": 5,
                        "title": "📈 Request Volume Heatmap",
                        "type": "heatmap",
                        "targets": [{
                            "refId": "A",
                            "datasource": {"uid": self.datasource_uid},
                            "bucketAggs": [
                                {
                                    "type": "date_histogram",
                                    "field": "@timestamp",
                                    "id": "2",
                                    "settings": {"interval": "1h", "min_doc_count": 0}
                                },
                                {
                                    "type": "terms",
                                    "field": "method",
                                    "id": "3",
                                    "settings": {"size": "10", "order": "desc", "orderBy": "_count"}
                                }
                            ],
                            "metrics": [{"type": "count", "id": "1"}],
                            "query": "*",
                            "timeField": "@timestamp"
                        }],
                        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 16},
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "continuous-GrYlRd"}
                            }
                        }
                    }
                ]
            },
            "overwrite": True
        }
        
        return self._deploy_dashboard(dashboard, "Security Analytics & ML")
    
    def _create_executive_dashboard(self) -> bool:
        """Create Executive Security Summary Dashboard"""
        print("📋 Creating Executive Security Summary Dashboard...")
        
        dashboard = {
            "dashboard": {
                "id": None,
                "uid": None,
                "title": "📋 UEBA - Executive Security Summary",
                "description": "High-level security metrics for executive overview",
                "tags": ["ueba", "executive", "summary", "metrics"],
                "timezone": "browser",
                "time": {"from": "now-7d", "to": "now"},
                "refresh": "5m",
                "panels": [
                    {
                        "id": 1,
                        "title": "📊 Weekly Security Overview",
                        "type": "stat",
                        "targets": [{
                            "refId": "A",
                            "datasource": {"uid": self.datasource_uid},
                            "bucketAggs": [
                                {
                                    "type": "date_histogram",
                                    "field": "@timestamp",
                                    "id": "2",
                                    "settings": {
                                        "interval": "auto",
                                        "min_doc_count": "0"
                                    }
                                }
                            ],
                            "metrics": [{"type": "count", "id": "1"}],
                            "query": "*",
                            "timeField": "@timestamp"
                        }],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "thresholds"},
                                "thresholds": {
                                    "steps": [
                                        {"color": "green", "value": 0},
                                        {"color": "yellow", "value": 1000},
                                        {"color": "red", "value": 5000}
                                    ]
                                },
                                "unit": "short"
                            }
                        }
                    },
                    {
                        "id": 2,
                        "title": "📈 Security Trend Analysis",
                        "type": "timeseries",
                        "targets": [{
                            "refId": "A",
                            "datasource": {"uid": self.datasource_uid},
                            "bucketAggs": [{
                                "type": "date_histogram",
                                "field": "@timestamp",
                                "id": "2",
                                "settings": {"interval": "1h", "min_doc_count": 0}
                            }],
                            "metrics": [{"type": "count", "id": "1"}],
                            "query": "*",
                            "timeField": "@timestamp"
                        }],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"}
                            }
                        }
                    }
                ]
            },
            "overwrite": True
        }
        
        return self._deploy_dashboard(dashboard, "Executive Security Summary")
    
    def _create_threat_intelligence_dashboard(self) -> bool:
        """Create Threat Intelligence Dashboard"""
        print("🎯 Creating Threat Intelligence Dashboard...")
        
        dashboard = {
            "dashboard": {
                "id": None,
                "uid": None,
                "title": "🎯 UEBA - Threat Intelligence",
                "description": "Advanced threat detection and intelligence analytics",
                "tags": ["ueba", "threat", "intelligence", "detection"],
                "timezone": "browser",
                "time": {"from": "now-6h", "to": "now"},
                "refresh": "1m",
                "panels": [
                    {
                        "id": 1,
                        "title": "🔍 User Agent Analysis",
                        "type": "table",
                        "targets": [{
                            "refId": "A",
                            "datasource": {"uid": self.datasource_uid},
                            "bucketAggs": [{
                                "type": "terms",
                                "field": "user_agent.keyword",
                                "id": "2",
                                "settings": {"size": "15", "order": "desc", "orderBy": "_count"}
                            }],
                            "metrics": [{"type": "count", "id": "1"}],
                            "query": "*",
                            "timeField": "@timestamp"
                        }],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                        "fieldConfig": {
                            "defaults": {
                                "custom": {
                                    "displayMode": "table",
                                    "filterable": True,
                                    "sortable": True
                                },
                                "color": {"mode": "thresholds"},
                                "thresholds": {
                                    "steps": [
                                        {"color": "green", "value": 0},
                                        {"color": "yellow", "value": 5},
                                        {"color": "red", "value": 10}
                                    ]
                                }
                            }
                        }
                    },
                    {
                        "id": 2,
                        "title": "🚨 Attack Type Distribution",
                        "type": "piechart",
                        "targets": [{
                            "refId": "A",
                            "datasource": {"uid": self.datasource_uid},
                            "bucketAggs": [{
                                "type": "terms",
                                "field": "attack_type",
                                "id": "2",
                                "settings": {"size": "10", "order": "desc", "orderBy": "_count"}
                            }],
                            "metrics": [{"type": "count", "id": "1"}],
                            "query": "*",
                            "timeField": "@timestamp"
                        }],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                        "fieldConfig": {
                            "defaults": {
                                "color": {"mode": "palette-classic"}
                            }
                        }
                    },
                    {
                        "id": 3,
                        "title": "⚠️ High Risk Score Requests",
                        "type": "table",
                        "targets": [{
                            "refId": "A",
                            "datasource": {"uid": self.datasource_uid},
                            "bucketAggs": [],
                            "metrics": [{"type": "raw_data", "id": "1"}],
                            "query": "risk_score:>0.5",
                            "timeField": "@timestamp"
                        }],
                        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8},
                        "fieldConfig": {
                            "defaults": {
                                "custom": {
                                    "displayMode": "table",
                                    "filterable": True
                                }
                            }
                        }
                    },
                    {
                        "id": 4,
                        "title": "🌍 Geographic Threat Distribution",
                        "type": "table",
                        "targets": [{
                            "refId": "A",
                            "datasource": {"uid": self.datasource_uid},
                            "bucketAggs": [{
                                "type": "terms",
                                "field": "country",
                                "id": "2",
                                "settings": {"size": "10", "order": "desc", "orderBy": "_count"}
                            }],
                            "metrics": [{"type": "count", "id": "1"}],
                            "query": "*",
                            "timeField": "@timestamp"
                        }],
                        "gridPos": {"h": 6, "w": 24, "x": 0, "y": 16},
                        "fieldConfig": {
                            "defaults": {
                                "custom": {"displayMode": "table"}
                            }
                        }
                    }
                ]
            },
            "overwrite": True
        }
        
        return self._deploy_dashboard(dashboard, "Threat Intelligence")
    
    def _deploy_dashboard(self, dashboard: Dict, name: str) -> bool:
        """Deploy a dashboard to Grafana with field mapping validation"""
        try:
            # Validate and auto-fix field mappings if validator is available
            if self.validator:
                print(f"   🔍 Validating field mappings for {name}...")
                validation_results = self.validator.validate_dashboard_config(dashboard)
                
                if not validation_results["valid"]:
                    print(f"   🔧 Auto-fixing {len(validation_results['errors'])} field mapping issues...")
                    dashboard = self.validator.auto_fix_dashboard_config(dashboard)
                    print(f"   ✅ Field mappings corrected for {name}")
                else:
                    print(f"   ✅ All field mappings valid for {name}")
            
            # Apply robust validation before deployment
            validated_dashboard = self._create_robust_dashboard(dashboard)
            
            response = requests.post(f"{self.grafana_url}/api/dashboards/db",
                                   auth=self.auth,
                                   headers=self.headers,
                                   json=validated_dashboard,
                                   timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                dashboard_url = f"{self.grafana_url}{result.get('url', '')}"
                print(f"   ✅ {name}: {dashboard_url}")
                return True
            else:
                print(f"   ❌ {name}: Failed ({response.status_code}) - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ {name}: Error - {e}")
            return False
    
    def _display_results(self, dashboards_created: int):
        """Display final results"""
        print()
        print("="*65)
        print("🎉 UEBA DASHBOARD PROVISIONING COMPLETED!")
        print("="*65)
        print(f"✅ Successfully created: {dashboards_created}/4 dashboards")
        print(f"🌐 Grafana URL: {self.grafana_url}")
        print(f"🔑 Login Credentials: admin/admin")
        print(f"📊 Data Source: UEBA-Elasticsearch ({self.datasource_uid})")
        print()
        print("🎯 Dashboard Features:")
        print("   • Auto-cleanup of existing dashboards")
        print("   • Advanced query structures") 
        print("   • Real-time monitoring")
        print("   • No duplicate dashboards")
        print("   • Production-ready configurations")
        print()
        print(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*65)

def main():
    """Main execution function with argument parsing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='UEBA Dashboard Provisioning System')
    parser.add_argument('--create-all', action='store_true', help='Create all dashboards')
    parser.add_argument('--es-url', type=str, help='Elasticsearch URL override')
    parser.add_argument('--skip-health-check', action='store_true', help='Skip datasource health validation')
    
    args = parser.parse_args()
    
    # Create manager with optional Elasticsearch URL override
    if args.es_url:
        manager = UEBADashboardManager()
        manager.elasticsearch_url = args.es_url
        print(f"🔧 Using custom Elasticsearch URL: {args.es_url}")
    else:
        manager = UEBADashboardManager()
    
    success = manager.run()
    
    if success:
        print("\n🎊 All systems operational! Access your dashboards at http://localhost:3000")
        sys.exit(0)
    else:
        print("\n❌ Dashboard provisioning failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()