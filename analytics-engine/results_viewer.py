#!/usr/bin/env python3
"""
UEBA Results Viewer - Clean & Professional Display
"""

import os
import json
import glob
from datetime import datetime
from pathlib import Path

def format_timestamp(timestamp_str):
    """Format timestamp for display"""
    try:
        dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str

def display_results():
    """Display UEBA results in a clean format"""
    print("\n" + "="*80)
    print("📊 UEBA SYSTEM RESULTS VIEWER")
    print("="*80)
    
    results_dir = Path("results")
    if not results_dir.exists():
        print("❌ No results directory found")
        return
    
    # Find all result files
    result_files = list(results_dir.glob("*.json"))
    if not result_files:
        print("❌ No result files found in results directory")
        return
    
    # Sort by modification time (newest first)
    result_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    print(f"\n🔍 Found {len(result_files)} result file(s)")
    print("-" * 80)
    
    for i, file_path in enumerate(result_files, 1):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Extract timestamp from filename
            filename = file_path.stem
            timestamp_part = filename.split('_')[-2] + '_' + filename.split('_')[-1]
            formatted_time = format_timestamp(timestamp_part)
            
            print(f"\n📄 Result #{i}: {file_path.name}")
            print(f"⏰ Generated: {formatted_time}")
            print(f"📁 Size: {file_path.stat().st_size:,} bytes")
            
            # Display key metrics
            if 'summary' in data:
                summary = data['summary']
                print(f"📊 Events Processed: {summary.get('total_events', 'N/A')}")
                print(f"⚡ Processing Time: {summary.get('processing_time', 'N/A')}")
                print(f"🎯 ML Models: {summary.get('models_used', 'N/A')}")
                
                if 'alerts' in summary:
                    alerts = summary['alerts']
                    print(f"🚨 Total Alerts: {alerts.get('total', 0)}")
                    print(f"   📈 High: {alerts.get('high', 0)}")
                    print(f"   📊 Medium: {alerts.get('medium', 0)}")
                    print(f"   📉 Low: {alerts.get('low', 0)}")
            
            # Display model performance if available
            if 'model_performance' in data:
                perf = data['model_performance']
                print("🤖 Model Performance:")
                for model, accuracy in perf.items():
                    if isinstance(accuracy, (int, float)):
                        print(f"   • {model}: {accuracy:.1f}%")
                    else:
                        print(f"   • {model}: {accuracy}")
            
            print("-" * 40)
            
        except Exception as e:
            print(f"❌ Error reading {file_path.name}: {e}")
    
    print(f"\n💡 To view detailed results, check files in: {results_dir.absolute()}")
    print("🌐 Or access Grafana dashboards at: http://localhost:3000")

def main():
    """Main function"""
    try:
        display_results()
    except KeyboardInterrupt:
        print("\n👋 Results viewer closed by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()