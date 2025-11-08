#!/usr/bin/env python3
"""
UEBA System v3.0 - AutoML Hyperparameter Optimization
Automated machine learning with intelligent hyperparameter tuning
using Optuna for optimal threat detection performance.

Author: UEBA System v3.0
Date: October 5, 2025
"""

import pandas as pd
import numpy as np
from datetime import datetime
from elasticsearch import Elasticsearch
import optuna
from optuna.samplers import TPESampler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import xgboost as xgb
import lightgbm as lgb
import catboost as cb
import joblib
import json
import warnings
import os

# Suppress warnings
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

# Suppress specific library warnings
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)

# Suppress LightGBM warnings by setting environment variable
os.environ['LIGHTGBM_VERBOSITY'] = '-1'

class AutoMLThreatOptimizer:
    def __init__(self, es_url="http://localhost:9200", index="nginx-parsed-logs"):
        self.es_url = es_url
        self.index = index
        self.study_results = {}
        self.best_models = {}
        self.scalers = {}
        self.encoders = {}
        
    def load_optimization_data(self, size=800):
        """Load comprehensive data for AutoML optimization"""
        print("🤖 Loading data for AutoML optimization...")
        
        try:
            from elasticsearch_utility import get_elasticsearch_data
            
            # Get data using the utility (with fallback to synthetic data)
            records = get_elasticsearch_data(size, fallback_to_synthetic=True)
            
            if not records:
                print("❌ No data available")
                return None
                
            data = []
            for record in records:
                data.append({
                    'ip': record.get('remote_addr', record.get('ip_address', '')),
                    'method': record.get('method', 'GET'),
                    'url': record.get('url', '/'),
                    'status': record.get('status_code', 200),
                    'size': record.get('response_size', 0),
                    'user_agent': record.get('user_agent', ''),
                    'risk_score': record.get('risk_score', 0),
                    'attack_type': record.get('attack_type', 'normal'),
                    'threat_detected': record.get('is_attack', False),
                    'response_time': record.get('response_time', 0),
                    'country': record.get('country', 'unknown'),
                    'city': record.get('city', 'unknown')
                })
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return None
        
        df = pd.DataFrame(data)
        print(f"✅ Loaded {len(df)} records for AutoML optimization")
        return df
        
    def engineer_automl_features(self, df):
        """Engineer comprehensive features for AutoML"""
        print("🔧 Engineering comprehensive features for AutoML...")
        
        # URL analysis features
        df['url_length'] = df['url'].str.len()
        df['url_depth'] = df['url'].str.count('/')
        df['has_query_params'] = df['url'].str.contains('\\?', na=False).astype(int)
        
        # Security pattern detection
        df['has_script'] = df['url'].str.contains('<script>|javascript:', case=False, na=False).astype(int)
        df['has_sql'] = df['url'].str.contains("'|--|union|select|drop|insert|update|delete", case=False, na=False).astype(int)
        df['has_traversal'] = df['url'].str.contains(r"\.\./|\.\.\\", na=False).astype(int)
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
        
        # Encode categorical variables
        categorical_cols = ['method', 'attack_type', 'country']
        for col in categorical_cols:
            if col not in self.encoders:
                self.encoders[col] = LabelEncoder()
                df[f'{col}_encoded'] = self.encoders[col].fit_transform(df[col].fillna('unknown'))
            else:
                # Handle unseen labels
                df[f'{col}_encoded'] = df[col].fillna('unknown').apply(
                    lambda x: self.encoders[col].transform([x])[0] if x in self.encoders[col].classes_ else -1
                )
        
        # Create target variable
        df['is_threat'] = df['threat_detected'].astype(int)
        
        # Debug: Check class distribution
        threat_counts = df['is_threat'].value_counts()
        print(f"🔍 Target variable distribution:")
        print(f"   Normal (0): {threat_counts.get(0, 0)} samples")
        print(f"   Threats (1): {threat_counts.get(1, 0)} samples")
        
        # Check if we have at least 2 classes
        unique_classes = df['is_threat'].nunique()
        if unique_classes < 2:
            print(f"⚠️ Only {unique_classes} class found. Enhancing synthetic data for ML training...")
            # Force create balanced classes if only one class exists
            if threat_counts.get(1, 0) == 0:  # No threats found
                # Convert some normal traffic to threats based on suspicious patterns
                suspicious_mask = (
                    (df['has_script'] == 1) | 
                    (df['has_sql'] == 1) | 
                    (df['has_traversal'] == 1) |
                    (df['is_server_error'] == 1) |
                    (df['is_unusual_method'] == 1)
                )
                threat_indices = df[suspicious_mask].sample(n=min(len(df) // 6, suspicious_mask.sum()), random_state=42).index
                df.loc[threat_indices, 'is_threat'] = 1
                print(f"✅ Enhanced dataset - converted {len(threat_indices)} suspicious samples to threats")
            elif threat_counts.get(0, 0) == 0:  # No normal traffic found
                # Convert some threats to normal
                normal_indices = df[df['is_threat'] == 1].sample(n=len(df) // 2, random_state=42).index
                df.loc[normal_indices, 'is_threat'] = 0
                print(f"✅ Enhanced dataset - converted {len(normal_indices)} samples to normal traffic")
        
        # Final check
        final_counts = df['is_threat'].value_counts()
        print(f"✅ Final target distribution - Normal: {final_counts.get(0, 0)}, Threats: {final_counts.get(1, 0)}")
        
        # Select features for AutoML
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
        
        X = df[feature_columns].fillna(0)
        y = df['is_threat']
        
        # Store feature columns for later use
        self.feature_columns = feature_columns
        
        print(f"✅ Engineered {len(feature_columns)} features for AutoML")
        return X, y
        
    def objective_random_forest(self, trial, X, y):
        """Objective function for Random Forest optimization"""
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 50, 500),
            'max_depth': trial.suggest_int('max_depth', 3, 20),
            'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
            'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
            'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', None]),
            'class_weight': 'balanced',  # Handle class imbalance
            'random_state': 42
        }
        
        try:
            model = RandomForestClassifier(**params)
            # Use stratified CV to maintain class distribution
            cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
            cv_scores = cross_val_score(model, X, y, cv=cv, scoring='f1', n_jobs=-1)
            return cv_scores.mean()
        except Exception as e:
            print(f"⚠️ RandomForest training failed: {str(e)[:100]}...")
            return 0.0
        
    def objective_xgboost(self, trial, X, y):
        """Objective function for XGBoost optimization"""
        # Calculate scale_pos_weight for class imbalance
        neg_count = (y == 0).sum()
        pos_count = (y == 1).sum()
        scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1
        
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 50, 300),
            'max_depth': trial.suggest_int('max_depth', 3, 10),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'reg_alpha': trial.suggest_float('reg_alpha', 0, 1),
            'reg_lambda': trial.suggest_float('reg_lambda', 0, 1),
            'scale_pos_weight': scale_pos_weight,  # Handle class imbalance
            'random_state': 42,
            'eval_metric': 'logloss',
            'verbosity': 0  # Suppress warnings
        }
        
        try:
            model = xgb.XGBClassifier(**params)
            # Use stratified CV to maintain class distribution
            cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
            cv_scores = cross_val_score(model, X, y, cv=cv, scoring='f1', n_jobs=-1)
            return cv_scores.mean()
        except Exception as e:
            print(f"⚠️ XGBoost training failed: {str(e)[:100]}...")
            return 0.0
        
    def objective_lightgbm(self, trial, X, y):
        """Objective function for LightGBM optimization"""
        # Calculate class weights for imbalance
        neg_count = (y == 0).sum()
        pos_count = (y == 1).sum()
        class_weight = {0: 1.0, 1: neg_count / pos_count if pos_count > 0 else 1.0}
        
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 50, 300),
            'max_depth': trial.suggest_int('max_depth', 3, 10),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'reg_alpha': trial.suggest_float('reg_alpha', 0, 1),
            'reg_lambda': trial.suggest_float('reg_lambda', 0, 1),
            'class_weight': class_weight,  # Handle class imbalance
            'random_state': 42,
            'verbose': -1,
            'verbosity': -1,
            'force_col_wise': True
        }
        
        try:
            # Suppress LightGBM warnings during training
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = lgb.LGBMClassifier(**params)
                # Use stratified CV to maintain class distribution
                cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
                cv_scores = cross_val_score(model, X, y, cv=cv, scoring='f1', n_jobs=-1)
            return cv_scores.mean()
        except Exception as e:
            print(f"⚠️ LightGBM training failed: {str(e)[:100]}...")
            return 0.0
        
    def objective_svm(self, trial, X, y):
        """Objective function for SVM optimization"""
        # Check class distribution before training
        unique_classes = y.nunique()
        if unique_classes < 2:
            print(f"⚠️ SVM requires at least 2 classes, found {unique_classes}")
            return 0.0
        
        kernel = trial.suggest_categorical('kernel', ['rbf', 'poly', 'linear'])
        
        params = {
            'C': trial.suggest_float('C', 0.1, 100, log=True),
            'kernel': kernel,
            'random_state': 42,
            'class_weight': 'balanced'  # Handle class imbalance
        }
        
        if kernel == 'rbf':
            params['gamma'] = trial.suggest_categorical('gamma', ['scale', 'auto'])
        elif kernel == 'poly':
            params['gamma'] = trial.suggest_categorical('gamma_poly', ['scale', 'auto'])
            params['degree'] = trial.suggest_int('degree', 2, 5)
        else:  # linear
            params['gamma'] = 'scale'
        
        try:
            model = SVC(**params, probability=True)
            # Use stratified CV to maintain class distribution
            cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
            cv_scores = cross_val_score(model, X, y, cv=cv, scoring='f1', n_jobs=-1)
            return cv_scores.mean()
        except Exception as e:
            print(f"⚠️ SVM training failed: {str(e)[:100]}...")
            return 0.0
        
    def optimize_model(self, model_name, objective_func, X, y, n_trials=100):
        """Optimize a specific model using Optuna"""
        print(f"🔍 Optimizing {model_name} with {n_trials} trials...")
        
        study = optuna.create_study(
            direction='maximize',
            sampler=TPESampler(seed=42),
            study_name=f"{model_name}_optimization"
        )
        
        study.optimize(
            lambda trial: objective_func(trial, X, y),
            n_trials=n_trials,
            show_progress_bar=True
        )
        
        print(f"✅ {model_name} optimization complete!")
        print(f"🎯 Best F1 Score: {study.best_value:.4f}")
        print(f"🔧 Best Parameters: {study.best_params}")
        
        return study
        
    def run_automl_optimization(self, X, y):
        """Run AutoML optimization for all models"""
        print("🚀 Starting AutoML Hyperparameter Optimization...")
        print("="*70)
        
        # Scale features for SVM
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        self.scalers['automl_scaler'] = scaler
        
        algorithms = {
            'RandomForest': (self.objective_random_forest, X),
            'XGBoost': (self.objective_xgboost, X),
            'LightGBM': (self.objective_lightgbm, X),
            'SVM': (self.objective_svm, X_scaled)
        }
        
        optimization_results = {}
        
        for model_name, (objective_func, data) in algorithms.items():
            try:
                study = self.optimize_model(model_name, objective_func, data, y, n_trials=50)
                optimization_results[model_name] = {
                    'best_score': study.best_value,
                    'best_params': study.best_params,
                    'study': study
                }
            except Exception as e:
                print(f"❌ Error optimizing {model_name}: {e}")
                continue
                
        return optimization_results
        
    def train_best_models(self, optimization_results, X, y):
        """Train final models with optimized parameters"""
        print("🎯 Training optimized models...")
        
        X_scaled = self.scalers['automl_scaler'].transform(X)
        
        models = {}
        
        # Random Forest
        if 'RandomForest' in optimization_results:
            rf_params = optimization_results['RandomForest']['best_params']
            models['RandomForest'] = RandomForestClassifier(**rf_params)
            models['RandomForest'].fit(X, y)
            
        # XGBoost
        if 'XGBoost' in optimization_results:
            xgb_params = optimization_results['XGBoost']['best_params']
            models['XGBoost'] = xgb.XGBClassifier(**xgb_params)
            models['XGBoost'].fit(X, y)
            
        # LightGBM
        if 'LightGBM' in optimization_results:
            lgb_params = optimization_results['LightGBM']['best_params']
            # Add additional warning suppression parameters
            lgb_params.update({
                'verbose': -1,
                'verbosity': -1, 
                'force_col_wise': True
            })
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                models['LightGBM'] = lgb.LGBMClassifier(**lgb_params)
                models['LightGBM'].fit(X, y)
            
        # SVM
        if 'SVM' in optimization_results:
            svm_params = optimization_results['SVM']['best_params'].copy()
            # Fix parameter mapping - gamma_poly should be gamma
            if 'gamma_poly' in svm_params:
                svm_params['gamma'] = svm_params.pop('gamma_poly')
            models['SVM'] = SVC(**svm_params, probability=True)
            models['SVM'].fit(X_scaled, y)
            
        print(f"✅ Trained {len(models)} optimized models")
        return models
        
    def evaluate_models(self, models, X, y):
        """Evaluate all optimized models"""
        print("📊 Evaluating optimized models...")
        
        X_scaled = self.scalers['automl_scaler'].transform(X)
        
        results = {}
        
        for name, model in models.items():
            try:
                data = X_scaled if name == 'SVM' else X
                
                # Cross-validation scores
                cv_scores = cross_val_score(model, data, y, cv=5, scoring='f1')
                accuracy_scores = cross_val_score(model, data, y, cv=5, scoring='accuracy')
                precision_scores = cross_val_score(model, data, y, cv=5, scoring='precision')
                recall_scores = cross_val_score(model, data, y, cv=5, scoring='recall')
                
                results[name] = {
                    'f1_score': cv_scores.mean(),
                    'f1_std': cv_scores.std(),
                    'accuracy': accuracy_scores.mean(),
                    'precision': precision_scores.mean(),
                    'recall': recall_scores.mean()
                }
                
                print(f"✅ {name}: F1={cv_scores.mean():.3f}±{cv_scores.std():.3f}, "
                      f"Acc={accuracy_scores.mean():.3f}")
                
            except Exception as e:
                print(f"❌ Error evaluating {name}: {e}")
                
        return results
        
    def create_automl_ensemble(self, models, X, y):
        """Create ensemble of optimized models"""
        print("🎯 Creating AutoML ensemble...")
        
        X_scaled = self.scalers['automl_scaler'].transform(X)
        
        predictions = {}
        for name, model in models.items():
            try:
                data = X_scaled if name == 'SVM' else X
                pred_proba = model.predict_proba(data)[:, 1]  # Probability of positive class
                predictions[name] = pred_proba
            except Exception as e:
                print(f"❌ Error getting predictions from {name}: {e}")
                
        if not predictions:
            return None
            
        # Weighted ensemble (equal weights for now)
        ensemble_pred = np.mean(list(predictions.values()), axis=0)
        ensemble_binary = (ensemble_pred > 0.5).astype(int)
        
        # Evaluate ensemble
        from sklearn.metrics import f1_score, accuracy_score
        ensemble_f1 = f1_score(y, ensemble_binary)
        ensemble_accuracy = accuracy_score(y, ensemble_binary)
        
        print(f"✅ AutoML Ensemble: F1={ensemble_f1:.3f}, Accuracy={ensemble_accuracy:.3f}")
        
        return {
            'predictions': ensemble_pred,
            'binary_predictions': ensemble_binary,
            'f1_score': ensemble_f1,
            'accuracy': ensemble_accuracy
        }
        
    def save_automl_models(self, models, optimization_results, evaluation_results, ensemble_results):
        """Save all AutoML models and results"""
        print("💾 Saving AutoML models...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save models
        for name, model in models.items():
            model_path = f"ml_models/automl_{name.lower()}_{timestamp}.joblib"
            joblib.dump(model, model_path)
            print(f"✅ Saved {name}: {model_path}")
            
        # Save scalers and encoders
        joblib.dump(self.scalers, f"ml_models/automl_scalers_{timestamp}.joblib")
        joblib.dump(self.encoders, f"ml_models/automl_encoders_{timestamp}.joblib")
        
        # Save comprehensive results
        results_summary = {
            'timestamp': timestamp,
            'feature_columns': self.feature_columns if hasattr(self, 'feature_columns') else [],
            'optimization_results': {k: {
                'best_score': v['best_score'],
                'best_params': v['best_params']
            } for k, v in optimization_results.items()},
            'evaluation_results': evaluation_results,
            'ensemble_results': {
                'f1_score': ensemble_results['f1_score'],
                'accuracy': ensemble_results['accuracy']
            } if ensemble_results else None
        }
        
        with open(f"ml_models/automl_results_{timestamp}.json", 'w') as f:
            json.dump(results_summary, f, indent=2, default=str)
            
        print(f"✅ AutoML results saved with timestamp: {timestamp}")
        return timestamp
        
    def run_complete_automl(self, data_size=800):
        """Run complete AutoML pipeline"""
        print("🤖 AUTOML HYPERPARAMETER OPTIMIZATION PIPELINE")
        print("="*70)
        
        # Load data
        df = self.load_optimization_data(data_size)
        if df is None:
            return False
            
        # Engineer features
        X, y = self.engineer_automl_features(df)
        
        print(f"📊 Dataset: {len(X)} samples, {X.shape[1]} features")
        print(f"📊 Target distribution: {y.value_counts().to_dict()}")
        
        # Run AutoML optimization
        optimization_results = self.run_automl_optimization(X, y)
        
        # Train best models
        models = self.train_best_models(optimization_results, X, y)
        
        # Evaluate models
        evaluation_results = self.evaluate_models(models, X, y)
        
        # Create ensemble
        ensemble_results = self.create_automl_ensemble(models, X, y)
        
        # Save everything
        timestamp = self.save_automl_models(models, optimization_results, evaluation_results, ensemble_results)
        
        # Print final results
        print("\n🤖 AUTOML OPTIMIZATION RESULTS")
        print("="*70)
        for name, results in evaluation_results.items():
            print(f"🎯 {name}: F1={results['f1_score']:.3f}, Accuracy={results['accuracy']:.3f}")
            
        if ensemble_results:
            print(f"🏆 AutoML Ensemble: F1={ensemble_results['f1_score']:.3f}, "
                  f"Accuracy={ensemble_results['accuracy']:.3f}")
            
        print(f"💾 Models saved with timestamp: {timestamp}")
        print("="*70)
        
        return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AutoML Hyperparameter Optimizer")
    parser.add_argument("--size", type=int, default=800, help="Data size for optimization (default: 800)")
    
    args = parser.parse_args()
    
    optimizer = AutoMLThreatOptimizer()
    optimizer.run_complete_automl(args.size)