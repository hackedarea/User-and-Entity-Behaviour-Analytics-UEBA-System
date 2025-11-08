#!/usr/bin/env python3
"""
ML Performance Benchmarking & Monitoring System
Real-time performance tracking for optimized ML models
with automated performance alerts and trend analysis.

Author: UEBA System v2.0
Date: October 5, 2025
"""

import json
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
import joblib
import threading
import signal
import sys
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class MLPerformanceBenchmark:
    def __init__(self, es_url="http://localhost:9200"):
        self.es = Elasticsearch([es_url])
        self.running = True
        self.performance_data = []
        
        # Performance thresholds
        self.accuracy_threshold = 0.85
        self.response_time_threshold = 2.0  # seconds
        self.memory_threshold = 500  # MB
        
        # Load optimized models
        self.models = {}
        self.scaler = None
        self.feature_columns = []
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n🛑 Shutting down performance monitoring...")
        self.running = False
        
    def load_latest_models(self):
        """Load the latest optimized models"""
        print("📥 Loading latest optimized models...")
        
        models_dir = Path("ml_models")
        if not models_dir.exists():
            print("❌ Models directory not found")
            return False
            
        # Find latest timestamp
        model_files = list(models_dir.glob("optimized_*.joblib"))
        if not model_files:
            print("❌ No optimized models found")
            return False
            
        # Extract timestamps and find latest
        timestamps = []
        for file in model_files:
            try:
                # Extract timestamp from filename like "optimized_isolation_forest_20251005_203734.joblib"
                parts = file.stem.split('_')
                if len(parts) >= 4:
                    timestamp = f"{parts[-2]}_{parts[-1]}"
                    timestamps.append(timestamp)
            except:
                continue
                
        if not timestamps:
            print("❌ No valid timestamps found")
            return False
            
        latest_timestamp = max(timestamps)
        print(f"📅 Loading models with timestamp: {latest_timestamp}")
        
        # Load models
        try:
            iso_file = f"ml_models/optimized_isolation_forest_{latest_timestamp}.joblib"
            svm_file = f"ml_models/optimized_one_class_svm_{latest_timestamp}.joblib"
            lof_file = f"ml_models/optimized_lof_detector_{latest_timestamp}.joblib"
            scaler_file = f"ml_models/optimized_scaler_{latest_timestamp}.joblib"
            
            if all(Path(f).exists() for f in [iso_file, svm_file, lof_file, scaler_file]):
                self.models['isolation_forest'] = joblib.load(iso_file)
                self.models['one_class_svm'] = joblib.load(svm_file)
                self.models['lof_detector'] = joblib.load(lof_file)
                self.scaler = joblib.load(scaler_file)
                
                # Load optimization results for feature columns
                results_file = f"ml_models/optimization_results_{latest_timestamp}.json"
                if Path(results_file).exists():
                    with open(results_file, 'r') as f:
                        results = json.load(f)
                        self.feature_columns = results.get('feature_columns', [])
                        
                print(f"✅ Loaded {len(self.models)} optimized models")
                return True
            else:
                print("❌ Some model files missing")
                return False
                
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            return False
            
    def prepare_test_data(self, size=100):
        """Prepare test data for benchmarking"""
        query = {
            "query": {"match_all": {}},
            "size": size,
            "sort": [{"@timestamp": {"order": "desc"}}]
        }
        
        try:
            response = self.es.search(index="nginx-parsed-logs", body=query)
            hits = response['hits']['hits']
            
            if not hits:
                return None, None
                
            data = []
            for hit in hits:
                source = hit['_source']
                data.append({
                    'ip': source.get('ip', ''),
                    'method': source.get('method', 'GET'),
                    'url': source.get('url', '/'),
                    'status': source.get('status', 200),
                    'size': source.get('size', 0),
                    'user_agent': source.get('user_agent', ''),
                    'risk_score': source.get('risk_score', 0),
                    'response_time': source.get('response_time', 0),
                    'threat_detected': source.get('threat_detected', False)
                })
                
            df = pd.DataFrame(data)
            
            # Prepare features (same as in optimization)
            df['method_encoded'] = df['method'].map({
                'GET': 0, 'POST': 1, 'PUT': 2, 'DELETE': 3, 'HEAD': 4, 'OPTIONS': 5
            }).fillna(6)
            
            df['url_length'] = df['url'].str.len()
            df['has_script'] = df['url'].str.contains('<script>', case=False).astype(int)
            df['has_sql'] = df['url'].str.contains("'|--|union|select", case=False).astype(int)
            df['has_traversal'] = df['url'].str.contains("\.\./", case=False).astype(int)
            
            if self.feature_columns:
                X = df[self.feature_columns].fillna(0)
            else:
                feature_columns = [
                    'status', 'size', 'risk_score', 'response_time',
                    'method_encoded', 'url_length', 'has_script', 'has_sql', 'has_traversal'
                ]
                X = df[feature_columns].fillna(0)
                
            y = df['threat_detected'].astype(int)
            
            if self.scaler:
                X_scaled = self.scaler.transform(X)
            else:
                X_scaled = X.values
                
            return X_scaled, y
            
        except Exception as e:
            print(f"❌ Error preparing test data: {e}")
            return None, None
            
    def benchmark_model(self, model_name, model, X, y):
        """Benchmark individual model performance"""
        try:
            start_time = time.time()
            
            # Make predictions
            if hasattr(model, 'predict'):
                predictions = model.predict(X)
            else:
                predictions = model.fit_predict(X)
                
            predictions = (predictions == -1).astype(int)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Calculate metrics
            accuracy = np.mean(predictions == y) if len(y) > 0 else 0
            precision = np.sum((predictions == 1) & (y == 1)) / max(np.sum(predictions == 1), 1)
            recall = np.sum((predictions == 1) & (y == 1)) / max(np.sum(y == 1), 1)
            f1_score = 2 * (precision * recall) / max(precision + recall, 1)
            
            return {
                'model': model_name,
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1_score,
                'response_time': response_time,
                'predictions_count': len(predictions),
                'anomalies_detected': np.sum(predictions == 1),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ Error benchmarking {model_name}: {e}")
            return None
            
    def ensemble_benchmark(self, X, y):
        """Benchmark ensemble voting performance"""
        try:
            start_time = time.time()
            
            predictions = []
            for name, model in self.models.items():
                try:
                    pred = model.predict(X)
                    pred = (pred == -1).astype(int)
                    predictions.append(pred)
                except:
                    pred = model.fit_predict(X)
                    pred = (pred == -1).astype(int)
                    predictions.append(pred)
                    
            # Ensemble voting
            if predictions:
                ensemble_pred = np.array(predictions).mean(axis=0)
                ensemble_pred = (ensemble_pred > 0.5).astype(int)
            else:
                ensemble_pred = np.zeros(len(X))
                
            end_time = time.time()
            response_time = end_time - start_time
            
            # Calculate metrics
            accuracy = np.mean(ensemble_pred == y) if len(y) > 0 else 0
            precision = np.sum((ensemble_pred == 1) & (y == 1)) / max(np.sum(ensemble_pred == 1), 1)
            recall = np.sum((ensemble_pred == 1) & (y == 1)) / max(np.sum(y == 1), 1)
            f1_score = 2 * (precision * recall) / max(precision + recall, 1)
            
            return {
                'model': 'ensemble_voting',
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1_score,
                'response_time': response_time,
                'predictions_count': len(ensemble_pred),
                'anomalies_detected': np.sum(ensemble_pred == 1),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ Error in ensemble benchmark: {e}")
            return None
            
    def check_performance_alerts(self, results):
        """Check for performance degradation alerts"""
        alerts = []
        
        for result in results:
            if result:
                # Accuracy alert
                if result['accuracy'] < self.accuracy_threshold:
                    alerts.append({
                        'type': 'ACCURACY_LOW',
                        'model': result['model'],
                        'metric': 'accuracy',
                        'value': result['accuracy'],
                        'threshold': self.accuracy_threshold,
                        'severity': 'HIGH',
                        'message': f"ACCURACY_LOW: {result['model']} accuracy = {result['accuracy']:.3f}"
                    })
                    
                # Response time alert
                if result['response_time'] > self.response_time_threshold:
                    alerts.append({
                        'type': 'RESPONSE_TIME_HIGH',
                        'model': result['model'],
                        'metric': 'response_time',
                        'value': result['response_time'],
                        'threshold': self.response_time_threshold,
                        'severity': 'MEDIUM',
                        'message': f"RESPONSE_TIME_HIGH: {result['model']} response_time = {result['response_time']:.3f}s"
                    })
                    
        return alerts
        
    def log_performance_data(self, results, alerts):
        """Log performance data to Elasticsearch"""
        try:
            for result in results:
                if result:
                    doc = {
                        '@timestamp': result['timestamp'].isoformat(),
                        'performance_type': 'ml_benchmark',
                        'model_name': result['model'],
                        'accuracy': result['accuracy'],
                        'precision': result['precision'],
                        'recall': result['recall'],
                        'f1_score': result['f1_score'],
                        'response_time': result['response_time'],
                        'predictions_count': result['predictions_count'],
                        'anomalies_detected': result['anomalies_detected']
                    }
                    
                    self.es.index(index="ml-performance", body=doc)
                    
            # Log alerts
            for alert in alerts:
                alert_doc = {
                    '@timestamp': datetime.now().isoformat(),
                    'alert_type': 'ml_performance',
                    'severity': alert['severity'],
                    'model': alert['model'],
                    'metric': alert['metric'],
                    'value': alert['value'],
                    'threshold': alert['threshold'],
                    'message': alert['message']
                }
                
                self.es.index(index="ml-alerts", body=alert_doc)
                
        except Exception as e:
            print(f"❌ Error logging performance data: {e}")
            
    def run_benchmark_cycle(self):
        """Run one complete benchmark cycle"""
        print("\n🔄 Running ML Performance Benchmark Cycle...")
        
        # Prepare test data
        X, y = self.prepare_test_data(100)
        if X is None:
            print("❌ No test data available")
            return
            
        print(f"📊 Testing with {len(X)} samples")
        
        # Benchmark individual models
        results = []
        for name, model in self.models.items():
            result = self.benchmark_model(name, model, X, y)
            if result:
                results.append(result)
                print(f"✅ {name}: Accuracy={result['accuracy']:.3f}, "
                      f"Response={result['response_time']:.3f}s, "
                      f"Anomalies={result['anomalies_detected']}")
                
        # Benchmark ensemble
        ensemble_result = self.ensemble_benchmark(X, y)
        if ensemble_result:
            results.append(ensemble_result)
            print(f"🗳️ Ensemble: Accuracy={ensemble_result['accuracy']:.3f}, "
                  f"Response={ensemble_result['response_time']:.3f}s, "
                  f"Anomalies={ensemble_result['anomalies_detected']}")
            
        # Check for alerts
        alerts = self.check_performance_alerts(results)
        if alerts:
            print(f"🚨 {len(alerts)} performance alerts detected:")
            for alert in alerts:
                print(f"   {alert['severity']}: {alert['message']}")
        else:
            print("✅ All performance metrics within thresholds")
            
        # Log performance data
        self.log_performance_data(results, alerts)
        
        return results, alerts
        
    def continuous_monitoring(self, interval=300):  # 5 minutes
        """Run continuous performance monitoring"""
        print("🚀 STARTING ML PERFORMANCE MONITORING")
        print("="*50)
        print(f"⏱️ Benchmark interval: {interval} seconds")
        print(f"🎯 Accuracy threshold: {self.accuracy_threshold}")
        print(f"⚡ Response time threshold: {self.response_time_threshold}s")
        print("="*50)
        
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                print(f"\n📊 BENCHMARK CYCLE #{cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                results, alerts = self.run_benchmark_cycle()
                
                # Store performance data
                self.performance_data.extend(results)
                
                # Keep only last 100 cycles
                if len(self.performance_data) > 100:
                    self.performance_data = self.performance_data[-100:]
                    
                print(f"⏳ Next benchmark in {interval} seconds...")
                
                # Wait with interrupt checking
                for i in range(interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error in monitoring cycle: {e}")
                time.sleep(10)
                
        print("\n✅ Performance monitoring stopped")
        
    def generate_performance_report(self):
        """Generate performance summary report"""
        if not self.performance_data:
            print("No performance data available")
            return
            
        df = pd.DataFrame(self.performance_data)
        
        print("\n📈 PERFORMANCE SUMMARY REPORT")
        print("="*50)
        
        for model in df['model'].unique():
            model_data = df[df['model'] == model]
            
            print(f"\n🤖 {model.upper()}:")
            print(f"   Average Accuracy: {model_data['accuracy'].mean():.3f}")
            print(f"   Average Response Time: {model_data['response_time'].mean():.3f}s")
            print(f"   Total Predictions: {model_data['predictions_count'].sum()}")
            print(f"   Total Anomalies: {model_data['anomalies_detected'].sum()}")
            
        print("="*50)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ML Performance Benchmark Monitor")
    parser.add_argument("--interval", type=int, default=300, 
                       help="Benchmark interval in seconds (default: 300)")
    parser.add_argument("--single", action="store_true", 
                       help="Run single benchmark cycle instead of continuous monitoring")
    
    args = parser.parse_args()
    
    monitor = MLPerformanceBenchmark()
    
    if not monitor.load_latest_models():
        print("❌ Cannot load optimized models. Run enhanced_ml_optimizer.py first.")
        sys.exit(1)
        
    if args.single:
        monitor.run_benchmark_cycle()
        monitor.generate_performance_report()
    else:
        try:
            monitor.continuous_monitoring(args.interval)
        finally:
            monitor.generate_performance_report()