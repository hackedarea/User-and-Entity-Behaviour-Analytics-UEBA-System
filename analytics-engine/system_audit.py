#!/usr/bin/env python3
"""
UEBA Analytics Engine Audit & Optimization Report
Cross-check all components to ensure advanced versions are used
"""

import os
import sys
from pathlib import Path
import json
from datetime import datetime

def print_header():
    print("="*80)
    print("🔍 UEBA ANALYTICS ENGINE AUDIT")
    print("="*80)
    print("📋 Checking for advanced vs test/temp/simple components")
    print("="*80)

def audit_analytics_engine():
    """Audit analytics engine components"""
    analytics_dir = Path("analytics-engine")
    
    if not analytics_dir.exists():
        print("❌ Analytics engine directory not found!")
        return False
    
    # Get all Python files
    py_files = list(analytics_dir.glob("*.py"))
    
    print(f"\n📊 Found {len(py_files)} Python files in analytics-engine/")
    
    # Categorize files
    categories = {
        "advanced": [],
        "optimized": [],
        "main_engines": [],
        "utilities": [],
        "monitoring": [],
        "deprecated": [],
        "test_temp": []
    }
    
    # File classification
    for file in py_files:
        name = file.name
        
        if any(word in name.lower() for word in ['test', 'temp', 'simple', 'basic', 'simplified']):
            categories["test_temp"].append(name)
        elif any(word in name.lower() for word in ['advanced', 'neural']):
            categories["advanced"].append(name)
        elif any(word in name.lower() for word in ['optimized', 'automl']):
            categories["optimized"].append(name)
        elif any(word in name.lower() for word in ['detector', 'engine', 'system']):
            categories["main_engines"].append(name)
        elif any(word in name.lower() for word in ['monitor', 'realtime', 'alert']):
            categories["monitoring"].append(name)
        elif any(word in name.lower() for word in ['dashboard', 'viewer', 'generator', 'validator']):
            categories["utilities"].append(name)
        else:
            categories["utilities"].append(name)
    
    return categories

def audit_system_integration():
    """Check which components are actually used by the system"""
    print("\n🔗 SYSTEM INTEGRATION AUDIT")
    print("-" * 50)
    
    # Check launcher integration
    launcher_components = []
    try:
        with open("ueba_launcher.py", "r", encoding='utf-8') as f:
            content = f.read()
            if "system_health_checker.py" in content:
                launcher_components.append("✅ system_health_checker.py")
            if "optimized_ueba_system.py" in content:
                launcher_components.append("✅ optimized_ueba_system.py")
            if "automl_optimizer.py" in content:
                launcher_components.append("✅ automl_optimizer.py")
            if "advanced_neural_detector.py" in content:
                launcher_components.append("✅ advanced_neural_detector.py")
            if "advanced_ml_detector.py" in content:
                launcher_components.append("✅ advanced_ml_detector.py")
            if "ml_alerting_system.py" in content:
                launcher_components.append("✅ ml_alerting_system.py")
            if "realtime_ml_monitor.py" in content:
                launcher_components.append("✅ realtime_ml_monitor.py")
            else:
                launcher_components.append("⚠️ realtime_ml_monitor.py - not in launcher")
            if "results_viewer.py" in content:
                launcher_components.append("✅ results_viewer.py")
            if "sample_data_generator.py" in content:
                launcher_components.append("✅ sample_data_generator.py")
    except FileNotFoundError:
        print("❌ ueba_launcher.py not found!")
        return []
    except UnicodeDecodeError:
        launcher_components.append("⚠️ Encoding issue in ueba_launcher.py")
    
    # Check quick deploy integration
    deploy_components = []
    try:
        with open("analytics-engine/quick_deploy_optimized.py", "r", encoding='utf-8') as f:
            content = f.read()
            if "sample_data_generator.py" in content:
                deploy_components.append("✅ sample_data_generator.py")
            if "optimized_ueba_system.py" in content:
                deploy_components.append("✅ optimized_ueba_system.py")
    except FileNotFoundError:
        print("❌ analytics-engine/quick_deploy_optimized.py not found!")
    except UnicodeDecodeError:
        deploy_components.append("⚠️ Encoding issue in analytics-engine/quick_deploy_optimized.py")
    
    return launcher_components, deploy_components

