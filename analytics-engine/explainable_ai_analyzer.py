#!/usr/bin/env python3
"""
UEBA System v3.0 - Explainable AI Threat Analysis
Provides interpretable explanations for ML model decisions
to help security analysts understand threat classifications.

Author: UEBA System v3.0
Date: October 5, 2025
"""

import pandas as pd
import numpy as np
from datetime import datetime
from elasticsearch import Elasticsearch
import joblib
import json
import shap
import lime
from lime.lime_tabular import LimeTabularExplainer
from sklearn.inspection import permutation_importance
from sklearn.tree import DecisionTreeClassifier, export_text
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class ExplainableAIAnalyzer:
    def __init__(self, es_url="http://localhost:9200", index="nginx-parsed-logs"):
        self.es = Elasticsearch([es_url])
        self.index = index
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_names = []
        self.explanations = {}
        
    def load_latest_models(self):
        """Load the latest trained models for explanation"""
        print("📥 Loading latest models for explainable AI...")
        
        models_dir = Path("ml_models")
        if not models_dir.exists():
            print("❌ Models directory not found")
            return False
            
        # Look for AutoML models first, then optimized models
        model_patterns = ["automl_*.joblib", "optimized_*.joblib"]
        
        for pattern in model_patterns:
            model_files = list(models_dir.glob(pattern))
            if model_files:
                # Find latest timestamp
                timestamps = []
                for file in model_files:
                    try:
                        parts = file.stem.split('_')
                        if len(parts) >= 3:
                            timestamp = f"{parts[-2]}_{parts[-1]}"
                            timestamps.append(timestamp)
                    except:
                        continue
                        
                if timestamps:
                    latest_timestamp = max(timestamps)
                    print(f"📅 Loading models with timestamp: {latest_timestamp}")
                    return self._load_models_by_timestamp(latest_timestamp, pattern.split('_')[0])
                    
        print("❌ No suitable models found")
        return False
        
    def _load_models_by_timestamp(self, timestamp, model_type):
        """Load models by timestamp and type"""
        try:
            models_dir = Path("ml_models")
            
            if model_type == "automl":
                # Load AutoML models
                model_files = {
                    'randomforest': f'automl_randomforest_{timestamp}.joblib',
                    'xgboost': f'automl_xgboost_{timestamp}.joblib',
                    'lightgbm': f'automl_lightgbm_{timestamp}.joblib',
                    'svm': f'automl_svm_{timestamp}.joblib'
                }
                
                scalers_file = f'automl_scalers_{timestamp}.joblib'
                encoders_file = f'automl_encoders_{timestamp}.joblib'
                results_file = f'automl_results_{timestamp}.json'
                
            else:
                # Load optimized models
                model_files = {
                    'isolation_forest': f'optimized_isolation_forest_{timestamp}.joblib',
                    'one_class_svm': f'optimized_one_class_svm_{timestamp}.joblib',
                    'lof_detector': f'optimized_lof_detector_{timestamp}.joblib'
                }
                
                scalers_file = f'optimized_scaler_{timestamp}.joblib'
                encoders_file = None
                results_file = f'optimization_results_{timestamp}.json'
            
            # Load models
            loaded_count = 0
            for name, filename in model_files.items():
                filepath = models_dir / filename
                if filepath.exists():
                    self.models[name] = joblib.load(filepath)
                    loaded_count += 1
                    print(f"✅ Loaded {name}")
                    
            # Load scalers
            scaler_path = models_dir / scalers_file
            if scaler_path.exists():
                if model_type == "automl":
                    self.scalers = joblib.load(scaler_path)
                else:
                    self.scalers['scaler'] = joblib.load(scaler_path)
                print("✅ Loaded scalers")
                
            # Load encoders
            if encoders_file:
                encoder_path = models_dir / encoders_file
                if encoder_path.exists():
                    self.encoders = joblib.load(encoder_path)
                    print("✅ Loaded encoders")
                    
            # Load feature configuration
            results_path = models_dir / results_file
            if results_path.exists():
                with open(results_path, 'r') as f:
                    results = json.load(f)
                    self.feature_names = results.get('feature_columns', [])
                    print(f"✅ Loaded feature configuration: {len(self.feature_names)} features")
                    
            if loaded_count > 0:
                print(f"🎯 Successfully loaded {loaded_count} models for explanation")
                return True
            else:
                print("❌ No models could be loaded")
                return False
                
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            return False
            
    def load_sample_data(self, size=100):
        """Load sample data for explanation"""
        print("📊 Loading sample data for explanation...")
        
        query = {
            "query": {"match_all": {}},
            "size": size,
            "sort": [{"@timestamp": {"order": "desc"}}]
        }
        
        response = self.es.search(index=self.index, body=query)
        hits = response['hits']['hits']
        
        if not hits:
            print("❌ No data found")
            return None
            
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
                'attack_type': source.get('attack_type', 'normal'),
                'threat_detected': source.get('threat_detected', False),
                'response_time': source.get('response_time', 0),
                'country': source.get('country', 'unknown'),
                'city': source.get('city', 'unknown')
            })
        
        df = pd.DataFrame(data)
        print(f"✅ Loaded {len(df)} records for explanation")
        return df
        
    def prepare_explanation_features(self, df):
        """Prepare features for explanation (same as training)"""
        print("🔧 Preparing features for explanation...")
        
        # Create the same features as in AutoML training
        if not self.feature_names:
            # Default comprehensive feature set
            # URL analysis features
            df['url_length'] = df['url'].str.len()
            df['url_depth'] = df['url'].str.count('/')
            df['has_query_params'] = df['url'].str.contains('\\?', na=False).astype(int)
            
            # Security pattern detection
            df['has_script'] = df['url'].str.contains('<script>|javascript:', case=False, na=False).astype(int)
            df['has_sql'] = df['url'].str.contains("'|--|union|select|drop|insert|update|delete", case=False, na=False).astype(int)
            df['has_traversal'] = df['url'].str.contains("\.\./|\.\.\\\\", na=False).astype(int)
            df['has_xss'] = df['url'].str.contains("alert\\(|prompt\\(|confirm\\(", case=False, na=False).astype(int)
            df['has_rfi'] = df['url'].str.contains("http://|https://|ftp://", case=False, na=False).astype(int)
            
            # User agent analysis
            df['ua_length'] = df['user_agent'].str.len()
            df['is_bot'] = df['user_agent'].str.contains('bot|crawler|spider|scraper', case=False, na=False).astype(int)
            df['is_curl'] = df['user_agent'].str.contains('curl|wget|python|java', case=False, na=False).astype(int)
            df['unusual_ua'] = (df['ua_length'] < 20).astype(int)
            
            # HTTP analysis
            df['is_get'] = (df['method'] == 'GET').astype(int)
            df['is_post'] = (df['method'] == 'POST').astype(int)
            df['is_unusual_method'] = df['method'].isin(['PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']).astype(int)
            
            # Status code analysis
            df['is_success'] = ((df['status'] >= 200) & (df['status'] < 300)).astype(int)
            df['is_redirect'] = ((df['status'] >= 300) & (df['status'] < 400)).astype(int)
            df['is_client_error'] = ((df['status'] >= 400) & (df['status'] < 500)).astype(int)
            df['is_server_error'] = (df['status'] >= 500).astype(int)
            
            # Response analysis
            df['large_response'] = (df['size'] > 10000).astype(int)
            df['empty_response'] = (df['size'] == 0).astype(int)
            df['slow_response'] = (df['response_time'] > 1000).astype(int)
            
            # Encode categorical variables using stored encoders
            categorical_cols = ['method', 'attack_type', 'country']
            for col in categorical_cols:
                if col in self.encoders:
                    # Handle unseen labels
                    df[f'{col}_encoded'] = df[col].fillna('unknown').apply(
                        lambda x: self.encoders[col].transform([x])[0] if x in self.encoders[col].classes_ else -1
                    )
                else:
                    # Default encoding if encoder not available
                    df[f'{col}_encoded'] = 0
            
            feature_columns = [
                'status', 'size', 'risk_score', 'response_time',
                'url_length', 'url_depth', 'has_query_params',
                'has_script', 'has_sql', 'has_traversal', 'has_xss', 'has_rfi',
                'ua_length', 'is_bot', 'is_curl', 'unusual_ua',
                'is_get', 'is_post', 'is_unusual_method',
                'is_success', 'is_redirect', 'is_client_error', 'is_server_error',
                'large_response', 'empty_response', 'slow_response',
                'method_encoded', 'attack_type_encoded', 'country_encoded'
            ]
        else:
            # Use configured features
            feature_columns = self.feature_names
            
        # Create features that exist
        existing_features = [col for col in feature_columns if col in df.columns]
        X = df[existing_features].fillna(0)
        
        # Add missing features with zero values
        for col in feature_columns:
            if col not in X.columns:
                X[col] = 0
                
        # Reorder to match training
        X = X[feature_columns]
        
        print(f"✅ Prepared {len(feature_columns)} features for explanation")
        return X, df
        
    def explain_with_shap(self, model, X, model_name, max_samples=50):
        """Generate SHAP explanations for model decisions"""
        print(f"🔍 Generating SHAP explanations for {model_name}...")
        
        try:
            # Use a subset for explanation to avoid memory issues
            X_sample = X.head(max_samples)
            
            # Create SHAP explainer based on model type
            if hasattr(model, 'predict_proba'):
                # For classification models
                explainer = shap.Explainer(model, X_sample)
                shap_values = explainer(X_sample)
                
                # For binary classification, use positive class
                if len(shap_values.shape) > 2:
                    shap_values = shap_values[:, :, 1]
            else:
                # For anomaly detection models (returns -1/1)
                def model_predict(X):
                    pred = model.predict(X)
                    return (pred == -1).astype(int)  # Convert to 0/1
                    
                explainer = shap.Explainer(model_predict, X_sample)
                shap_values = explainer(X_sample)
            
            # Calculate feature importance
            feature_importance = np.abs(shap_values.values).mean(axis=0)
            
            explanations = {
                'model_name': model_name,
                'feature_importance': dict(zip(X.columns, feature_importance)),
                'shap_values': shap_values.values.tolist(),
                'feature_names': list(X.columns),
                'sample_size': len(X_sample)
            }
            
            print(f"✅ Generated SHAP explanations for {len(X_sample)} samples")
            return explanations
            
        except Exception as e:
            print(f"❌ Error generating SHAP explanations for {model_name}: {e}")
            return None
            
    def explain_with_lime(self, model, X, model_name, sample_idx=0):
        """Generate LIME explanation for a specific sample"""
        print(f"🍋 Generating LIME explanation for {model_name} (sample {sample_idx})...")
        
        try:
            # Prepare data for LIME
            X_array = X.values
            
            # Create LIME explainer
            explainer = LimeTabularExplainer(
                X_array,
                feature_names=list(X.columns),
                class_names=['Normal', 'Threat'],
                mode='classification',
                discretize_continuous=True
            )
            
            # Get prediction function
            if hasattr(model, 'predict_proba'):
                predict_fn = model.predict_proba
            else:
                # For anomaly detection models
                def predict_fn(X):
                    pred = model.predict(X)
                    prob_normal = (pred == 1).astype(float)
                    prob_threat = (pred == -1).astype(float)
                    return np.column_stack([prob_normal, prob_threat])
            
            # Generate explanation for the specified sample
            explanation = explainer.explain_instance(
                X_array[sample_idx],
                predict_fn,
                num_features=min(10, len(X.columns))
            )
            
            # Extract explanation data
            lime_data = {
                'model_name': model_name,
                'sample_index': sample_idx,
                'feature_explanations': explanation.as_list(),
                'prediction_probability': explanation.predict_proba.tolist(),
                'local_pred': explanation.local_pred
            }
            
            print(f"✅ Generated LIME explanation for sample {sample_idx}")
            return lime_data
            
        except Exception as e:
            print(f"❌ Error generating LIME explanation for {model_name}: {e}")
            return None
            
    def create_decision_tree_surrogate(self, model, X, y_pred, model_name):
        """Create interpretable decision tree surrogate model"""
        print(f"🌳 Creating decision tree surrogate for {model_name}...")
        
        try:
            # Create a simple decision tree to mimic the complex model
            surrogate = DecisionTreeClassifier(
                max_depth=5,
                min_samples_split=20,
                min_samples_leaf=10,
                random_state=42
            )
            
            # Train surrogate on original model's predictions
            surrogate.fit(X, y_pred)
            
            # Get tree rules as text
            tree_rules = export_text(
                surrogate,
                feature_names=list(X.columns),
                max_depth=5
            )
            
            # Calculate feature importance
            feature_importance = dict(zip(X.columns, surrogate.feature_importances_))
            
            surrogate_data = {
                'model_name': f"{model_name}_surrogate",
                'tree_rules': tree_rules,
                'feature_importance': feature_importance,
                'accuracy': surrogate.score(X, y_pred)
            }
            
            print(f"✅ Created decision tree surrogate (accuracy: {surrogate.score(X, y_pred):.3f})")
            return surrogate_data
            
        except Exception as e:
            print(f"❌ Error creating surrogate model for {model_name}: {e}")
            return None
            
    def generate_threat_explanations(self, df, X):
        """Generate explanations for threat predictions"""
        print("🔍 Generating comprehensive threat explanations...")
        
        all_explanations = {}
        
        for model_name, model in self.models.items():
            print(f"\n📊 Analyzing {model_name}...")
            
            try:
                # Get model predictions
                if hasattr(model, 'predict_proba'):
                    y_pred_proba = model.predict_proba(X)
                    if len(y_pred_proba.shape) > 1 and y_pred_proba.shape[1] > 1:
                        y_pred = (y_pred_proba[:, 1] > 0.5).astype(int)
                    else:
                        y_pred = (y_pred_proba > 0.5).astype(int)
                else:
                    # Anomaly detection models
                    y_pred_raw = model.predict(X)
                    y_pred = (y_pred_raw == -1).astype(int)
                
                model_explanations = {
                    'predictions': y_pred.tolist(),
                    'threat_count': int(y_pred.sum()),
                    'total_samples': len(y_pred)
                }
                
                # SHAP explanations
                shap_exp = self.explain_with_shap(model, X, model_name)
                if shap_exp:
                    model_explanations['shap'] = shap_exp
                
                # LIME explanation for first threat sample
                threat_indices = np.where(y_pred == 1)[0]
                if len(threat_indices) > 0:
                    lime_exp = self.explain_with_lime(model, X, model_name, threat_indices[0])
                    if lime_exp:
                        model_explanations['lime'] = lime_exp
                
                # Decision tree surrogate
                surrogate_exp = self.create_decision_tree_surrogate(model, X, y_pred, model_name)
                if surrogate_exp:
                    model_explanations['surrogate'] = surrogate_exp
                
                all_explanations[model_name] = model_explanations
                
            except Exception as e:
                print(f"❌ Error analyzing {model_name}: {e}")
                continue
                
        return all_explanations
        
    def create_explanation_report(self, explanations, df):
        """Create comprehensive explanation report"""
        print("📋 Creating explanation report...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report = {
            'timestamp': timestamp,
            'analysis_summary': {
                'total_samples': len(df),
                'models_analyzed': list(explanations.keys()),
                'threat_detections': {}
            },
            'model_explanations': explanations,
            'top_threat_features': {},
            'explanation_methodology': {
                'shap': 'SHapley Additive exPlanations for feature importance',
                'lime': 'Local Interpretable Model-agnostic Explanations',
                'surrogate': 'Decision tree surrogate for rule extraction'
            }
        }
        
        # Aggregate threat detection statistics
        for model_name, exp in explanations.items():
            if 'threat_count' in exp:
                report['analysis_summary']['threat_detections'][model_name] = {
                    'threats_detected': exp['threat_count'],
                    'percentage': (exp['threat_count'] / exp['total_samples']) * 100
                }
        
        # Extract top threat features across all models
        all_feature_importance = {}
        for model_name, exp in explanations.items():
            if 'shap' in exp and 'feature_importance' in exp['shap']:
                for feature, importance in exp['shap']['feature_importance'].items():
                    if feature not in all_feature_importance:
                        all_feature_importance[feature] = []
                    all_feature_importance[feature].append(importance)
        
        # Calculate average feature importance
        avg_feature_importance = {
            feature: np.mean(importances) 
            for feature, importances in all_feature_importance.items()
        }
        
        # Get top 10 features
        top_features = sorted(avg_feature_importance.items(), 
                             key=lambda x: x[1], reverse=True)[:10]
        report['top_threat_features'] = dict(top_features)
        
        return report
        
    def save_explanations(self, report):
        """Save explanation report"""
        print("💾 Saving explanation report...")
        
        timestamp = report['timestamp']
        
        # Save JSON report
        report_path = f"ml_models/explainable_ai_report_{timestamp}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
        print(f"✅ Explanation report saved: {report_path}")
        return report_path
        
    def print_explanation_summary(self, report):
        """Print summary of explanations"""
        print("\n🔍 EXPLAINABLE AI ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"📊 Total Samples Analyzed: {report['analysis_summary']['total_samples']}")
        print(f"🤖 Models Analyzed: {len(report['analysis_summary']['models_analyzed'])}")
        
        print("\n🚨 Threat Detection Results:")
        for model, stats in report['analysis_summary']['threat_detections'].items():
            print(f"   {model}: {stats['threats_detected']} threats ({stats['percentage']:.1f}%)")
        
        print("\n🎯 Top Threat Detection Features:")
        for i, (feature, importance) in enumerate(report['top_threat_features'].items(), 1):
            print(f"   {i}. {feature}: {importance:.4f}")
            
        print("\n📋 Explanation Methods Used:")
        for method, description in report['explanation_methodology'].items():
            print(f"   • {method.upper()}: {description}")
            
        print("="*60)
        
    def run_explainable_analysis(self, data_size=100):
        """Run complete explainable AI analysis"""
        print("🔍 EXPLAINABLE AI THREAT ANALYSIS PIPELINE")
        print("="*60)
        
        # Load models
        if not self.load_latest_models():
            print("❌ Cannot load models for explanation")
            return False
            
        # Load sample data
        df = self.load_sample_data(data_size)
        if df is None:
            return False
            
        # Prepare features
        X, df_processed = self.prepare_explanation_features(df)
        
        # Generate explanations
        explanations = self.generate_threat_explanations(df_processed, X)
        
        # Create report
        report = self.create_explanation_report(explanations, df_processed)
        
        # Save report
        self.save_explanations(report)
        
        # Print summary
        self.print_explanation_summary(report)
        
        return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Explainable AI Threat Analyzer")
    parser.add_argument("--size", type=int, default=100, 
                       help="Data size for analysis (default: 100)")
    
    args = parser.parse_args()
    
    analyzer = ExplainableAIAnalyzer()
    analyzer.run_explainable_analysis(args.size)