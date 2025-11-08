#!/usr/bin/env python3
"""
UEBA Real-Time ML Inference Engine
Provides real-time anomaly scoring for new log entries using pre-trained ML models

Prerequisites:
    - Trained models from advanced_ml_detector.py
    - Active Elasticsearch instance with incoming logs

Author: UEBA System
Date: October 4, 2025
Version: 2.0 - Real-time ML Inference
"""

import pandas as pd
import numpy as np
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta
import json
import time
import sys
import os
import warnings
from typing import Dict, List, Optional
import joblib
import argparse

# Suppress warnings
warnings.filterwarnings('ignore')

class RealTimeMLInference:
    """
    Real-time ML inference engine for continuous anomaly detection using optimized models
    """
    
    def __init__(self, model_dir: str = "ml_models", 
                 elasticsearch_url: str = "http://localhost:9200",
                 index_name: str = "nginx-parsed-logs"):
        """
        Initialize real-time ML inference engine with optimized models
        
        Args:
            model_dir (str): Directory containing trained models
            elasticsearch_url (str): Elasticsearch URL
            index_name (str): Index name for parsed logs
        """
        self.model_dir = model_dir
        self.es_url = elasticsearch_url
        self.index_name = index_name
        self.es_client = None
        self.optimized_models = {}
        self.optimized_scaler = None
        self.feature_columns = []
        
        # ML Models
        self.models = {}
        self.scaler = None
        self.label_encoders = {}
        
        # Tracking
        self.last_processed_timestamp = None
        self.anomaly_threshold = 0.7  # Ensemble score threshold
        
        # Initialize
        self._connect_to_elasticsearch()
        self._load_models()
    
    def _connect_to_elasticsearch(self) -> bool:
        """Connect to Elasticsearch"""
        try:
            self.es_client = Elasticsearch([self.es_url])
            if self.es_client.ping():
                print(f"✅ Connected to Elasticsearch at {self.es_url}")
                return True
            else:
                print(f"❌ Failed to connect to Elasticsearch")
                return False
        except Exception as e:
            print(f"❌ Elasticsearch connection error: {str(e)}")
            return False
    
    def _load_models(self) -> bool:
        """Load optimized ML models"""
        try:
            print(f"🔍 Loading optimized models from {self.model_dir}/")
            
            # Check if model directory exists
            if not os.path.exists(self.model_dir):
                print(f"❌ Model directory {self.model_dir} not found!")
                print("💡 Run enhanced_ml_optimizer.py first to create optimized models")
                return False
            
            # Find latest optimized models
            from pathlib import Path
            model_files = list(Path(self.model_dir).glob("optimized_*.joblib"))
            
            if not model_files:
                print("❌ No optimized models found!")
                print("💡 Run enhanced_ml_optimizer.py first to create optimized models")
                return False
            
            # Extract timestamps and find latest
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
                print("❌ No valid model timestamps found")
                return False
                
            latest_timestamp = max(timestamps)
            print(f"📅 Loading models with timestamp: {latest_timestamp}")
            
            # Load optimized models
            model_files = {
                'isolation_forest': f'optimized_isolation_forest_{latest_timestamp}.joblib',
                'one_class_svm': f'optimized_one_class_svm_{latest_timestamp}.joblib',
                'lof_detector': f'optimized_lof_detector_{latest_timestamp}.joblib',
                'scaler': f'optimized_scaler_{latest_timestamp}.joblib'
            }
            
            for model_name, filename in model_files.items():
                filepath = os.path.join(self.model_dir, filename)
                if os.path.exists(filepath):
                    if model_name == 'scaler':
                        self.optimized_scaler = joblib.load(filepath)
                        print(f"✅ Loaded optimized {model_name}")
                    else:
                        self.optimized_models[model_name] = joblib.load(filepath)
                        print(f"✅ Loaded optimized {model_name}")
                else:
                    print(f"⚠️  Optimized model file not found: {filepath}")
            
            # Load optimization results for feature columns
            results_file = f"{self.model_dir}/optimization_results_{latest_timestamp}.json"
            if os.path.exists(results_file):
                with open(results_file, 'r') as f:
                    results = json.load(f)
                    self.feature_columns = results.get('feature_columns', [])
                    print(f"✅ Loaded feature configuration: {len(self.feature_columns)} features")
            
            if not self.optimized_models:
                print("❌ No optimized models loaded!")
            print(f"🎯 Successfully loaded {len(self.optimized_models)} optimized models")
            return True
            
        except Exception as e:
            print(f"❌ Error loading optimized models: {str(e)}")
            return False
    
    def _engineer_features_single_record(self, record: Dict) -> pd.DataFrame:
        """Engineer features for a single log record using optimized feature set"""
        # Convert to DataFrame for consistent processing
        df = pd.DataFrame([record])
        
        # Engineer the same features as in optimization (matching enhanced_ml_optimizer.py)
        # Method encoding
        df['method_encoded'] = df.get('method', 'GET').map({
            'GET': 0, 'POST': 1, 'PUT': 2, 'DELETE': 3, 'HEAD': 4, 'OPTIONS': 5
        }).fillna(6)
        
        # URL analysis features
        url_col = 'url' if 'url' in df.columns else 'url_path'
        if url_col in df.columns:
            df['url_length'] = df[url_col].str.len().fillna(0)
            df['has_script'] = df[url_col].str.contains('<script>', case=False, na=False).astype(int)
            df['has_sql'] = df[url_col].str.contains("'|--|union|select", case=False, na=False).astype(int)
            df['has_traversal'] = df[url_col].str.contains("\.\./", case=False, na=False).astype(int)
        else:
            df['url_length'] = 0
            df['has_script'] = 0
            df['has_sql'] = 0
            df['has_traversal'] = 0
        
        # Ensure all required columns exist with defaults
        required_columns = ['status', 'size', 'risk_score', 'response_time']
        for col in required_columns:
            if col not in df.columns:
                df[col] = 0
        
        # Select optimized feature columns
        if self.feature_columns:
            feature_df = df[self.feature_columns].fillna(0)
        else:
            # Fallback to default feature set
            feature_columns = [
                'status', 'size', 'risk_score', 'response_time',
                'method_encoded', 'url_length', 'has_script', 'has_sql', 'has_traversal'
            ]
            feature_df = df[feature_columns].fillna(0)
        
        return feature_df
    
    def _prepare_feature_vector(self, record: Dict) -> np.ndarray:
        """Prepare feature vector for optimized ML inference"""
        # Engineer features using optimized feature set
        df = self._engineer_features_single_record(record)
        
        # Scale features using optimized scaler
        if self.optimized_scaler:
            feature_vector = self.optimized_scaler.transform(df)
        else:
            feature_vector = df.values
            
        return feature_vector
    
    def score_record(self, record: Dict) -> Dict:
        """
        Score a single record for anomalies using optimized models
        
        Args:
            record (Dict): Log record to score
            
        Returns:
            Dict: Anomaly scores and predictions
        """
        try:
            # Prepare features
            feature_vector = self._prepare_feature_vector(record)
            
            # Get predictions from each optimized model
            predictions = {}
            scores = {}
            
            # Isolation Forest
            if 'isolation_forest' in self.optimized_models:
                model = self.optimized_models['isolation_forest']
                pred = model.predict(feature_vector)[0]
                score = model.decision_function(feature_vector)[0]
                predictions['isolation_forest'] = 1 if pred == -1 else 0
                scores['isolation_forest'] = score
            
            # One-Class SVM
            if 'one_class_svm' in self.optimized_models:
                model = self.optimized_models['one_class_svm']
                pred = model.predict(feature_vector)[0]
                score = model.decision_function(feature_vector)[0]
                predictions['one_class_svm'] = 1 if pred == -1 else 0
                scores['one_class_svm'] = score
            
            # LOF Detector
            if 'lof_detector' in self.optimized_models:
                model = self.optimized_models['lof_detector']
                # LOF needs fit_predict, so we use a workaround
                try:
                    pred = model.predict(feature_vector)[0] if hasattr(model, 'predict') else -1
                    predictions['lof_detector'] = 1 if pred == -1 else 0
                    scores['lof_detector'] = -1.0 if pred == -1 else 1.0
                except:
                    predictions['lof_detector'] = 0
                    scores['lof_detector'] = 1.0
            
            # Ensemble voting (majority vote)
            if predictions:
                ensemble_vote = sum(predictions.values()) / len(predictions)
                ensemble_score = ensemble_vote
            else:
                ensemble_score = 0
            
            # Determine if anomaly
            is_anomaly = ensemble_score > 0.5
            
            # Calculate risk level based on ensemble score
            if ensemble_score > 0.8:
                risk_level = "CRITICAL"
            elif ensemble_score > 0.6:
                risk_level = "HIGH"
            elif ensemble_score > 0.3:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            result = {
                'timestamp': record.get('@timestamp', datetime.now().isoformat()),
                'client_ip': record.get('client_ip', 'unknown'),
                'url_path': record.get('url_path', 'unknown'),
                'status_code': record.get('status_code', 'unknown'),
                'is_anomaly': is_anomaly,
                'ensemble_score': ensemble_score,
                'risk_level': risk_level,
                'individual_predictions': predictions,
                'individual_scores': scores
            }
            
            return result
            
        except Exception as e:
            return {
                'error': f"Scoring failed: {str(e)}",
                'timestamp': record.get('@timestamp', datetime.now().isoformat())
            }
    
    def monitor_new_logs(self, interval_seconds: int = 30, max_iterations: int = None):
        """
        Monitor for new logs and score them in real-time
        
        Args:
            interval_seconds (int): Polling interval
            max_iterations (int): Maximum iterations (None for infinite)
        """
        print(f"🔍 Starting real-time anomaly monitoring...")
        print(f"📊 Polling interval: {interval_seconds} seconds")
        print(f"🎯 Anomaly threshold: {self.anomaly_threshold}")
        print("="*60)
        
        iteration = 0
        
        try:
            while True:
                if max_iterations and iteration >= max_iterations:
                    break
                
                # Get recent logs
                query = {
                    "query": {
                        "bool": {
                            "must": [{"match_all": {}}]
                        }
                    },
                    "sort": [{"@timestamp": {"order": "desc"}}],
                    "size": 10  # Check last 10 logs
                }
                
                # Add timestamp filter if we have a last processed timestamp
                if self.last_processed_timestamp:
                    query["query"]["bool"]["must"].append({
                        "range": {
                            "@timestamp": {
                                "gt": self.last_processed_timestamp
                            }
                        }
                    })
                
                try:
                    response = self.es_client.search(index=self.index_name, body=query)
                    hits = response['hits']['hits']
                    
                    if hits:
                        print(f"\n🔍 Processing {len(hits)} new log entries...")
                        
                        anomalies_found = 0
                        
                        for hit in reversed(hits):  # Process chronologically
                            record = hit['_source']
                            result = self.score_record(record)
                            
                            if 'error' not in result:
                                # Update last processed timestamp
                                self.last_processed_timestamp = result['timestamp']
                                
                                # Check for anomalies
                                if result['is_anomaly']:
                                    anomalies_found += 1
                                    self._alert_anomaly(result)
                                else:
                                    print(f"✅ Normal: {result['client_ip']} -> {result['url_path']} (Score: {result['ensemble_score']:.3f})")
                            else:
                                print(f"❌ Error processing record: {result['error']}")
                        
                        if anomalies_found == 0:
                            print(f"🔒 No anomalies detected in latest batch")
                    
                    else:
                        print(f"📊 No new logs found (checked at {datetime.now().strftime('%H:%M:%S')})")
                
                except Exception as e:
                    print(f"❌ Error querying logs: {str(e)}")
                
                # Wait before next iteration
                time.sleep(interval_seconds)
                iteration += 1
                
        except KeyboardInterrupt:
            print(f"\n⏹️  Real-time monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Monitoring error: {str(e)}")
    
    def _alert_anomaly(self, result: Dict):
        """Alert on detected anomaly"""
        print(f"🚨 ANOMALY DETECTED!")
        print(f"   ⏰ Time: {result['timestamp']}")
        print(f"   🌐 IP: {result['client_ip']}")
        print(f"   🔗 Path: {result['url_path']}")
        print(f"   📊 Status: {result['status_code']}")
        print(f"   🎯 Score: {result['ensemble_score']:.3f}")
        print(f"   ⚠️  Risk: {result['risk_level']}")
        print(f"   🔍 Models: {result['individual_predictions']}")
        print("-" * 50)