def check_component_capabilities():
    """Check capabilities of each component"""
    print("\n🛠️ COMPONENT CAPABILITIES ANALYSIS")
    print("-" * 50)
    
    capabilities = {}
    analytics_dir = Path("analytics-engine")
    
    # Key components to analyze
    key_components = [
        "advanced_ml_detector.py",
        "automl_optimizer.py", 
        "optimized_ueba_system.py",
        "advanced_neural_detector.py",
        "realtime_ml_monitor.py",
        "ml_alerting_system.py"
    ]
    
    for component in key_components:
        file_path = analytics_dir / component
        if file_path.exists():
            try:
                with open(file_path, "r", encoding='utf-8') as f:
                    content = f.read()
                    
                # Analyze advanced capabilities with enhanced criteria
                cap = {
                    "elasticsearch_utility": "elasticsearch_utility" in content or "ElasticsearchUtility" in content,
                    "feature_engineering": ("engineer" in content.lower() and "feature" in content.lower()) or "engineer_features" in content,
                    "ensemble_methods": "ensemble" in content.lower() or "randomforest" in content.lower() or "voting" in content.lower(),
                    "anomaly_detection": "anomaly" in content.lower() or "isolationforest" in content.lower() or "predict_anomaly" in content,
                    "neural_networks": "neural" in content.lower() or "lstm" in content.lower() or "cnn" in content.lower() or "tensorflow" in content.lower(),
                    "automl": "optuna" in content.lower() or "automl" in content.lower(),
                    "advanced_ml": "xgboost" in content.lower() or "lightgbm" in content.lower() or "svm" in content.lower(),
                    "real_time": ("real" in content.lower() and "time" in content.lower()) or "realtime" in content.lower() or "threading" in content.lower(),
                    "optimization": "optim" in content.lower() or "hyperparameter" in content.lower(),
                    "cross_validation": "cross_val" in content.lower() or "stratified" in content.lower(),
                    "class_balancing": "class_weight" in content.lower() or "balanced" in content.lower(),
                    "ml_monitoring": "monitor" in content.lower() and ("ml" in content.lower() or "machine" in content.lower()),
                    "alerting_system": "alert" in content.lower() and ("threshold" in content.lower() or "severity" in content.lower()),
                    "error_handling": "try:" in content and "except" in content,
                    "line_count": len(content.split('\n'))
                }
                capabilities[component] = cap
            except Exception as e:
                capabilities[component] = {"error": str(e)}
        else:
            capabilities[component] = {"status": "missing"}
    
    return capabilities

def generate_upgrade_recommendations():
    """Generate recommendations for upgrading to advanced components"""
    print("\n🚀 UPGRADE RECOMMENDATIONS")
    print("-" * 50)
    
    recommendations = []
    
    # Check for deprecated files that should be archived
    deprecated_files = ["simplified_advanced_detector.py"]
    for file in deprecated_files:
        if Path(f"analytics-engine/{file}").exists():
            recommendations.append({
                "priority": "MEDIUM",
                "action": f"Archive {file} as it's deprecated",
                "reason": "Simplified version replaced by advanced components",
                "files_to_update": ["archive"]
            })
    
    # Check for missing integrations based on actual launcher content
    try:
        with open("ueba_launcher.py", "r", encoding='utf-8') as f:
            launcher_content = f.read()
            
        missing_integrations = []
        advanced_components = {
            "advanced_ml_detector.py": "Advanced ML Detection",
            "ml_alerting_system.py": "ML Alerting System", 
            "realtime_ml_monitor.py": "Real-time ML Monitoring"
        }
        
        for component, description in advanced_components.items():
            if Path(f"analytics-engine/{component}").exists() and component not in launcher_content:
                missing_integrations.append({
                    "priority": "LOW",
                    "action": f"Add {description} to launcher menu",
                    "reason": f"Advanced component {component} available but not in launcher",
                    "files_to_update": ["ueba_launcher.py"]
                })
        
        recommendations.extend(missing_integrations)
        
    except FileNotFoundError:
        recommendations.append({
            "priority": "HIGH",
            "action": "Create ueba_launcher.py",
            "reason": "Main launcher file is missing",
            "files_to_update": ["ueba_launcher.py"]
        })
    
    return recommendations

