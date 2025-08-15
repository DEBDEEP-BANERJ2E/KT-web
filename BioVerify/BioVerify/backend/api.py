"""
FastAPI backend for Behavioral Biometrics System
"""

import os
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
import pandas as pd
import requests

from backend.models import (
    User, BiometricSample, AuthenticationScore, SecurityEvent,
    ModelMetadata, SystemMetrics, get_db, init_db
)
from backend.ml_engine import ml_engine
from backend.notifications import notification_service
from backend.drive_storage import drive_service
from config import config
from utils.helpers import generate_qr_code, export_to_csv, validate_features

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="Behavioral Biometrics API",
    description="Real-time behavioral biometrics authentication system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models
class UserRegistration(BaseModel):
    user_id: str
    email: Optional[str] = None
    full_name: Optional[str] = None

class BiometricFeatures(BaseModel):
    user_id: str
    features: Dict[str, float]
    device_info: Optional[Dict] = None
    typingdna_pattern: Optional[Dict] = None

class AuthenticationRequest(BaseModel):
    user_id: str
    features: Dict[str, float]
    session_id: Optional[str] = None
    device_info: Optional[Dict] = None
    typingdna_pattern: Optional[Dict] = None

class LabelRequest(BaseModel):
    user_id: str
    features: Dict[str, float]
    label: int  # 1 = genuine, 0 = impostor
    device_info: Optional[Dict] = None

class TypingDNARequest(BaseModel):
    user_id: str
    typing_pattern: str
    text_id: str
    quality: Optional[int] = None

# TypingDNA Integration
class TypingDNAService:
    """Service for TypingDNA API integration"""
    
    def __init__(self):
        self.api_key = config.TYPINGDNA_API_KEY
        self.api_secret = config.TYPINGDNA_API_SECRET
        self.base_url = config.TYPINGDNA_BASE_URL
        self.enabled = bool(self.api_key and self.api_secret)
    
    def save_pattern(self, user_id: str, typing_pattern: str) -> Dict:
        """Save typing pattern to TypingDNA"""
        if not self.enabled:
            return {"success": False, "message": "TypingDNA not configured"}
        
        try:
            url = f"{self.base_url}/save/{user_id}"
            response = requests.post(
                url,
                auth=(self.api_key, self.api_secret),
                data={"tp": typing_pattern}
            )
            return response.json()
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def verify_pattern(self, user_id: str, typing_pattern: str) -> Dict:
        """Verify typing pattern against saved patterns"""
        if not self.enabled:
            return {"success": False, "message": "TypingDNA not configured"}
        
        try:
            url = f"{self.base_url}/verify/{user_id}"
            response = requests.post(
                url,
                auth=(self.api_key, self.api_secret),
                data={"tp": typing_pattern}
            )
            return response.json()
        except Exception as e:
            return {"success": False, "message": str(e)}

typingdna_service = TypingDNAService()

# API Endpoints

@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "active",
        "service": "Behavioral Biometrics API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/config")
async def get_config():
    """Get system configuration status"""
    return {
        "config_status": config.validate_config(),
        "features": config.FEATURES,
        "thresholds": {
            "score_threshold": config.SCORE_THRESHOLD,
            "impostor_threshold": config.IMPOSTOR_THRESHOLD,
            "min_enrollments": config.USER_ENROLL_MIN_POSITIVES
        }
    }

@app.post("/register")
async def register_user(user_data: UserRegistration, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.user_id == user_data.user_id).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create new user
    user = User(
        user_id=user_data.user_id,
        email=user_data.email,
        full_name=user_data.full_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "status": "success",
        "message": "User registered successfully",
        "user_id": user.user_id
    }

