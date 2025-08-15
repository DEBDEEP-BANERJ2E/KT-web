"""
Utility functions for the Behavioral Biometrics System
"""

import os
import io
import csv
import base64
import hashlib
import secrets
import qrcode
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from PIL import Image
from sqlalchemy.orm import Session
from backend.models import BiometricSample, AuthenticationScore, User
from config import config

def validate_features(features: Dict[str, Any]) -> bool:
    """Validate biometric features"""
    if not isinstance(features, dict):
        return False
    
    # Check if all required features are present and numeric
    for feature in config.FEATURES:
        if feature not in features:
            continue  # Optional features
        
        value = features[feature]
        if not isinstance(value, (int, float)):
            try:
                float(value)
            except (ValueError, TypeError):
                return False
    
    return True

def generate_qr_code(data: str, size: int = 200) -> str:
    """Generate QR code and return as base64 string"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((size, size))
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_base64}"
        
    except Exception as e:
        print(f"Error generating QR code: {e}")
        return ""

def generate_otp(length: int = 6) -> str:
    """Generate a random OTP code"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(length)])

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def export_to_csv(db: Session, data_type: str, user_id: Optional[str] = None) -> str:
    """Export data to CSV file"""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(config.EXPORTS_DIR, f"{data_type}_{timestamp}.csv")
    
    os.makedirs(config.EXPORTS_DIR, exist_ok=True)
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        if data_type == "samples":
            writer = csv.writer(csvfile)
            
            # Header
            header = [
                'id', 'user_id', 'label', 'source', 'created_at'
            ] + config.FEATURES
            writer.writerow(header)
            
            # Query samples
            query = db.query(BiometricSample)
            if user_id:
                query = query.filter(BiometricSample.user_id == user_id)
            
            samples = query.all()
            
            # Write data
            for sample in samples:
                row = [
                    sample.id,
                    sample.user_id,
                    sample.label,
                    sample.source,
                    sample.created_at.isoformat() if sample.created_at else ''
                ]
                
                # Add feature values
                for feature in config.FEATURES:
                    row.append(getattr(sample, feature, 0.0))
                
                writer.writerow(row)
        
        elif data_type == "scores":
            writer = csv.writer(csvfile)
            
            # Header
            header = [
                'id', 'user_id', 'prob_knn', 'prob_svm', 'prob_avg',
                'typingdna_score', 'final_score', 'verdict', 'confidence',
                'risk_level', 'session_id', 'ip_address', 'created_at'
            ]
            writer.writerow(header)
            
            # Query scores
            query = db.query(AuthenticationScore)
            if user_id:
                query = query.filter(AuthenticationScore.user_id == user_id)
            
            scores = query.all()
            
            # Write data
            for score in scores:
                row = [
                    score.id,
                    score.user_id,
                    score.prob_knn,
                    score.prob_svm,
                    score.prob_avg,
                    score.typingdna_score,
                    score.final_score,
                    score.verdict,
                    score.confidence,
                    score.risk_level,
                    score.session_id,
                    score.ip_address,
                    score.created_at.isoformat() if score.created_at else ''
                ]
                writer.writerow(row)
        
        elif data_type == "users":
            writer = csv.writer(csvfile)
            
            # Header
            header = [
                'id', 'user_id', 'email', 'full_name', 'is_active',
                'created_at', 'last_login', 'failed_attempts'
            ]
            writer.writerow(header)
            
            # Query users
            users = db.query(User).all()
            
            # Write data
            for user in users:
                row = [
                    user.id,
                    user.user_id,
                    user.email,
                    user.full_name,
                    user.is_active,
                    user.created_at.isoformat() if user.created_at else '',
                    user.last_login.isoformat() if user.last_login else '',
                    user.failed_attempts
                ]
                writer.writerow(row)
    
    return filename

def calculate_risk_score(authentication_history: List[Dict]) -> Dict[str, Any]:
    """Calculate user risk score based on authentication history"""
    if not authentication_history:
        return {"risk_score": 0.5, "risk_level": "unknown", "factors": []}
    
    factors = []
    risk_score = 0.0
    
    # Analyze recent authentication attempts
    recent_attempts = authentication_history[-10:]  # Last 10 attempts
    
    # Factor 1: Failed authentication rate
    failed_count = sum(1 for auth in recent_attempts if auth.get('verdict') == 'impostor')
    failed_rate = failed_count / len(recent_attempts)
    risk_score += failed_rate * 0.4
    if failed_rate > 0.3:
        factors.append(f"High impostor detection rate: {failed_rate:.1%}")
    
    # Factor 2: Score consistency
    scores = [auth.get('final_score', 0.5) for auth in recent_attempts]
    if scores:
        score_variance = sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores)
        if score_variance > 0.1:
            risk_score += 0.2
            factors.append(f"Inconsistent authentication scores")
    
    # Factor 3: Time-based patterns
    timestamps = [auth.get('timestamp') for auth in recent_attempts if auth.get('timestamp')]
    if len(timestamps) > 3:
        # Check for unusual timing patterns
        time_diffs = []
        for i in range(1, len(timestamps)):
            try:
                t1 = datetime.fromisoformat(timestamps[i-1].replace('Z', '+00:00'))
                t2 = datetime.fromisoformat(timestamps[i].replace('Z', '+00:00'))
                diff = (t2 - t1).total_seconds()
                time_diffs.append(diff)
            except:
                continue
        
        if time_diffs:
            avg_diff = sum(time_diffs) / len(time_diffs)
            if avg_diff < 60:  # Very frequent attempts
                risk_score += 0.15
                factors.append("Unusually frequent authentication attempts")
    
    # Determine risk level
    if risk_score >= 0.7:
        risk_level = "critical"
    elif risk_score >= 0.5:
        risk_level = "high"
    elif risk_score >= 0.3:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    return {
        "risk_score": min(risk_score, 1.0),
        "risk_level": risk_level,
        "factors": factors,
        "analysis_count": len(recent_attempts)
    }

def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    # Remove or replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename

def get_client_ip(request) -> str:
    """Extract client IP address from request"""
    # Check for forwarded headers (when behind proxy)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    # Fallback to direct client host
    return getattr(request.client, 'host', 'unknown')

def create_session_id() -> str:
    """Create a unique session ID"""
    return secrets.token_urlsafe(32)

def is_mobile_device(user_agent: str) -> bool:
    """Detect if request is from mobile device"""
    mobile_indicators = [
        'Mobile', 'Android', 'iPhone', 'iPad', 'iPod',
        'BlackBerry', 'Windows Phone', 'webOS'
    ]
    
    return any(indicator in user_agent for indicator in mobile_indicators)

def log_system_event(event_type: str, details: Dict[str, Any]):
    """Log system events for monitoring"""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'details': details
    }
    
    # Write to log file
    log_file = os.path.join(config.LOGS_DIR, f"system_{datetime.utcnow().strftime('%Y%m%d')}.log")
    os.makedirs(config.LOGS_DIR, exist_ok=True)
    
    with open(log_file, 'a') as f:
        f.write(f"{log_entry}\n")
