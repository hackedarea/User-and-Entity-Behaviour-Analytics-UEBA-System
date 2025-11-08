#!/usr/bin/env python3
"""
UEBA System v3.0 - Advanced Neural Network Threat Detector
Implements LSTM and CNN neural networks for sophisticated 
pattern detection in cybersecurity events.

Author: UEBA System v3.0
Date: October 5, 2025
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
import warnings
import os

# Suppress warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow warnings

import tensorflow as tf
tf.get_logger().setLevel('ERROR')  # Only show errors

# Use direct tf.keras imports to avoid Pylance import resolution issues
Sequential = tf.keras.models.Sequential
Model = tf.keras.models.Model
LSTM = tf.keras.layers.LSTM
Dense = tf.keras.layers.Dense
Dropout = tf.keras.layers.Dropout
Conv1D = tf.keras.layers.Conv1D
MaxPooling1D = tf.keras.layers.MaxPooling1D
Flatten = tf.keras.layers.Flatten
Input = tf.keras.layers.Input
Concatenate = tf.keras.layers.Concatenate
BatchNormalization = tf.keras.layers.BatchNormalization
Adam = tf.keras.optimizers.Adam
EarlyStopping = tf.keras.callbacks.EarlyStopping
ReduceLROnPlateau = tf.keras.callbacks.ReduceLROnPlateau
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
import json

class AdvancedNeuralThreatDetector:
    def __init__(self, es_url="http://localhost:9200", index="nginx-parsed-logs"):
        self.es = Elasticsearch([es_url])
        self.index = index
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.sequence_length = 10  # For LSTM sequence analysis
        
        # Neural network architectures
        self.architectures = {
            'lstm': self._build_lstm_model,
            'cnn': self._build_cnn_model,
            'hybrid': self._build_hybrid_model
        }
        
        # Create models directory
        self.models_dir = "ml_models"
        os.makedirs(self.models_dir, exist_ok=True)
        
    def load_data(self, size=None):
        """Load data for advanced neural network training"""
        print("🧠 Loading data for neural network training...")
        
        # Generate synthetic cybersecurity data for demonstration
        np.random.seed(42)
        data = []
        
        # Generate normal and anomalous patterns
        for i in range(size or 1000):
            is_threat = np.random.choice([0, 1], p=[0.7, 0.3])
            
            # Base features
            base_features = {
                'timestamp': datetime.now() - timedelta(hours=np.random.randint(0, 24*7)),
                'user_id': f"user_{np.random.randint(1, 100)}",
                'session_id': f"session_{np.random.randint(1, 1000)}",
                'source_ip': f"192.168.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}",
                'method': np.random.choice(['GET', 'POST', 'PUT', 'DELETE']),
                'status': np.random.choice([200, 404, 500, 403, 401], p=[0.7, 0.1, 0.1, 0.05, 0.05]),
                'response_time': np.random.exponential(0.5),
                'size': np.random.exponential(1000),
                'user_agent': np.random.choice(['Chrome', 'Firefox', 'Safari', 'Edge', 'Bot']),
                'is_threat': is_threat
            }
            
            # Add threat-specific patterns
            if is_threat:
                base_features['status'] = np.random.choice([403, 404, 500], p=[0.4, 0.3, 0.3])
                base_features['response_time'] = np.random.exponential(2.0)  # Slower responses
                base_features['size'] = np.random.exponential(5000)  # Larger payloads
                
            data.append(base_features)
        
        df = pd.DataFrame(data)
        print(f"✅ Loaded {len(df)} records for neural network analysis")
        return df
    
    def engineer_features(self, df):
        """Engineer advanced features for neural networks"""
        print("🔧 Engineering advanced features for neural networks...")
        
        # Temporal features
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['is_business_hours'] = df['hour'].between(9, 17).astype(int)
        
        # Categorical encoding
        categorical_cols = ['method', 'user_agent', 'user_id', 'source_ip']
        for col in categorical_cols:
            if col not in self.encoders:
                self.encoders[col] = LabelEncoder()
                df[f'{col}_encoded'] = self.encoders[col].fit_transform(df[col].astype(str))
            else:
                # Handle unseen values
                try:
                    df[f'{col}_encoded'] = self.encoders[col].transform(df[col].astype(str))
                except ValueError:
                    # For unseen values, assign -1
                    known_values = set(self.encoders[col].classes_)
                    df[f'{col}_encoded'] = df[col].apply(
                        lambda x: self.encoders[col].transform([x])[0] if x in known_values else -1
                    )
        
        # Statistical features
        df['log_response_time'] = np.log1p(df['response_time'])
        df['log_size'] = np.log1p(df['size'])
        df['status_group'] = df['status'].apply(lambda x: x // 100)  # 2xx, 4xx, 5xx
        
        # Risk scoring
        df['risk_score'] = (
            (df['status'] >= 400).astype(int) * 0.3 +
            (df['response_time'] > df['response_time'].quantile(0.9)).astype(int) * 0.2 +
            (df['size'] > df['size'].quantile(0.9)).astype(int) * 0.2 +
            (~df['is_business_hours']).astype(int) * 0.1 +
            df['is_weekend'].astype(int) * 0.1 +
            (df['user_agent'] == 'Bot').astype(int) * 0.1
        )
        
        # User behavior features
        user_stats = df.groupby('user_id').agg({
            'response_time': ['mean', 'std'],
            'size': ['mean', 'std'],
            'status': lambda x: (x >= 400).mean()
        }).fillna(0)
        
        user_stats.columns = [f'user_{col[0]}_{col[1]}' if col[1] else f'user_{col[0]}' for col in user_stats.columns]
        df = df.merge(user_stats, left_on='user_id', right_index=True, how='left').fillna(0)
        
        # Select numerical features for neural networks
        feature_columns = [
            'status', 'response_time', 'size', 'hour', 'day_of_week',
            'is_weekend', 'is_business_hours', 'method_encoded', 'user_agent_encoded',
            'log_response_time', 'log_size', 'status_group', 'risk_score',
            'user_response_time_mean', 'user_response_time_std',
            'user_size_mean', 'user_size_std', 'user_status_<lambda>'
        ]
        
        # Handle missing columns
        available_features = [col for col in feature_columns if col in df.columns]
        missing_features = [col for col in feature_columns if col not in df.columns]
        
        if missing_features:
            print(f"⚠️ Missing features: {missing_features}")
            for col in missing_features:
                df[col] = 0
        
        print(f"✅ Engineered {len(available_features)} advanced features")
        return df, available_features

    def prepare_sequences(self, X, y):
        """Prepare sequences for LSTM training"""
        print("📊 Preparing sequences for LSTM training...")
        
        sequences_X = []
        sequences_y = []
        
        for i in range(len(X) - self.sequence_length + 1):
            sequences_X.append(X.iloc[i:i + self.sequence_length].values)
            sequences_y.append(y.iloc[i + self.sequence_length - 1])
        
        sequences_X = np.array(sequences_X)
        sequences_y = np.array(sequences_y)
        
        print(f"✅ Created {len(sequences_X)} sequences of length {self.sequence_length}")
        return sequences_X, sequences_y

    def _build_lstm_model(self, input_shape):
        """Build LSTM neural network"""
        print("🧠 Creating LSTM neural network...")
        
        model = Sequential([
            LSTM(128, return_sequences=True, input_shape=input_shape),
            BatchNormalization(),
            Dropout(0.3),
            LSTM(64, return_sequences=False),
            BatchNormalization(),
            Dropout(0.3),
            Dense(32, activation='relu'),
            Dropout(0.2),
            Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', 'precision', 'recall']
        )
        
        return model

    def _build_cnn_model(self, input_shape):
        """Build CNN neural network"""
        print("🧠 Creating CNN neural network...")
        
        model = Sequential([
            Conv1D(filters=64, kernel_size=3, activation='relu', input_shape=input_shape),
            BatchNormalization(),
            MaxPooling1D(pool_size=2),
            Dropout(0.3),
            Conv1D(filters=32, kernel_size=3, activation='relu'),
            BatchNormalization(),
            MaxPooling1D(pool_size=2),
            Dropout(0.3),
            Flatten(),
            Dense(32, activation='relu'),
            Dropout(0.2),
            Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', 'precision', 'recall']
        )
        
        return model

    def _build_hybrid_model(self, input_shape):
        """Build hybrid LSTM+CNN neural network"""
        print("🧠 Creating Hybrid LSTM+CNN neural network...")
        
        # Input layer
        input_layer = Input(shape=input_shape)
        
        # LSTM branch
        lstm_branch = LSTM(64, return_sequences=True)(input_layer)
        lstm_branch = BatchNormalization()(lstm_branch)
        lstm_branch = Dropout(0.3)(lstm_branch)
        lstm_branch = LSTM(32, return_sequences=False)(lstm_branch)
        lstm_branch = BatchNormalization()(lstm_branch)
        lstm_branch = Dropout(0.2)(lstm_branch)
        
        # CNN branch
        cnn_branch = Conv1D(filters=32, kernel_size=3, activation='relu')(input_layer)
        cnn_branch = BatchNormalization()(cnn_branch)
        cnn_branch = MaxPooling1D(pool_size=2)(cnn_branch)
        cnn_branch = Dropout(0.3)(cnn_branch)
        cnn_branch = Flatten()(cnn_branch)
        
        # Combine branches
        combined = Concatenate()([lstm_branch, cnn_branch])
        combined = Dense(32, activation='relu')(combined)
        combined = Dropout(0.2)(combined)
        output = Dense(1, activation='sigmoid')(combined)
        
        model = Model(inputs=input_layer, outputs=output)
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', 'precision', 'recall']
        )
        
        return model

    def train_neural_models(self, df, feature_columns):
        """Train all neural network models"""
        print("🚀 Training Advanced Neural Networks...")
        
        # Prepare features and target
        X = df[feature_columns].fillna(0)
        y = df['is_threat']
        
        # Scale features
        if 'neural_scaler' not in self.scalers:
            self.scalers['neural_scaler'] = StandardScaler()
            X_scaled = self.scalers['neural_scaler'].fit_transform(X)
        else:
            X_scaled = self.scalers['neural_scaler'].transform(X)
        
        # Prepare sequences for neural networks
        X_seq, y_seq = self.prepare_sequences(pd.DataFrame(X_scaled), pd.Series(y.values))
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X_seq, y_seq, test_size=0.2, random_state=42, stratify=y_seq
        )
        
        print(f"📊 Training set: {len(X_train)} sequences")
        print(f"📊 Test set: {len(X_test)} sequences")
        
        # Callbacks
        early_stopping = EarlyStopping(
            monitor='val_loss', patience=10, restore_best_weights=True, verbose=0
        )
        lr_scheduler = ReduceLROnPlateau(
            monitor='val_loss', factor=0.5, patience=5, verbose=0, min_lr=1e-6
        )
        
        results = {}
        
        # Train each model
        for model_name, build_func in self.architectures.items():
            print(f"\n🧠 Training {model_name.upper()} Model...")
            
            # Build model
            input_shape = (X_train.shape[1], X_train.shape[2])
            model = build_func(input_shape)
            
            # Train model with reduced verbosity
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                history = model.fit(
                    X_train, y_train,
                    validation_data=(X_test, y_test),
                    epochs=50,
                    batch_size=32,
                    callbacks=[early_stopping, lr_scheduler],
                    verbose=1  # Reduced verbosity
                )
            
            # Evaluate model
            y_pred = (model.predict(X_test, verbose=0) > 0.5).astype(int)
            accuracy = accuracy_score(y_test, y_pred)
            
            print(f"✅ {model_name.upper()} Accuracy: {accuracy:.3f}")
            
            # Store model and results
            self.models[model_name] = model
            results[model_name] = accuracy
        
        # Create ensemble
        ensemble_predictions = []
        for model_name, model in self.models.items():
            pred = model.predict(X_test, verbose=0)
            ensemble_predictions.append(pred.flatten())
        
        # Average ensemble
        ensemble_pred = np.mean(ensemble_predictions, axis=0)
        ensemble_pred_binary = (ensemble_pred > 0.5).astype(int)
        ensemble_accuracy = accuracy_score(y_test, ensemble_pred_binary)
        
        print(f"✅ Neural Ensemble Accuracy: {ensemble_accuracy:.3f}")
        results['ensemble'] = ensemble_accuracy
        
        return results

    def save_models(self, timestamp=None):
        """Save neural network models"""
        print("💾 Saving neural network models...")
        
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        saved_models = []
        
        # Save neural network models (.h5 format with warning suppression)
        for model_name, model in self.models.items():
            model_path = f"{self.models_dir}/neural_{model_name}_{timestamp}.h5"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model.save(model_path)
            saved_models.append(f"neural_{model_name}_{timestamp}.h5")
            print(f"✅ Saved {model_name} model: {model_path}")
        
        # Save scalers and encoders
        scalers_path = f"{self.models_dir}/neural_scalers_{timestamp}.joblib"
        encoders_path = f"{self.models_dir}/neural_encoders_{timestamp}.joblib"
        
        joblib.dump(self.scalers, scalers_path)
        joblib.dump(self.encoders, encoders_path)
        
        print(f"✅ Neural models saved with timestamp: {timestamp}")
        return timestamp, saved_models

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='UEBA Advanced Neural Network Threat Detector')
    parser.add_argument('--size', type=int, default=1000, help='Number of records to process')
    parser.add_argument('--models', nargs='+', default=['lstm', 'cnn', 'hybrid'], 
                       help='Models to train')
    
    args = parser.parse_args()
    
    print("🚀 ADVANCED NEURAL NETWORK TRAINING PIPELINE")
    print("=" * 70)
    
    # Initialize detector
    detector = AdvancedNeuralThreatDetector()
    
    # Load and process data
    df = detector.load_data(size=args.size)
    df, feature_columns = detector.engineer_features(df)
    
    # Train neural models
    results = detector.train_neural_models(df, feature_columns)
    
    # Save models
    timestamp, saved_models = detector.save_models()
    
    # Print summary
    print(f"\n🧠 NEURAL NETWORK RESULTS SUMMARY")
    print("=" * 70)
    for model_name, accuracy in results.items():
        if model_name == 'ensemble':
            print(f"🎯 Neural Ensemble: {accuracy:.3f} accuracy")
        else:
            print(f"🧠 {model_name.upper()} Network: {accuracy:.3f} accuracy")
    
    print(f"💾 Models saved with timestamp: {timestamp}")
    print("=" * 70)

if __name__ == "__main__":
    main()