@app.post("/enroll")
async def enroll_user(
    enrollment: BiometricFeatures,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Enroll user biometric features"""
    # Validate features
    if not validate_features(enrollment.features):
        raise HTTPException(status_code=400, detail="Invalid feature format")
    
    # Create biometric sample
    sample = BiometricSample(
        user_id=enrollment.user_id,
        label=1,  # Enrollment samples are always genuine
        source="enrollment",
        device_info=enrollment.device_info,
        typingdna_pattern=enrollment.typingdna_pattern
    )
    
    # Set feature values
    for feature in config.FEATURES:
        if hasattr(sample, feature):
            setattr(sample, feature, enrollment.features.get(feature, 0.0))
    
    db.add(sample)
    db.commit()
    
    # Check if we can train models
    can_train, message = ml_engine.can_train_model(db, enrollment.user_id)
    train_info = None
    
    if can_train:
        # Train models in background
        background_tasks.add_task(train_user_models_bg, enrollment.user_id)
        train_info = "Model training initiated"
    else:
        train_info = message
    
    # Get enrollment count
    enrollment_count = db.query(BiometricSample).filter(
        BiometricSample.user_id == enrollment.user_id,
        BiometricSample.label == 1
    ).count()
    
    return {
        "status": "enrolled",
        "user_id": enrollment.user_id,
        "enrollment_count": enrollment_count,
        "train_info": train_info,
        "can_authenticate": enrollment_count >= config.USER_ENROLL_MIN_POSITIVES
    }

@app.post("/authenticate")
async def authenticate_user(
    auth_request: AuthenticationRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Authenticate user using behavioral biometrics"""
    # Check if user exists and has enough enrollments
    enrollment_count = db.query(BiometricSample).filter(
        BiometricSample.user_id == auth_request.user_id,
        BiometricSample.label == 1
    ).count()
    
    if enrollment_count < config.USER_ENROLL_MIN_POSITIVES:
        return {
            "status": "insufficient_enrollment",
            "message": f"Need at least {config.USER_ENROLL_MIN_POSITIVES} enrollments",
            "current_enrollments": enrollment_count
        }
    
    # Validate features
    if not validate_features(auth_request.features):
        raise HTTPException(status_code=400, detail="Invalid feature format")
    
    # Score using ML models
    score_result = ml_engine.score_features(auth_request.user_id, auth_request.features)
    if score_result is None:
        return {
            "status": "model_not_ready",
            "message": "Authentication model not available"
        }
    
    # TypingDNA verification if available
    typingdna_score = None
    if auth_request.typingdna_pattern and typingdna_service.enabled:
        typingdna_result = typingdna_service.verify_pattern(
            auth_request.user_id,
            auth_request.typingdna_pattern.get("pattern", "")
        )
        if typingdna_result.get("success"):
            typingdna_score = typingdna_result.get("result", 0) / 100.0
    
    # Combine scores
    final_score = score_result['prob_avg']
    if typingdna_score is not None:
        final_score = (final_score + typingdna_score) / 2.0
    
    # Update verdict based on final score
    if final_score >= config.SCORE_THRESHOLD:
        verdict = "genuine"
        risk_level = "low"
    elif final_score >= config.IMPOSTOR_THRESHOLD:
        verdict = "uncertain"
        risk_level = "medium"
    else:
        verdict = "impostor"
        risk_level = "high"
    
    # Log authentication attempt
    auth_score = AuthenticationScore(
        user_id=auth_request.user_id,
        prob_knn=score_result['prob_knn'],
        prob_svm=score_result['prob_svm'],
        prob_avg=score_result['prob_avg'],
        typingdna_score=typingdna_score,
        final_score=final_score,
        verdict=verdict,
        confidence=score_result['confidence'],
        risk_level=risk_level,
        session_id=auth_request.session_id or str(uuid.uuid4()),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", ""),
        features_used=auth_request.features
    )
    db.add(auth_score)
    db.commit()
    
    # Handle security events
    if verdict == "impostor" or risk_level in ["high", "critical"]:
        background_tasks.add_task(
            handle_security_event,
            auth_request.user_id,
            "impostor_detected" if verdict == "impostor" else "high_risk_access",
            {
                "final_score": final_score,
                "verdict": verdict,
                "risk_level": risk_level,
                "ip_address": request.client.host
            }
        )
    
    response = {
        "status": "authenticated",
        "user_id": auth_request.user_id,
        "verdict": verdict,
        "confidence": score_result['confidence'],
        "risk_level": risk_level,
        "final_score": final_score,
        "scores": {
            "ml_average": score_result['prob_avg'],
            "knn": score_result['prob_knn'],
            "svm": score_result['prob_svm'],
            "typingdna": typingdna_score
        },
        "requires_step_up": verdict == "impostor" or risk_level == "high"
    }
    
    return response

@app.post("/label")
async def label_sample(
    label_request: LabelRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Label a sample as genuine or impostor"""
    # Validate features
    if not validate_features(label_request.features):
        raise HTTPException(status_code=400, detail="Invalid feature format")
    
    # Create labeled sample
    sample = BiometricSample(
        user_id=label_request.user_id,
        label=label_request.label,
        source="manual_label",
        device_info=label_request.device_info
    )
    
    # Set feature values
    for feature in config.FEATURES:
        if hasattr(sample, feature):
            setattr(sample, feature, label_request.features.get(feature, 0.0))
    
    db.add(sample)
    db.commit()
    
    # Retrain models if we have enough data
    can_train, message = ml_engine.can_train_model(db, label_request.user_id)
    if can_train:
        background_tasks.add_task(train_user_models_bg, label_request.user_id)
    
    # Get sample counts
    positive_count = db.query(BiometricSample).filter(
        BiometricSample.user_id == label_request.user_id,
        BiometricSample.label == 1
    ).count()
    
    negative_count = db.query(BiometricSample).filter(
        BiometricSample.user_id == label_request.user_id,
        BiometricSample.label == 0
    ).count()
    
    return {
        "status": "labeled",
        "user_id": label_request.user_id,
        "label": label_request.label,
        "sample_counts": {
            "positive": positive_count,
            "negative": negative_count
        },
        "training_status": message
    }

@app.post("/typingdna/save")
async def save_typing_pattern(pattern_request: TypingDNARequest, db: Session = Depends(get_db)):
    """Save typing pattern to TypingDNA"""
    if not typingdna_service.enabled:
        raise HTTPException(status_code=503, detail="TypingDNA service not configured")
    
    result = typingdna_service.save_pattern(
        pattern_request.user_id,
        pattern_request.typing_pattern
    )
    
    return result

@app.post("/typingdna/verify")
async def verify_typing_pattern(pattern_request: TypingDNARequest, db: Session = Depends(get_db)):
    """Verify typing pattern against TypingDNA"""
    if not typingdna_service.enabled:
        raise HTTPException(status_code=503, detail="TypingDNA service not configured")
    
    result = typingdna_service.verify_pattern(
        pattern_request.user_id,
        pattern_request.typing_pattern
    )
    
    return result

@app.get("/users")
async def get_users(db: Session = Depends(get_db)):
    """Get list of all users"""
    users = db.query(User).all()
    return {
        "users": [
            {
                "user_id": user.user_id,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
            for user in users
        ]
    }

@app.get("/users/{user_id}/stats")
async def get_user_stats(user_id: str, db: Session = Depends(get_db)):
    """Get statistics for a specific user"""
    # Sample counts
    positive_samples = db.query(BiometricSample).filter(
        BiometricSample.user_id == user_id,
        BiometricSample.label == 1
    ).count()
    
    negative_samples = db.query(BiometricSample).filter(
        BiometricSample.user_id == user_id,
        BiometricSample.label == 0
    ).count()
    
    # Authentication history
    recent_auths = db.query(AuthenticationScore).filter(
        AuthenticationScore.user_id == user_id
    ).order_by(AuthenticationScore.created_at.desc()).limit(10).all()
    
    # Model stats
    model_stats = ml_engine.get_model_stats(db, user_id)
    
    return {
        "user_id": user_id,
        "sample_counts": {
            "positive": positive_samples,
            "negative": negative_samples,
            "total": positive_samples + negative_samples
        },
        "recent_authentications": [
            {
                "timestamp": auth.created_at.isoformat(),
                "verdict": auth.verdict,
                "confidence": auth.confidence,
                "risk_level": auth.risk_level,
                "final_score": auth.final_score
            }
            for auth in recent_auths
        ],
        "model_stats": model_stats
    }

@app.get("/users/{user_id}/metrics")
async def get_user_metrics(user_id: str, db: Session = Depends(get_db)):
    """Get authentication metrics for a user"""
    # Get authentication history
    auth_history = db.query(AuthenticationScore).filter(
        AuthenticationScore.user_id == user_id
    ).order_by(AuthenticationScore.created_at.asc()).all()
    
    if not auth_history:
        return {
            "user_id": user_id,
            "metrics": {
                "timestamps": [],
                "scores": [],
                "verdicts": [],
                "risk_levels": []
            }
        }
    
    return {
        "user_id": user_id,
        "metrics": {
            "timestamps": [auth.created_at.isoformat() for auth in auth_history],
            "scores": [auth.final_score for auth in auth_history],
            "verdicts": [auth.verdict for auth in auth_history],
            "risk_levels": [auth.risk_level for auth in auth_history]
        }
    }

@app.post("/users/{user_id}/retrain")
async def retrain_user_models(
    user_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Manually retrain models for a user"""
    can_train, message = ml_engine.can_train_model(db, user_id)
    
    if not can_train:
        raise HTTPException(status_code=400, detail=message)
    
    # Start training in background
    background_tasks.add_task(train_user_models_bg, user_id)
    
    return {
        "status": "training_started",
        "user_id": user_id,
        "message": "Model retraining initiated"
    }

@app.get("/export/{data_type}")
async def export_data(data_type: str, user_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Export data to CSV"""
    if data_type not in ["samples", "scores", "users"]:
        raise HTTPException(status_code=400, detail="Invalid data type")
    
    try:
        filename = export_to_csv(db, data_type, user_id)
        return FileResponse(
            filename,
            media_type="text/csv",
            filename=os.path.basename(filename)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/qr-code")
async def get_qr_code():
    """Generate QR code for mobile access"""
    # Get the current server URL (you might want to make this configurable)
    qr_data = "http://localhost:5000"  # Gradio frontend URL
    qr_image = generate_qr_code(qr_data)
    
    return {"qr_code": qr_image, "url": qr_data}

# Background tasks
async def train_user_models_bg(user_id: str):
    """Background task to train user models"""
    db = next(get_db())
    try:
        success, message, metadata = ml_engine.train_user_models(db, user_id)
        print(f"Model training for {user_id}: {message}")
        
        # Sync to Google Drive if enabled
        if config.GOOGLE_DRIVE_ENABLED and success:
            drive_service.sync_user_models(user_id)
            
    except Exception as e:
        print(f"Error training models for {user_id}: {e}")
    finally:
        db.close()

async def handle_security_event(user_id: str, event_type: str, metadata: Dict):
    """Handle security events and send notifications"""
    db = next(get_db())
    try:
        # Create security event
        event = SecurityEvent(
            user_id=user_id,
            event_type=event_type,
            severity="high" if event_type == "impostor_detected" else "medium",
            description=f"Security event: {event_type}",
            metadata=metadata
        )
        db.add(event)
        db.commit()
        
        # Send notifications
        notification_service.send_security_alert(user_id, event_type, metadata)
        
    except Exception as e:
        print(f"Error handling security event: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
