#!/usr/bin/env python3
"""
UEBA Advanced ML Anomaly Detection Engine
Implements sophisticated machine learning algorithms for behavioral anomaly detection
including Isolation Forest, One-Class SVM, Local Outlier Factor, and DBSCAN clustering.

Prerequisites:
    pip install scikit-learn elasticsearch pandas numpy matplotlib seaborn

Author: UEBA System  
Date: October 4, 2025
Version: 2.0 - Advanced ML Implementation
"""

import pandas as pd
import numpy as np
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta
import json
import sys
import warnings
from typing import Dict, List, Optional, Tuple
import argparse

# Scikit-learn imports for advanced ML
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import cross_val_score
import joblib

# Data visualization
import matplotlib.pyplot as plt
import seaborn as sns

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

class AdvancedMLAnomalyDetector:
    """
    Advanced Machine Learning Anomaly Detection Engine
    Implements multiple ML algorithms for comprehensive threat detection
    """
    
    def __init__(self, elasticsearch_url: str = "http://localhost:9200", 
                 index_name: str = "nginx-parsed-logs"):
        """
        Initialize the Advanced ML Anomaly Detector
        
        Args:
            elasticsearch_url (str): URL of Elasticsearch instance
            index_name (str): Name of the index containing parsed logs
        """
        self.es_url = elasticsearch_url
        self.index_name = index_name
        self.scaler = StandardScaler()
        self.label_encoders = {}
        
        # ML Models
        self.isolation_forest = None
        self.one_class_svm = None
        self.lof_detector = None
        self.dbscan_clusterer = None
        
        # Data storage
        self.df = None
        self.feature_matrix = None
        self.anomaly_scores = {}
        
        print(f"🚀 Advanced ML Detector initialized for index: {self.index_name}")
    
    def load_and_prepare_data(self, max_size: int = 1000) -> bool:
        """
        Load data from Elasticsearch and prepare for ML analysis
        
        Args:
            max_size (int): Maximum number of records to process
            
        Returns:
            bool: Success status
        """
        try:
            from elasticsearch_utility import get_elasticsearch_data
            
            print(f"🔍 Loading data from Elasticsearch index: {self.index_name}")
            
            # Get data using the utility (with fallback to synthetic data)
            records = get_elasticsearch_data(max_size, fallback_to_synthetic=True)
            
            if not records:
                print("❌ No data available")
                return False
            
            print(f"📊 Found {len(records)} records")
            
            # Convert to DataFrame
            self.df = pd.DataFrame(records)
            print(f"✅ Created DataFrame with shape: {self.df.shape}")
            
            # Prepare features for ML
            self._engineer_advanced_features()
            self._prepare_feature_matrix()
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading data: {str(e)}")
            return False
    
    def _engineer_advanced_features(self):
        """Engineer advanced features for ML algorithms"""
        print("🔧 Engineering advanced ML features...")
        
        # Ensure timestamp is datetime
        if '@timestamp' in self.df.columns:
            self.df['@timestamp'] = pd.to_datetime(self.df['@timestamp'])
        
        # Advanced temporal features
        if '@timestamp' in self.df.columns:
            self.df['hour_of_day'] = self.df['@timestamp'].dt.hour
            self.df['day_of_week'] = self.df['@timestamp'].dt.dayofweek
            self.df['is_weekend'] = self.df['day_of_week'].isin([5, 6]).astype(int)
            self.df['is_business_hours'] = ((self.df['hour_of_day'] >= 9) & 
                                          (self.df['hour_of_day'] <= 17)).astype(int)
            self.df['is_night_time'] = ((self.df['hour_of_day'] >= 22) | 
                                       (self.df['hour_of_day'] <= 6)).astype(int)
        
        # Request frequency features
        if 'client_ip' in self.df.columns:
            ip_counts = self.df['client_ip'].value_counts()
            self.df['ip_request_frequency'] = self.df['client_ip'].map(ip_counts)
            self.df['is_high_volume_ip'] = (self.df['ip_request_frequency'] > 
                                          self.df['ip_request_frequency'].quantile(0.95)).astype(int)
        
        # URL path analysis
        if 'url_path' in self.df.columns:
            path_counts = self.df['url_path'].value_counts()
            self.df['path_popularity'] = self.df['url_path'].map(path_counts)
            self.df['is_rare_path'] = (self.df['path_popularity'] <= 2).astype(int)
            
            # URL length and complexity
            self.df['url_length'] = self.df['url_path'].str.len().fillna(0)
            self.df['url_depth'] = self.df['url_path'].str.count('/').fillna(0)
            self.df['has_query_params'] = self.df['url_path'].str.contains('\\?', na=False).astype(int)
        
        # Status code analysis
        if 'status_code' in self.df.columns:
            self.df['status_code'] = pd.to_numeric(self.df['status_code'], errors='coerce').fillna(0)
            self.df['is_error_4xx'] = ((self.df['status_code'] >= 400) & 
                                     (self.df['status_code'] < 500)).astype(int)
            self.df['is_error_5xx'] = (self.df['status_code'] >= 500).astype(int)
            self.df['is_success'] = ((self.df['status_code'] >= 200) & 
                                   (self.df['status_code'] < 300)).astype(int)
        
        # User agent analysis
        if 'user_agent' in self.df.columns:
            self.df['user_agent'] = self.df['user_agent'].fillna('unknown')
            self.df['is_bot'] = self.df['user_agent'].str.contains(
                'bot|crawler|spider|scraper', case=False, na=False).astype(int)
            self.df['is_curl'] = self.df['user_agent'].str.contains('curl', case=False, na=False).astype(int)
            self.df['is_mobile'] = self.df['user_agent'].str.contains(
                'mobile|android|iphone', case=False, na=False).astype(int)
            self.df['user_agent_length'] = self.df['user_agent'].str.len()
        
        # Response size analysis
        if 'response_size' in self.df.columns:
            self.df['response_size'] = pd.to_numeric(self.df['response_size'], errors='coerce').fillna(0)
            self.df['is_large_response'] = (self.df['response_size'] > 
                                          self.df['response_size'].quantile(0.95)).astype(int)
            self.df['is_empty_response'] = (self.df['response_size'] == 0).astype(int)
        
        # HTTP method analysis
        if 'method' in self.df.columns:
            self.df['is_get'] = (self.df['method'] == 'GET').astype(int)
            self.df['is_post'] = (self.df['method'] == 'POST').astype(int)
            self.df['is_suspicious_method'] = self.df['method'].isin(
                ['PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']).astype(int)
        
        # Security indicators
        if 'url_path' in self.df.columns:
            security_patterns = [
                'admin', 'login', 'wp-admin', 'phpmyadmin', 'config', 
                'backup', '.env', 'passwd', 'shadow', '../', 'script',
                'union', 'select', 'drop', 'insert', 'update', 'delete'
            ]
            
            for pattern in security_patterns:
                col_name = f'has_{pattern.replace(".", "_").replace("/", "_")}'
                self.df[col_name] = self.df['url_path'].str.contains(
                    pattern, case=False, na=False).astype(int)
        
        print(f"✅ Feature engineering complete. DataFrame shape: {self.df.shape}")
    
    def _prepare_feature_matrix(self):
        """Prepare numerical feature matrix for ML algorithms"""
        print("🎯 Preparing feature matrix for ML algorithms...")
        
        # Select numerical and engineered features
        feature_columns = []
        
        # Numerical features
        numerical_cols = ['hour_of_day', 'day_of_week', 'is_weekend', 'is_business_hours', 
                         'is_night_time', 'ip_request_frequency', 'is_high_volume_ip',
                         'path_popularity', 'is_rare_path', 'url_length', 'url_depth',
                         'has_query_params', 'status_code', 'is_error_4xx', 'is_error_5xx',
                         'is_success', 'is_bot', 'is_curl', 'is_mobile', 'user_agent_length',
                         'response_size', 'is_large_response', 'is_empty_response',
                         'is_get', 'is_post', 'is_suspicious_method']
        
        # Add security indicator features
        security_features = [col for col in self.df.columns if col.startswith('has_')]
        feature_columns.extend(numerical_cols + security_features)
        
        # Filter existing columns
        existing_features = [col for col in feature_columns if col in self.df.columns]
        
        # Create feature matrix
        self.feature_matrix = self.df[existing_features].fillna(0)
        
        # Handle categorical features if needed
        categorical_cols = ['method', 'log_type']
        for col in categorical_cols:
            if col in self.df.columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    encoded = self.label_encoders[col].fit_transform(self.df[col].fillna('unknown'))
                else:
                    encoded = self.label_encoders[col].transform(self.df[col].fillna('unknown'))
                self.feature_matrix[f'{col}_encoded'] = encoded
        
        # Scale features
        self.feature_matrix = pd.DataFrame(
            self.scaler.fit_transform(self.feature_matrix),
            columns=self.feature_matrix.columns,
            index=self.feature_matrix.index
        )
        
        print(f"✅ Feature matrix prepared with {self.feature_matrix.shape[1]} features")
        print(f"📊 Features: {list(self.feature_matrix.columns)}")
    
    def train_isolation_forest(self, contamination: float = 0.1, random_state: int = 42) -> Dict:
        """
        Train Isolation Forest for anomaly detection
        
        Args:
            contamination (float): Expected proportion of anomalies
            random_state (int): Random seed for reproducibility
            
        Returns:
            Dict: Training results and metrics
        """
        print("\n🌲 Training Isolation Forest Model...")
        
        self.isolation_forest = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100
        )
        
        # Train model
        self.isolation_forest.fit(self.feature_matrix)
        
        # Predict anomalies
        predictions = self.isolation_forest.predict(self.feature_matrix)
        scores = self.isolation_forest.decision_function(self.feature_matrix)
        
        # Convert predictions (-1 for anomaly, 1 for normal) to 0/1
        anomaly_labels = (predictions == -1).astype(int)
        
        # Store results
        self.anomaly_scores['isolation_forest'] = {
            'predictions': anomaly_labels,
            'scores': scores,
            'model': self.isolation_forest
        }
        
        # Calculate metrics
        anomaly_count = np.sum(anomaly_labels)
        anomaly_percentage = (anomaly_count / len(anomaly_labels)) * 100
        
        results = {
            'algorithm': 'Isolation Forest',
            'total_samples': len(self.feature_matrix),
            'anomalies_detected': anomaly_count,
            'anomaly_percentage': anomaly_percentage,
            'contamination_threshold': contamination,
            'avg_anomaly_score': np.mean(scores[anomaly_labels == 1])
        }
        
        print(f"✅ Isolation Forest Results:")
        print(f"   📊 Total samples: {results['total_samples']}")
        print(f"   🚨 Anomalies detected: {results['anomalies_detected']} ({results['anomaly_percentage']:.1f}%)")
        print(f"   📈 Average anomaly score: {results['avg_anomaly_score']:.3f}")
        
        return results
    
    def train_one_class_svm(self, nu: float = 0.1, gamma: str = 'scale') -> Dict:
        """
        Train One-Class SVM for novelty detection
        
        Args:
            nu (float): Upper bound on fraction of training errors
            gamma (str): Kernel coefficient
            
        Returns:
            Dict: Training results and metrics
        """
        print("\n🎯 Training One-Class SVM Model...")
        
        self.one_class_svm = OneClassSVM(
            nu=nu,
            gamma=gamma,
            kernel='rbf'
        )
        
        # Train model
        self.one_class_svm.fit(self.feature_matrix)
        
        # Predict anomalies
        predictions = self.one_class_svm.predict(self.feature_matrix)
        scores = self.one_class_svm.decision_function(self.feature_matrix)
        
        # Convert predictions
        anomaly_labels = (predictions == -1).astype(int)
        
        # Store results
        self.anomaly_scores['one_class_svm'] = {
            'predictions': anomaly_labels,
            'scores': scores,
            'model': self.one_class_svm
        }
        
        # Calculate metrics
        anomaly_count = np.sum(anomaly_labels)
        anomaly_percentage = (anomaly_count / len(anomaly_labels)) * 100
        
        results = {
            'algorithm': 'One-Class SVM',
            'total_samples': len(self.feature_matrix),
            'anomalies_detected': anomaly_count,
            'anomaly_percentage': anomaly_percentage,
            'nu_parameter': nu,
            'avg_anomaly_score': np.mean(scores[anomaly_labels == 1]) if anomaly_count > 0 else 0
        }
        
        print(f"✅ One-Class SVM Results:")
        print(f"   📊 Total samples: {results['total_samples']}")
        print(f"   🚨 Anomalies detected: {results['anomalies_detected']} ({results['anomaly_percentage']:.1f}%)")
        print(f"   📈 Average anomaly score: {results['avg_anomaly_score']:.3f}")
        
        return results
    
    def train_local_outlier_factor(self, n_neighbors: int = 20, contamination: float = 0.1) -> Dict:
        """
        Train Local Outlier Factor for density-based anomaly detection
        
        Args:
            n_neighbors (int): Number of neighbors to use
            contamination (float): Expected proportion of anomalies
            
        Returns:
            Dict: Training results and metrics
        """
        print("\n🎯 Training Local Outlier Factor Model...")
        
        self.lof_detector = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=contamination,
            novelty=False
        )
        
        # Train and predict in one step (LOF doesn't separate fit/predict)
        predictions = self.lof_detector.fit_predict(self.feature_matrix)
        scores = self.lof_detector.negative_outlier_factor_
        
        # Convert predictions
        anomaly_labels = (predictions == -1).astype(int)
        
        # Store results
        self.anomaly_scores['local_outlier_factor'] = {
            'predictions': anomaly_labels,
            'scores': scores,
            'model': self.lof_detector
        }
        
        # Calculate metrics
        anomaly_count = np.sum(anomaly_labels)
        anomaly_percentage = (anomaly_count / len(anomaly_labels)) * 100
        
        results = {
            'algorithm': 'Local Outlier Factor',
            'total_samples': len(self.feature_matrix),
            'anomalies_detected': anomaly_count,
            'anomaly_percentage': anomaly_percentage,
            'n_neighbors': n_neighbors,
            'avg_outlier_score': np.mean(scores[anomaly_labels == 1]) if anomaly_count > 0 else 0
        }
        
        print(f"✅ Local Outlier Factor Results:")
        print(f"   📊 Total samples: {results['total_samples']}")
        print(f"   🚨 Anomalies detected: {results['anomalies_detected']} ({results['anomaly_percentage']:.1f}%)")
        print(f"   📈 Average outlier score: {results['avg_outlier_score']:.3f}")
        
        return results
    
    def perform_dbscan_clustering(self, eps: float = 0.5, min_samples: int = 5) -> Dict:
        """
        Perform DBSCAN clustering to identify behavioral patterns
        
        Args:
            eps (float): Maximum distance between samples in a cluster
            min_samples (int): Minimum samples in a cluster
            
        Returns:
            Dict: Clustering results and metrics
        """
        print("\n🔍 Performing DBSCAN Clustering Analysis...")
        
        self.dbscan_clusterer = DBSCAN(eps=eps, min_samples=min_samples)
        
        # Perform clustering
        cluster_labels = self.dbscan_clusterer.fit_predict(self.feature_matrix)
        
        # Identify noise points (cluster label -1) as potential anomalies
        anomaly_labels = (cluster_labels == -1).astype(int)
        
        # Store results
        self.anomaly_scores['dbscan'] = {
            'predictions': anomaly_labels,
            'cluster_labels': cluster_labels,
            'model': self.dbscan_clusterer
        }
        
        # Calculate metrics
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        n_noise = list(cluster_labels).count(-1)
        
        results = {
            'algorithm': 'DBSCAN Clustering',
            'total_samples': len(self.feature_matrix),
            'n_clusters': n_clusters,
            'noise_points': n_noise,
            'noise_percentage': (n_noise / len(cluster_labels)) * 100,
            'eps_parameter': eps,
            'min_samples': min_samples
        }
        
        print(f"✅ DBSCAN Clustering Results:")
        print(f"   📊 Total samples: {results['total_samples']}")
        print(f"   🎯 Clusters found: {results['n_clusters']}")
        print(f"   🚨 Noise points (anomalies): {results['noise_points']} ({results['noise_percentage']:.1f}%)")
        
        return results
    
    def create_ensemble_score(self, weights: Optional[Dict[str, float]] = None) -> np.ndarray:
        """
        Create ensemble anomaly score from multiple algorithms
        
        Args:
            weights (Dict): Weights for each algorithm
            
        Returns:
            np.ndarray: Ensemble anomaly scores
        """
        print("\n🎭 Creating Ensemble Anomaly Scores...")
        
        if weights is None:
            weights = {
                'isolation_forest': 0.3,
                'one_class_svm': 0.3,
                'local_outlier_factor': 0.25,
                'dbscan': 0.15
            }
        
        ensemble_scores = np.zeros(len(self.feature_matrix))
        
        for algorithm, weight in weights.items():
            if algorithm in self.anomaly_scores:
                if algorithm == 'dbscan':
                    # For DBSCAN, use binary anomaly predictions
                    scores = self.anomaly_scores[algorithm]['predictions']
                else:
                    # Normalize scores to 0-1 range
                    raw_scores = self.anomaly_scores[algorithm]['scores']
                    if algorithm == 'local_outlier_factor':
                        # LOF scores are negative, convert to positive
                        scores = 1 / (1 + np.exp(-raw_scores))
                    else:
                        # Normalize using min-max scaling
                        scores = (raw_scores - raw_scores.min()) / (raw_scores.max() - raw_scores.min())
                
                ensemble_scores += weight * scores
        
        # Store ensemble results
        ensemble_anomalies = (ensemble_scores > np.percentile(ensemble_scores, 90)).astype(int)
        
        self.anomaly_scores['ensemble'] = {
            'scores': ensemble_scores,
            'predictions': ensemble_anomalies
        }
        
        anomaly_count = np.sum(ensemble_anomalies)
        print(f"✅ Ensemble Analysis Complete:")
        print(f"   🎯 Ensemble anomalies detected: {anomaly_count} ({(anomaly_count/len(ensemble_scores))*100:.1f}%)")
        print(f"   📈 Average ensemble score: {np.mean(ensemble_scores):.3f}")
        
        return ensemble_scores
    
    def generate_detailed_report(self) -> str:
        """Generate comprehensive anomaly detection report"""
        print("\n📊 Generating Detailed Analysis Report...")
        
        report = []
        report.append("="*80)
        report.append("🤖 UEBA ADVANCED ML ANOMALY DETECTION REPORT")
        report.append("="*80)
        report.append(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"📊 Dataset Size: {len(self.feature_matrix)} records")
        report.append(f"🎯 Features Used: {self.feature_matrix.shape[1]} features")
        report.append("")
        
        # Algorithm results
        for algorithm, results in self.anomaly_scores.items():
            if algorithm == 'ensemble':
                continue
                
            predictions = results['predictions']
            anomaly_count = np.sum(predictions)
            anomaly_percentage = (anomaly_count / len(predictions)) * 100
            
            report.append(f"🔍 {algorithm.upper().replace('_', ' ')} ANALYSIS:")
            report.append(f"   • Anomalies Detected: {anomaly_count} ({anomaly_percentage:.1f}%)")
            
            if 'scores' in results:
                avg_score = np.mean(results['scores'])
                report.append(f"   • Average Score: {avg_score:.3f}")
            
            # Identify top anomalies
            if anomaly_count > 0:
                anomaly_indices = np.where(predictions == 1)[0]
                top_anomalies = anomaly_indices[:min(5, len(anomaly_indices))]
                
                report.append(f"   • Top Anomalous Records:")
                for idx in top_anomalies:
                    if idx < len(self.df):
                        row = self.df.iloc[idx]
                        ip = row.get('client_ip', 'N/A')
                        path = row.get('url_path', 'N/A')
                        status = row.get('status_code', 'N/A')
                        report.append(f"     - Record {idx}: IP={ip}, Path={path}, Status={status}")
            
            report.append("")
        
        # Ensemble results
        if 'ensemble' in self.anomaly_scores:
            ensemble_results = self.anomaly_scores['ensemble']
            ensemble_anomalies = np.sum(ensemble_results['predictions'])
            ensemble_percentage = (ensemble_anomalies / len(ensemble_results['predictions'])) * 100
            
            report.append("🎭 ENSEMBLE ANALYSIS:")
            report.append(f"   • Combined Anomalies: {ensemble_anomalies} ({ensemble_percentage:.1f}%)")
            report.append(f"   • Average Ensemble Score: {np.mean(ensemble_results['scores']):.3f}")
            report.append("")
        
        # Security insights
        report.append("🛡️ SECURITY INSIGHTS:")
        
        # High-risk IPs
        if 'client_ip' in self.df.columns:
            ip_anomaly_counts = {}
            for algorithm in ['isolation_forest', 'one_class_svm', 'local_outlier_factor']:
                if algorithm in self.anomaly_scores:
                    anomaly_indices = np.where(self.anomaly_scores[algorithm]['predictions'] == 1)[0]
                    for idx in anomaly_indices:
                        if idx < len(self.df):
                            ip = self.df.iloc[idx]['client_ip']
                            ip_anomaly_counts[ip] = ip_anomaly_counts.get(ip, 0) + 1
            
            if ip_anomaly_counts:
                sorted_ips = sorted(ip_anomaly_counts.items(), key=lambda x: x[1], reverse=True)
                report.append("   • High-Risk IP Addresses:")
                for ip, count in sorted_ips[:5]:
                    report.append(f"     - {ip}: {count} anomaly detections")
        
        # Attack patterns
        if 'url_path' in self.df.columns:
            attack_patterns = ['admin', 'login', 'config', 'passwd', 'union', 'select']
            for pattern in attack_patterns:
                col_name = f'has_{pattern}'
                if col_name in self.df.columns:
                    pattern_count = self.df[col_name].sum()
                    if pattern_count > 0:
                        report.append(f"   • '{pattern}' pattern detected: {pattern_count} times")
        
        report.append("")
        report.append("💡 RECOMMENDATIONS:")
        report.append("   • Monitor high-risk IPs for continued suspicious activity")
        report.append("   • Implement rate limiting for IPs with high anomaly scores")
        report.append("   • Review and block access to sensitive endpoints")
        report.append("   • Consider implementing automated response mechanisms")
        report.append("")
        report.append("="*80)
        
        report_text = "\n".join(report)
        print(report_text)
        
        return report_text
    
    def save_models(self, model_dir: str = "ml_models"):
        """Save trained models to disk"""
        import os
        
        os.makedirs(model_dir, exist_ok=True)
        
        models_to_save = {
            'isolation_forest': self.isolation_forest,
            'one_class_svm': self.one_class_svm,
            'lof_detector': self.lof_detector,
            'dbscan_clusterer': self.dbscan_clusterer,
            'scaler': self.scaler
        }
        
        for name, model in models_to_save.items():
            if model is not None:
                filepath = os.path.join(model_dir, f"{name}_model.joblib")
                joblib.dump(model, filepath)
                print(f"✅ Saved {name} to {filepath}")
        
        # Save label encoders
        if self.label_encoders:
            filepath = os.path.join(model_dir, "label_encoders.joblib")
            joblib.dump(self.label_encoders, filepath)
            print(f"✅ Saved label encoders to {filepath}")
    
    def run_complete_analysis(self, max_size: int = 1000) -> Dict:
        """
        Run complete ML anomaly detection analysis
        
        Args:
            max_size (int): Maximum records to analyze
            
        Returns:
            Dict: Complete analysis results
        """
        print("🚀 Starting Complete Advanced ML Anomaly Detection Analysis")
        print("="*80)
        
        # Load and prepare data
        if not self.load_and_prepare_data(max_size):
            return {"error": "Failed to load data"}
        
        # Train all algorithms
        results = {}
        
        try:
            results['isolation_forest'] = self.train_isolation_forest()
            results['one_class_svm'] = self.train_one_class_svm()
            results['local_outlier_factor'] = self.train_local_outlier_factor()
            results['dbscan'] = self.perform_dbscan_clustering()
            
            # Create ensemble
            ensemble_scores = self.create_ensemble_score()
            
            # Generate report
            report = self.generate_detailed_report()
            
            # Save models
            self.save_models()
            
            results['ensemble_scores'] = ensemble_scores
            results['detailed_report'] = report
            results['analysis_complete'] = True
            
        except Exception as e:
            print(f"❌ Error during analysis: {str(e)}")
            results['error'] = str(e)
        
        return results


def main():
    """Main function to run advanced ML anomaly detection"""
    parser = argparse.ArgumentParser(description='UEBA Advanced ML Anomaly Detection Engine')
    parser.add_argument('--size', type=int, default=1000, 
                       help='Maximum number of records to analyze (default: 1000)')
    parser.add_argument('--contamination', type=float, default=0.1,
                       help='Expected contamination rate for anomaly detection (default: 0.1)')
    parser.add_argument('--save-models', action='store_true',
                       help='Save trained models to disk')
    
    args = parser.parse_args()
    
    # Initialize ML anomaly detector
    detector = AdvancedMLAnomalyDetector()
    
    # Run complete analysis
    results = detector.run_complete_analysis(max_size=args.size)
    
    if 'error' in results:
        print(f"❌ Analysis failed: {results['error']}")
        sys.exit(1)
    
    print("\n🎉 Advanced ML Anomaly Detection Analysis Complete!")
    print("💾 Models saved to 'ml_models/' directory")
    print("📊 Check the detailed report above for security insights")
    
    return results


if __name__ == "__main__":
    main()