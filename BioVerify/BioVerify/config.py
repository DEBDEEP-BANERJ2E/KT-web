"""
Configuration settings for the Behavioral Biometrics System
"""

import os
from typing import Dict, Any

class Config:
    """Application configuration"""
    
    # Database settings
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./biometrics.db")
    
    # TypingDNA API settings
    TYPINGDNA_API_KEY = os.getenv("TYPINGDNA_API_KEY", "")
    TYPINGDNA_API_SECRET = os.getenv("TYPINGDNA_API_SECRET", "")
    TYPINGDNA_BASE_URL = "https://api.typingdna.com"
    
    # Google Drive settings for model persistence
    GOOGLE_DRIVE_ENABLED = os.getenv("GOOGLE_DRIVE_ENABLED", "false").lower() == "true"
    GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")
    
    # Email notification settings
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_USER = os.getenv("EMAIL_USER", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")
    
    # Webhook settings
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
    
    # ML Model settings
    USER_ENROLL_MIN_POSITIVES = int(os.getenv("USER_ENROLL_MIN_POSITIVES", "3"))
    KNN_NEIGHBORS = int(os.getenv("KNN_NEIGHBORS", "5"))
    SVM_KERNEL = os.getenv("SVM_KERNEL", "rbf")
    SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD", "0.60"))
    IMPOSTOR_THRESHOLD = float(os.getenv("IMPOSTOR_THRESHOLD", "0.30"))
    
    # Security settings
    SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
    MAX_FAILED_ATTEMPTS = int(os.getenv("MAX_FAILED_ATTEMPTS", "3"))
    LOCKOUT_DURATION = int(os.getenv("LOCKOUT_DURATION", "300"))  # 5 minutes
    
    # Feature extraction settings
    FEATURES = [
        "dwell_mean", "dwell_std", "flight_mean", "flight_std",
        "key_count", "session_time", "pressure_mean", "swipe_vel",
        "gyro_x", "gyro_y", "gyro_z", "typing_speed", "rhythm_consistency"
    ]
    
    # Directories
    MODELS_DIR = "./models"
    DATA_DIR = "./data"
    EXPORTS_DIR = "./exports"
    LOGS_DIR = "./logs"
    
    @classmethod
    def get_model_paths(cls, user_id: str) -> Dict[str, str]:
        """Get model file paths for a specific user"""
        safe_id = user_id.replace("/", "_").replace("\\", "_")
        return {
            "scaler": os.path.join(cls.MODELS_DIR, f"{safe_id}_scaler.pkl"),
            "knn": os.path.join(cls.MODELS_DIR, f"{safe_id}_knn.pkl"),
            "svm": os.path.join(cls.MODELS_DIR, f"{safe_id}_svm.pkl"),
            "metadata": os.path.join(cls.MODELS_DIR, f"{safe_id}_metadata.json")
        }
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """Validate configuration and return status"""
        status = {
            "database": bool(cls.DATABASE_URL),
            "typingdna": bool(cls.TYPINGDNA_API_KEY and cls.TYPINGDNA_API_SECRET),
            "email": bool(cls.EMAIL_USER and cls.EMAIL_PASSWORD),
            "webhook": bool(cls.WEBHOOK_URL),
            "google_drive": cls.GOOGLE_DRIVE_ENABLED
        }
        return status

# Global config instance
config = Config()
