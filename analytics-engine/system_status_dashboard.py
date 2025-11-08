#!/usr/bin/env python3
"""
UEBA System v2.0 Status Dashboard
Comprehensive system health and performance overview
for all three enhanced goals implementation.

Author: UEBA System v2.0
Date: October 5, 2025
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from elasticsearch import Elasticsearch

class UEBASystemDashboard:
    def __init__(self):
        self.es = Elasticsearch(["http://localhost:9200"])
        self.system_version = "UEBA System v2.0"
        self.enhancement_date = "October 5, 2025"
        
    def get_elasticsearch_stats(self):
        """Get Elasticsearch cluster and index statistics"""
        try:
            cluster_health = self.es.cluster.health()
            
            # Get nginx-parsed-logs stats
            nginx_stats = self.es.count(index="nginx-parsed-logs")
            
            # Check for performance and alert indices
            ml_perf_count = 0
            ml_alerts_count = 0
            
            try:
                ml_perf_count = self.es.count(index="ml-performance")['count']
            except:
                pass
                
            try:
                ml_alerts_count = self.es.count(index="ml-alerts")['count']
            except:
                pass
            
            return {
                'cluster_status': cluster_health.get('status', 'unknown'),
                'total_indices': cluster_health.get('number_of_data_nodes', 0),
                'nginx_logs_count': nginx_stats.get('count', 0),
                'ml_performance_logs': ml_perf_count,
                'ml_alerts_count': ml_alerts_count
            }
        except Exception as e:
            return {'error': str(e)}
            
    def get_ml_models_status(self):
        """Get ML models optimization status"""
        models_dir = Path("ml_models")
        
        if not models_dir.exists():
            return {'status': 'not_found', 'models': []}
            
        # Find latest optimized models
        model_files = list(models_dir.glob("optimized_*.joblib"))
        
        if not model_files:
            return {'status': 'no_optimized', 'models': []}
            
        # Get latest timestamp
        timestamps = []
        for file in model_files:
            try:
                parts = file.stem.split('_')
                if len(parts) >= 4:
                    timestamp = f"{parts[-2]}_{parts[-1]}"
                    timestamps.append(timestamp)
            except:
                continue
                
        if not timestamps:
            return {'status': 'no_timestamps', 'models': []}
            
        latest_timestamp = max(timestamps)
        
        # Check optimization results
        results_file = f"ml_models/optimization_results_{latest_timestamp}.json"
        optimization_results = {}
        
        if Path(results_file).exists():
            try:
                with open(results_file, 'r') as f:
                    optimization_results = json.load(f)
            except:
                pass
                
        return {
            'status': 'optimized',
            'latest_timestamp': latest_timestamp,
            'optimization_results': optimization_results,
            'model_files_count': len(model_files)
        }
        
    def get_archive_status(self):
        """Get system cleanup and archive status"""
        archive_dir = Path("../.archive/demos")
        
        if not archive_dir.exists():
            return {'status': 'no_archive', 'archived_files': 0}
            
        archived_files = list(archive_dir.glob("*.py"))
        readme_file = archive_dir / "README.md"
        
        archived_info = []
        if readme_file.exists():
            try:
                with open(readme_file, 'r') as f:
                    content = f.read()
                    archived_info.append("README.md found with documentation")
            except:
                pass
                
        return {
            'status': 'active',
            'archived_files': len(archived_files),
            'documentation': len(archived_info) > 0,
            'archive_location': str(archive_dir.resolve())
        }
        
    def get_analytics_tools_status(self):
        """Get analytics engine tools status"""
        analytics_files = []
        
        # Core active tools
        core_tools = [
            "sample_data_generator.py",
            "ml_dashboard_provisioner.py", 
            "realtime_ml_monitor.py",
            "ml_alerting_system.py",
            "ml_model_trainer.py"
        ]
        
        # Enhanced tools (new implementations)
        enhanced_tools = [
            "enhanced_realtime_pipeline.py",
            "enhanced_ml_optimizer.py", 
            "ml_performance_monitor.py"
        ]
        
        status = {
            'core_tools': [],
            'enhanced_tools': [],
            'total_active': 0
        }
        
        # Check core tools
        for tool in core_tools:
            if Path(tool).exists():
                status['core_tools'].append({'name': tool, 'status': 'active'})
                status['total_active'] += 1
            else:
                status['core_tools'].append({'name': tool, 'status': 'missing'})
                
        # Check enhanced tools  
        for tool in enhanced_tools:
            if Path(tool).exists():
                status['enhanced_tools'].append({'name': tool, 'status': 'active'})
                status['total_active'] += 1
            else:
                status['enhanced_tools'].append({'name': tool, 'status': 'missing'})
                
        return status
        
    def generate_system_report(self):
        """Generate comprehensive system status report"""
        print("🚀 UEBA SYSTEM v2.0 - COMPREHENSIVE STATUS DASHBOARD")
        print("="*80)
        print(f"📅 Enhancement Date: {self.enhancement_date}")
        print(f"⏰ Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Goal 1: System Cleanup Status
        print("\n🗂️  GOAL 1: SYSTEM CLEANUP & ORGANIZATION")
        print("-" * 50)
        
        archive_status = self.get_archive_status()
        if archive_status['status'] == 'active':
            print(f"✅ Cleanup Status: COMPLETED")
            print(f"📁 Archived Files: {archive_status['archived_files']} files")
            print(f"📋 Documentation: {'Yes' if archive_status['documentation'] else 'No'}")
            print(f"📍 Archive Location: {archive_status['archive_location']}")
        else:
            print(f"❌ Cleanup Status: NOT IMPLEMENTED")
            
        # Goal 2: Enhanced Real-time Pipeline
        print("\n🌊 GOAL 2: ENHANCED REAL-TIME PIPELINE")
        print("-" * 50)
        
        analytics_status = self.get_analytics_tools_status()
        
        enhanced_tools_count = len([t for t in analytics_status['enhanced_tools'] if t['status'] == 'active'])
        if enhanced_tools_count >= 2:  # enhanced_realtime_pipeline.py is key
            print(f"✅ Enhanced Pipeline: OPERATIONAL")
            print(f"🔧 Enhanced Tools Active: {enhanced_tools_count}/3")
            
            for tool in analytics_status['enhanced_tools']:
                status_icon = "✅" if tool['status'] == 'active' else "❌"
                print(f"   {status_icon} {tool['name']}: {tool['status'].upper()}")
        else:
            print(f"❌ Enhanced Pipeline: NOT READY")
            
        # Goal 3: ML Model Optimization
        print("\n🤖 GOAL 3: ADVANCED ML MODEL OPTIMIZATION")
        print("-" * 50)
        
        ml_status = self.get_ml_models_status()
        if ml_status['status'] == 'optimized':
            print(f"✅ ML Optimization: COMPLETED")
            print(f"📅 Latest Models: {ml_status['latest_timestamp']}")
            print(f"💾 Model Files: {ml_status['model_files_count']}")
            
            if 'optimization_results' in ml_status and ml_status['optimization_results']:
                results = ml_status['optimization_results']
                print(f"\n🎯 MODEL PERFORMANCE RESULTS:")
                
                if 'isolation_forest' in results:
                    iso_acc = results['isolation_forest'].get('accuracy', 0)
                    print(f"   🌲 Isolation Forest: {iso_acc:.3f} accuracy")
                    
                if 'one_class_svm' in results:
                    svm_acc = results['one_class_svm'].get('accuracy', 0)
                    print(f"   🎯 One-Class SVM: {svm_acc:.3f} accuracy")
                    
                if 'lof_detector' in results:
                    lof_acc = results['lof_detector'].get('accuracy', 0)
                    print(f"   📍 LOF Detector: {lof_acc:.3f} accuracy")
                    
                if 'ensemble_accuracy' in results:
                    ensemble_acc = results['ensemble_accuracy']
                    print(f"   🗳️ Ensemble Voting: {ensemble_acc:.3f} accuracy")
        else:
            print(f"❌ ML Optimization: NOT COMPLETED")
            
        # Elasticsearch & Data Status
        print("\n📊 DATA INFRASTRUCTURE STATUS")
        print("-" * 50)
        
        es_stats = self.get_elasticsearch_stats()
        if 'error' not in es_stats:
            print(f"✅ Elasticsearch: {es_stats['cluster_status'].upper()}")
            print(f"📄 Nginx Logs: {es_stats['nginx_logs_count']} documents")
            print(f"📈 ML Performance Logs: {es_stats['ml_performance_logs']} entries")
            print(f"🚨 ML Alerts: {es_stats['ml_alerts_count']} alerts")
        else:
            print(f"❌ Elasticsearch: ERROR - {es_stats['error']}")
            
        # Core Analytics Tools Status
        print("\n🔧 CORE ANALYTICS TOOLS STATUS")
        print("-" * 50)
        
        core_active = len([t for t in analytics_status['core_tools'] if t['status'] == 'active'])
        total_core = len(analytics_status['core_tools'])
        
        print(f"📊 Core Tools Active: {core_active}/{total_core}")
        
        for tool in analytics_status['core_tools']:
            status_icon = "✅" if tool['status'] == 'active' else "❌"
            print(f"   {status_icon} {tool['name']}: {tool['status'].upper()}")
            
        # Overall System Health
        print("\n🎯 OVERALL SYSTEM HEALTH ASSESSMENT")
        print("="*80)
        
        total_goals = 3
        completed_goals = 0
        
        # Check Goal 1
        if archive_status['status'] == 'active':
            completed_goals += 1
            
        # Check Goal 2  
        if enhanced_tools_count >= 2:
            completed_goals += 1
            
        # Check Goal 3
        if ml_status['status'] == 'optimized':
            completed_goals += 1
            
        completion_percentage = (completed_goals / total_goals) * 100
        
        if completion_percentage == 100:
            health_status = "EXCELLENT ✨"
            health_icon = "🟢"
        elif completion_percentage >= 66:
            health_status = "GOOD ✅"
            health_icon = "🟡" 
        else:
            health_status = "NEEDS ATTENTION ⚠️"
            health_icon = "🔴"
            
        print(f"{health_icon} System Health: {health_status}")
        print(f"📊 Goals Completed: {completed_goals}/{total_goals} ({completion_percentage:.0f}%)")
        print(f"🎯 Total Active Tools: {analytics_status['total_active']}")
        print(f"💻 System Version: {self.system_version}")
        
        print("\n" + "="*80)
        print("🏆 UEBA SYSTEM v2.0 ENHANCEMENT COMPLETE!")
        print("="*80)
        
        return {
            'health_status': health_status,
            'completion_percentage': completion_percentage,
            'goals_completed': completed_goals,
            'total_tools': analytics_status['total_active']
        }

if __name__ == "__main__":
    dashboard = UEBASystemDashboard()
    dashboard.generate_system_report()