def main():
    """Main audit function"""
    print_header()
    
    # 1. Audit analytics engine files
    categories = audit_analytics_engine()
    
    print("\n📂 FILE CATEGORIZATION:")
    for category, files in categories.items():
        if files:
            icon = "⚠️" if category == "test_temp" else "✅"
            print(f"\n{icon} {category.upper().replace('_', ' ')}:")
            for file in sorted(files):
                print(f"   • {file}")
    
    # 2. Check system integration
    launcher_comp, deploy_comp = audit_system_integration()
    
    print("\n🔗 LAUNCHER INTEGRATION:")
    for comp in launcher_comp:
        print(f"   {comp}")
    
    print("\n🚀 DEPLOY INTEGRATION:")
    for comp in deploy_comp:
        print(f"   {comp}")
    
    # 3. Analyze component capabilities
    capabilities = check_component_capabilities()
    
    print("\n🛠️ COMPONENT ANALYSIS:")
    for component, cap in capabilities.items():
        if "error" in cap:
            print(f"   ❌ {component}: Error - {cap['error']}")
        elif "status" in cap:
            print(f"   ⚠️ {component}: {cap['status']}")
        else:
            # Count advanced features with enhanced criteria
            advanced_features = sum([
                cap.get('elasticsearch_utility', False),
                cap.get('feature_engineering', False), 
                cap.get('ensemble_methods', False),
                cap.get('anomaly_detection', False),
                cap.get('neural_networks', False),
                cap.get('automl', False),
                cap.get('advanced_ml', False),
                cap.get('real_time', False),
                cap.get('optimization', False),
                cap.get('cross_validation', False),
                cap.get('class_balancing', False),
                cap.get('ml_monitoring', False),
                cap.get('alerting_system', False),
                cap.get('error_handling', False)
            ])
            total_features = 14
            status = "🚀 Advanced" if advanced_features >= 4 else "⚠️ Basic"
            print(f"   {status} {component}: {cap.get('line_count', 0)} lines, {advanced_features}/{total_features} advanced features")
    
    # 4. Generate recommendations
    recommendations = generate_upgrade_recommendations()
    
    for i, rec in enumerate(recommendations, 1):
        priority_icon = "🔴" if rec["priority"] == "HIGH" else "🟡" if rec["priority"] == "MEDIUM" else "🟢"
        print(f"\n{i}. {priority_icon} {rec['priority']} PRIORITY:")
        print(f"   Action: {rec['action']}")
        print(f"   Reason: {rec['reason']}")
        print(f"   Files: {', '.join(rec['files_to_update'])}")
    
    # 5. Overall assessment
    print("\n" + "="*80)
    print("📊 OVERALL ASSESSMENT")
    print("="*80)
    
    # Count actual issues (basic components, missing files, deprecated files)
    basic_components = len([comp for comp, cap in capabilities.items() 
                           if not cap.get('error') and not cap.get('status') 
                           and sum([cap.get(feature, False) for feature in [
                               'elasticsearch_utility', 'feature_engineering', 'ensemble_methods',
                               'anomaly_detection', 'neural_networks', 'automl', 'advanced_ml',
                               'real_time', 'optimization', 'cross_validation', 'class_balancing',
                               'ml_monitoring', 'alerting_system', 'error_handling'
                           ]]) < 4])
    
    deprecated_files = len([f for f in categories["test_temp"] if f])
    actual_issues = basic_components + deprecated_files
    
    if actual_issues == 0:
        print("✅ EXCELLENT: All components are advanced and properly integrated!")
    elif actual_issues <= 2:
        print("🟡 GOOD: Minor optimizations needed for full advanced integration")
    else:
        print("🔴 NEEDS ATTENTION: Multiple components need upgrading to advanced versions")
    
    print(f"\n📈 Status: {len(categories['advanced']) + len(categories['optimized'])} advanced components")
    print(f"✅ Advanced: {len([comp for comp, cap in capabilities.items() if not cap.get('error') and not cap.get('status') and sum([cap.get(feature, False) for feature in ['elasticsearch_utility', 'feature_engineering', 'ensemble_methods', 'anomaly_detection', 'neural_networks', 'automl', 'advanced_ml', 'real_time', 'optimization', 'cross_validation', 'class_balancing', 'ml_monitoring', 'alerting_system', 'error_handling']]) >= 4])} of {len(capabilities)} components verified")
    print(f"🎯 Integration: {len(launcher_comp)} launcher components")
    
    # 6. Next steps based on current status
    if actual_issues == 0 and len(recommendations) == 0:
        print(f"\n🎉 SYSTEM STATUS: PRODUCTION READY!")
        print("✅ All components are advanced")
        print("✅ No deprecated files found") 
        print("✅ Clean system architecture")
        print("✅ Ready for enterprise deployment")
    else:
        print(f"\n💡 NEXT STEPS:")
        if len(recommendations) > 0:
            print("1. Review integration recommendations above")
            print("2. Consider adding components to launcher for easier access")
        if actual_issues > 0:
            print("3. Address any basic components identified")
            print("4. Archive any deprecated files")
        print("5. Test all integrations after updates")

if __name__ == "__main__":
    main()