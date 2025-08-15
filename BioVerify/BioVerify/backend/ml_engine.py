"""
Machine Learning Engine for Behavioral Biometrics
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Tuple, Optional, List
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
from sqlalchemy.orm import Session

from backend.models import BiometricSample, ModelMetadata, get_db
from config import config

class BiometricMLEngine:
    """Machine Learning engine for behavioral biometrics"""
    
    def __init__(self):
        self.features = config.FEATURES
        self.models_dir = config.MODELS_DIR
        os.makedirs(self.models_dir, exist_ok=True)
    
    def extract_features_from_sample(self, sample: BiometricSample) -> Dict[str, float]:
        """Extract feature vector from a biometric sample"""
        features = {}
        for feature in self.features:
            features[feature] = getattr(sample, feature, 0.0)
        return features
    
    def get_training_data(self, session: Session, user_id: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Get positive and negative training samples for a user"""
        # Get positive samples (genuine user)
        positive_samples = session.query(BiometricSample).filter(
            BiometricSample.user_id == user_id,
            BiometricSample.label == 1
        ).all()
        
        # Get negative samples (other users + labeled impostors)
        other_users = session.query(BiometricSample).filter(
            BiometricSample.user_id != user_id,
            BiometricSample.label == 1
        ).all()
        
        user_impostors = session.query(BiometricSample).filter(
            BiometricSample.user_id == user_id,
            BiometricSample.label == 0
        ).all()
        
        negative_samples = other_users + user_impostors
        
        # Convert to DataFrames
        def samples_to_df(samples):
            if not samples:
                return pd.DataFrame(columns=self.features)
            
            data = []
            for sample in samples:
                row = {}
                for feature in self.features:
                    row[feature] = getattr(sample, feature, 0.0)
                data.append(row)
            return pd.DataFrame(data)
        
        X_pos = samples_to_df(positive_samples)
        X_neg = samples_to_df(negative_samples)
        
        return X_pos, X_neg
    
    def can_train_model(self, session: Session, user_id: str) -> Tuple[bool, str]:
        """Check if we have enough data to train a model"""
        pos_count = session.query(BiometricSample).filter(
            BiometricSample.user_id == user_id,
            BiometricSample.label == 1
        ).count()
        
        neg_count = session.query(BiometricSample).filter(
            BiometricSample.user_id != user_id,
            BiometricSample.label == 1
        ).count() + session.query(BiometricSample).filter(
            BiometricSample.user_id == user_id,
            BiometricSample.label == 0
        ).count()
        
        if pos_count < config.USER_ENROLL_MIN_POSITIVES:
            return False, f"Need at least {config.USER_ENROLL_MIN_POSITIVES} positive samples (have {pos_count})"
        
        if neg_count < 1:
            return False, "Need at least 1 negative sample for training"
        
        return True, f"Ready to train: {pos_count} positive, {neg_count} negative samples"
    
    def train_user_models(self, session: Session, user_id: str) -> Tuple[bool, str, Dict]:
        """Train ML models for a specific user"""
        try:
            # Check if we can train
            can_train, message = self.can_train_model(session, user_id)
            if not can_train:
                return False, message, {}
            
            # Get training data
            X_pos, X_neg = self.get_training_data(session, user_id)
            
            if X_pos.empty:
                return False, "No positive samples available", {}
            
            if X_neg.empty:
                return False, "No negative samples available", {}
            
            # Prepare training dataset
            X_pos['label'] = 1
            X_neg['label'] = 0
            df = pd.concat([X_pos, X_neg], ignore_index=True)
            
            X = df[self.features].fillna(0.0).values
            y = df['label'].values.astype(int)
            
            if len(np.unique(y)) < 2:
                return False, "Need both positive and negative samples", {}
            
            # Train models
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # KNN Classifier
            knn = KNeighborsClassifier(n_neighbors=min(config.KNN_NEIGHBORS, len(X) - 1))
            knn.fit(X_scaled, y)
            
            # SVM Classifier
            svm = SVC(kernel=config.SVM_KERNEL, probability=True, random_state=42)
            svm.fit(X_scaled, y)
            
            # Calculate performance metrics
            knn_scores = cross_val_score(knn, X_scaled, y, cv=min(3, len(X)))
            svm_scores = cross_val_score(svm, X_scaled, y, cv=min(3, len(X)))
            
            # Save models
            model_paths = config.get_model_paths(user_id)
            joblib.dump(scaler, model_paths['scaler'])
            joblib.dump(knn, model_paths['knn'])
            joblib.dump(svm, model_paths['svm'])
            
            # Save metadata
            metadata = {
                'user_id': user_id,
                'training_timestamp': datetime.utcnow().isoformat(),
                'positive_samples': len(X_pos),
                'negative_samples': len(X_neg),
                'total_samples': len(X),
                'knn_cv_score': float(np.mean(knn_scores)),
                'svm_cv_score': float(np.mean(svm_scores)),
                'features': self.features,
                'model_version': '1.0'
            }
            
            with open(model_paths['metadata'], 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Update database
            model_meta = ModelMetadata(
                user_id=user_id,
                model_version='1.0',
                training_samples=len(X),
                positive_samples=len(X_pos),
                negative_samples=len(X_neg),
                accuracy=float(np.mean(svm_scores)),
                scaler_path=model_paths['scaler'],
                knn_path=model_paths['knn'],
                svm_path=model_paths['svm'],
                training_params=json.dumps({
                    'knn_neighbors': config.KNN_NEIGHBORS,
                    'svm_kernel': config.SVM_KERNEL,
                    'features': self.features
                })
            )
            session.add(model_meta)
            session.commit()
            
            return True, f"Models trained successfully: KNN CV={np.mean(knn_scores):.3f}, SVM CV={np.mean(svm_scores):.3f}", metadata
            
        except Exception as e:
            return False, f"Training failed: {str(e)}", {}
    
    def load_user_models(self, user_id: str) -> Tuple[Optional[StandardScaler], Optional[KNeighborsClassifier], Optional[SVC]]:
        """Load trained models for a user"""
        try:
            model_paths = config.get_model_paths(user_id)
            
            if not all(os.path.exists(path) for path in [model_paths['scaler'], model_paths['knn'], model_paths['svm']]):
                return None, None, None
            
            scaler = joblib.load(model_paths['scaler'])
            knn = joblib.load(model_paths['knn'])
            svm = joblib.load(model_paths['svm'])
            
            return scaler, knn, svm
            
        except Exception as e:
            print(f"Error loading models for {user_id}: {e}")
            return None, None, None
    
    def score_features(self, user_id: str, features: Dict[str, float]) -> Optional[Dict]:
        """Score feature vector using trained models"""
        try:
            # Load models
            scaler, knn, svm = self.load_user_models(user_id)
            if scaler is None:
                return None
            
            # Prepare feature vector
            feature_vector = np.array([[features.get(f, 0.0) for f in self.features]])
            feature_vector_scaled = scaler.transform(feature_vector)
            
            # Get predictions
            knn_prob = float(knn.predict_proba(feature_vector_scaled)[0][1])
            svm_prob = float(svm.predict_proba(feature_vector_scaled)[0][1])
            
            # Calculate average score
            avg_prob = (knn_prob + svm_prob) / 2.0
            
            # Determine verdict and risk level
            if avg_prob >= config.SCORE_THRESHOLD:
                verdict = "genuine"
                risk_level = "low"
            elif avg_prob >= config.IMPOSTOR_THRESHOLD:
                verdict = "uncertain"
                risk_level = "medium"
            else:
                verdict = "impostor"
                risk_level = "high"
            
            # Calculate confidence
            confidence = abs(avg_prob - 0.5) * 2.0  # 0 to 1 scale
            
            return {
                'prob_knn': knn_prob,
                'prob_svm': svm_prob,
                'prob_avg': avg_prob,
                'final_score': avg_prob,
                'verdict': verdict,
                'confidence': confidence,
                'risk_level': risk_level
            }
            
        except Exception as e:
            print(f"Error scoring features for {user_id}: {e}")
            return None
    
    def get_model_stats(self, session: Session, user_id: str) -> Dict:
        """Get model statistics and performance"""
        try:
            # Load metadata
            model_paths = config.get_model_paths(user_id)
            if not os.path.exists(model_paths['metadata']):
                return {}
            
            with open(model_paths['metadata'], 'r') as f:
                metadata = json.load(f)
            
            # Get recent performance from database
            recent_scores = session.query(BiometricSample).filter(
                BiometricSample.user_id == user_id
            ).order_by(BiometricSample.created_at.desc()).limit(100).all()
            
            stats = {
                'model_metadata': metadata,
                'recent_samples': len(recent_scores),
                'last_training': metadata.get('training_timestamp', 'Unknown'),
                'model_exists': True
            }
            
            return stats
            
        except Exception as e:
            return {'error': str(e), 'model_exists': False}

# Global ML engine instance
ml_engine = BiometricMLEngine()