def main():
    """Main function for real-time ML inference"""
    parser = argparse.ArgumentParser(description='UEBA Real-Time ML Inference Engine')
    parser.add_argument('--model-dir', default='ml_models',
                       help='Directory containing trained models')
    parser.add_argument('--interval', type=int, default=30,
                       help='Polling interval in seconds (default: 30)')
    parser.add_argument('--max-iterations', type=int, default=None,
                       help='Maximum iterations (default: infinite)')
    parser.add_argument('--test-single', action='store_true',
                       help='Test scoring on a single recent record')
    
    args = parser.parse_args()
    
    # Initialize inference engine
    inference = RealTimeMLInference(model_dir=args.model_dir)
    
    if args.test_single:
        # Test on single record
        print("🧪 Testing single record scoring...")
        
        # Get most recent log
        query = {
            "query": {"match_all": {}},
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": 1
        }
        
        try:
            response = inference.es_client.search(index=inference.index_name, body=query)
            if response['hits']['hits']:
                record = response['hits']['hits'][0]['_source']
                result = inference.score_record(record)
                
                print(f"📊 Test Results:")
                print(json.dumps(result, indent=2, default=str))
            else:
                print("❌ No records found for testing")
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
    
    else:
        # Start real-time monitoring
        inference.monitor_new_logs(
            interval_seconds=args.interval,
            max_iterations=args.max_iterations
        )


if __name__ == "__main__":
    main()