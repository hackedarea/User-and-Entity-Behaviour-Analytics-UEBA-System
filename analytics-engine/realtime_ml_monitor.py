#!/usr/bin/env python3
"""
Real-time ML Monitoring and Inference System
Provides continuous ML-based threat detection with real-time model inference
and adaptive learning capabilities.

Author: UEBA System
Date: October 5, 2025  
Version: 1.0 - Real-time ML Monitoring
"""

import time
import json
import sys
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import argparse
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import warnings
import queue
import signal

# Import our unified Elasticsearch utility
try:
    from elasticsearch_utility import ElasticsearchUtility
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from elasticsearch_utility import ElasticsearchUtility

# Suppress warnings
warnings.filterwarnings('ignore')

# Fix Windows console encoding for emoji characters
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Setup logging with safe encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('realtime_ml.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class RealTimeMLMonitor:
    """Real-time ML monitoring and inference system"""
    
    def __init__(self, elasticsearch_url: str = "http://localhost:9200",
                 index_name: str = "nginx-parsed-logs",
                 model_dir: str = "ml_models"):
        self.es_url = elasticsearch_url
        self.index_name = index_name
        self.model_dir = model_dir
        self.es_utility = None
        
        # ML Models
        self.models = {}
        self.scaler = None
        self.label_encoders = {}
        
        # Monitoring state
        self.running = False
        self.processing_queue = queue.Queue(maxsize=1000)
        self.stats = {
            'events_processed': 0,
            'anomalies_detected': 0,
            'high_risk_events': 0,
            'start_time': None,
            'last_processed': None
        }
        
        # Performance metrics
        self.performance_window = []
        self.max_window_size = 100
        
        # Initialize
        self._connect_to_elasticsearch()
        self._load_ml_models()
    
    def _connect_to_elasticsearch(self) -> bool:
        """Connect to Elasticsearch using our unified utility"""
        try:
            self.es_utility = ElasticsearchUtility()
            # Test connection
            success, message = self.es_utility.test_connection()
            if success:
                logger.info(f"✅ Connected to Elasticsearch: {message}")
                return True
            else:
                logger.error(f"❌ Failed to connect to Elasticsearch: {message}")
                return False
        except Exception as e:
            logger.error(f"❌ Elasticsearch connection error: {str(e)}")
            return False
    
    def _load_ml_models(self) -> bool:
        """Load trained ML models"""
        try:
            model_files = {
                'isolation_forest': 'isolation_forest_model.joblib',
                'one_class_svm': 'one_class_svm_model.joblib', 
                'lof_detector': 'lof_detector_model.joblib',
                'scaler': 'scaler_model.joblib',
                'label_encoders': 'label_encoders.joblib'
            }
            
            import os
            
            for model_name, filename in model_files.items():
                filepath = os.path.join(self.model_dir, filename)
                
                if os.path.exists(filepath):
                    if model_name == 'scaler':
                        self.scaler = joblib.load(filepath)
                    elif model_name == 'label_encoders':
                        self.label_encoders = joblib.load(filepath)
                    else:
                        self.models[model_name] = joblib.load(filepath)
                    logger.info(f"✅ Loaded {model_name}")
                else:
                    logger.warning(f"⚠️  Model file not found: {filepath}")
            
            if len(self.models) > 0:
                logger.info(f"✅ Loaded {len(self.models)} ML models successfully")
                return True
            else:
                logger.error("❌ No ML models loaded")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error loading ML models: {str(e)}")
            return False
    
    def engineer_features(self, event: Dict) -> np.ndarray:
        """Engineer features for a single event"""
        try:
            # Create DataFrame with single event
            df = pd.DataFrame([event])
            
            # Engineer temporal features
            if '@timestamp' in df.columns:
                df['@timestamp'] = pd.to_datetime(df['@timestamp'])
                df['hour_of_day'] = df['@timestamp'].dt.hour
                df['day_of_week'] = df['@timestamp'].dt.dayofweek
                df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
                df['is_business_hours'] = ((df['hour_of_day'] >= 9) & (df['hour_of_day'] <= 17)).astype(int)
                df['is_night_time'] = ((df['hour_of_day'] >= 22) | (df['hour_of_day'] <= 6)).astype(int)
            else:
                # Default values if timestamp missing
                now = datetime.now()
                df['hour_of_day'] = now.hour
                df['day_of_week'] = now.weekday()
                df['is_weekend'] = 1 if now.weekday() >= 5 else 0
                df['is_business_hours'] = 1 if 9 <= now.hour <= 17 else 0
                df['is_night_time'] = 1 if now.hour >= 22 or now.hour <= 6 else 0
            
            # User agent features
            user_agent = event.get('http_user_agent', '')
            df['is_bot'] = 1 if any(bot in user_agent.lower() for bot in ['bot', 'crawler', 'spider', 'scraper']) else 0
            df['is_curl'] = 1 if 'curl' in user_agent.lower() else 0
            df['is_mobile'] = 1 if any(mobile in user_agent.lower() for mobile in ['mobile', 'android', 'iphone']) else 0
            df['user_agent_length'] = len(user_agent)
            
            # Request method features
            method = event.get('request_method', 'GET')
            df['is_get'] = 1 if method == 'GET' else 0
            df['is_post'] = 1 if method == 'POST' else 0
            df['is_suspicious_method'] = 1 if method in ['PUT', 'DELETE', 'PATCH', 'TRACE', 'CONNECT'] else 0
            
            # Encode method
            if 'request_method' in self.label_encoders:
                try:
                    df['method_encoded'] = self.label_encoders['request_method'].transform([method])[0]
                except:
                    df['method_encoded'] = 0
            else:
                df['method_encoded'] = 0
            
            # Select feature columns
            feature_columns = [
                'hour_of_day', 'day_of_week', 'is_weekend', 'is_business_hours', 'is_night_time',
                'is_bot', 'is_curl', 'is_mobile', 'user_agent_length',
                'is_get', 'is_post', 'is_suspicious_method', 'method_encoded'
            ]
            
            # Create feature matrix
            features = df[feature_columns].fillna(0).values
            
            # Scale features
            if self.scaler:
                features = self.scaler.transform(features)
            
            return features
            
        except Exception as e:
            logger.error(f"❌ Feature engineering error: {str(e)}")
            # Return zero vector as fallback
            return np.zeros((1, 13))
    
    def predict_anomaly(self, event: Dict) -> Dict:
        """Predict if event is anomalous using ensemble of models"""
        try:
            # Engineer features
            features = self.engineer_features(event)
            
            # Get predictions from all models
            predictions = {}
            scores = {}
            
            for model_name, model in self.models.items():
                try:
                    if model_name == 'isolation_forest':
                        pred = model.predict(features)[0]
                        score = model.decision_function(features)[0]
                        predictions[model_name] = pred
                        scores[model_name] = score
                    
                    elif model_name == 'one_class_svm':
                        pred = model.predict(features)[0]
                        score = model.decision_function(features)[0]
                        predictions[model_name] = pred
                        scores[model_name] = score
                    
                    elif model_name == 'lof_detector':
                        pred = model.fit_predict(features)[0]
                        score = model.negative_outlier_factor_[0] if hasattr(model, 'negative_outlier_factor_') else -1.0
                        predictions[model_name] = pred
                        scores[model_name] = score
                        
                except Exception as model_error:
                    logger.warning(f"⚠️  Model {model_name} prediction failed: {str(model_error)}")
                    predictions[model_name] = 1  # Normal by default
                    scores[model_name] = 0.0
            
            # Calculate ensemble score
            anomaly_votes = sum(1 for pred in predictions.values() if pred == -1)
            total_models = len(predictions)
            ensemble_score = anomaly_votes / total_models if total_models > 0 else 0
            
            # Determine if anomalous (majority vote)
            is_anomaly = anomaly_votes > (total_models / 2)
            
            # Calculate risk level
            risk_level = "LOW"
            if ensemble_score >= 0.75:
                risk_level = "CRITICAL"
            elif ensemble_score >= 0.5:
                risk_level = "HIGH"
            elif ensemble_score >= 0.25:
                risk_level = "MEDIUM"
            
            return {
                'is_anomaly': is_anomaly,
                'ensemble_score': ensemble_score,
                'risk_level': risk_level,
                'model_predictions': predictions,
                'model_scores': scores,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Prediction error: {str(e)}")
            return {
                'is_anomaly': False,
                'ensemble_score': 0.0,
                'risk_level': "LOW",
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def process_event_stream(self, duration_minutes: int = 30):
        """Process real-time event stream"""
        logger.info(f"🚀 Starting real-time ML monitoring for {duration_minutes} minutes")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        self.stats['start_time'] = start_time
        self.running = True
        
        try:
            while self.running and datetime.now() < end_time:
                # Query for recent events
                now = datetime.now()
                since = now - timedelta(minutes=1)  # Check last minute
                
                query = {
                    "query": {
                        "range": {
                            "@timestamp": {
                                "gte": since.isoformat(),
                                "lte": now.isoformat()
                            }
                        }
                    },
                    "sort": [{"@timestamp": {"order": "desc"}}],
                    "size": 50
                }
                
                try:
                    response = self.es_utility.search_with_query(
                        index=self.index_name,
                        query=query
                    )
                    events = response['hits']['hits'] if response and 'hits' in response else []
                    
                    for hit in events:
                        event = hit['_source']
                        
                        # Skip if already processed (basic deduplication)
                        event_time = event.get('@timestamp')
                        if self.stats['last_processed'] and event_time <= self.stats['last_processed']:
                            continue
                        
                        # Predict anomaly
                        start_predict = time.time()
                        prediction = self.predict_anomaly(event)
                        predict_time = time.time() - start_predict
                        
                        # Update performance metrics
                        self.performance_window.append(predict_time)
                        if len(self.performance_window) > self.max_window_size:
                            self.performance_window.pop(0)
                        
                        # Update statistics
                        self.stats['events_processed'] += 1
                        self.stats['last_processed'] = event_time
                        
                        if prediction['is_anomaly']:
                            self.stats['anomalies_detected'] += 1
                            
                            # Log anomaly
                            logger.warning(
                                f"🚨 ANOMALY DETECTED - Risk: {prediction['risk_level']} "
                                f"Score: {prediction['ensemble_score']:.3f} "
                                f"IP: {event.get('remote_addr', 'N/A')}"
                            )
                            
                            if prediction['risk_level'] in ['HIGH', 'CRITICAL']:
                                self.stats['high_risk_events'] += 1
                        
                        # Log progress every 100 events
                        if self.stats['events_processed'] % 100 == 0:
                            self._log_progress()
                    
                except Exception as query_error:
                    logger.error(f"❌ Query error: {str(query_error)}")
                
                # Wait before next check
                time.sleep(5)  # Check every 5 seconds
                
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring stopped by user")
        finally:
            self.running = False
            self._log_final_stats()
    
    def _log_progress(self):
        """Log current progress and performance"""
        runtime = datetime.now() - self.stats['start_time']
        avg_predict_time = np.mean(self.performance_window) if self.performance_window else 0
        
        logger.info(
            f"📊 Progress - Events: {self.stats['events_processed']}, "
            f"Anomalies: {self.stats['anomalies_detected']}, "
            f"High Risk: {self.stats['high_risk_events']}, "
            f"Runtime: {runtime}, "
            f"Avg Prediction Time: {avg_predict_time:.4f}s"
        )
    
    def _log_final_stats(self):
        """Log final monitoring statistics"""
        runtime = datetime.now() - self.stats['start_time']
        anomaly_rate = (self.stats['anomalies_detected'] / self.stats['events_processed'] * 100) if self.stats['events_processed'] > 0 else 0
        avg_predict_time = np.mean(self.performance_window) if self.performance_window else 0
        
        logger.info("🎯 FINAL MONITORING STATISTICS")
        logger.info("=" * 50)
        logger.info(f"📊 Total Events Processed: {self.stats['events_processed']}")
        logger.info(f"🚨 Anomalies Detected: {self.stats['anomalies_detected']}")
        logger.info(f"⚠️  High Risk Events: {self.stats['high_risk_events']}")
        logger.info(f"📈 Anomaly Rate: {anomaly_rate:.2f}%")
        logger.info(f"⏱️  Total Runtime: {runtime}")
        logger.info(f"⚡ Average Prediction Time: {avg_predict_time:.4f} seconds")
        logger.info(f"🎯 Processing Rate: {self.stats['events_processed']/runtime.total_seconds():.2f} events/second")
        logger.info("=" * 50)

def signal_handler(signum, frame):
    """Handle interrupt signals gracefully"""
    logger.info("🛑 Received interrupt signal, shutting down...")
    sys.exit(0)

def main():
    """Main function for real-time ML monitoring"""
    parser = argparse.ArgumentParser(description='Real-time ML Monitoring System')
    parser.add_argument('--duration', type=int, default=30,
                       help='Monitoring duration in minutes (default: 30)')
    parser.add_argument('--model-dir', type=str, default='../ml_models',
                       help='Directory containing ML models (default: ../ml_models)')
    
    args = parser.parse_args()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("⚡ UEBA Real-time ML Monitoring System")
    print("=" * 50)
    print(f"⏰ Duration: {args.duration} minutes")
    print(f"📁 Model Directory: {args.model_dir}")
    print("=" * 50)
    
    # Initialize monitor
    monitor = RealTimeMLMonitor(model_dir=args.model_dir)
    
    if not monitor.models:
        logger.error("❌ No ML models loaded. Please train models first.")
        sys.exit(1)
    
    try:
        # Start monitoring
        monitor.process_event_stream(duration_minutes=args.duration)
    except Exception as e:
        logger.error(f"❌ Monitoring error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()