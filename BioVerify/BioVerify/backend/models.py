"""
Database models for the Behavioral Biometrics System
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func
from config import config

# Database setup
engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {}
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class User(Base):
    """User management table"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)

class BiometricSample(Base):
    """Biometric feature samples"""
    __tablename__ = "biometric_samples"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), index=True, nullable=False)
    
    # Typing dynamics features
    dwell_mean = Column(Float, default=0.0)
    dwell_std = Column(Float, default=0.0)
    flight_mean = Column(Float, default=0.0)
    flight_std = Column(Float, default=0.0)
    key_count = Column(Float, default=0.0)
    session_time = Column(Float, default=0.0)
    typing_speed = Column(Float, default=0.0)
    rhythm_consistency = Column(Float, default=0.0)
    
    # Touch/gesture features
    pressure_mean = Column(Float, default=0.0)
    swipe_vel = Column(Float, default=0.0)
    
    # Device motion features
    gyro_x = Column(Float, default=0.0)
    gyro_y = Column(Float, default=0.0)
    gyro_z = Column(Float, default=0.0)
    
    # TypingDNA features (JSON storage)
    typingdna_pattern = Column(JSON)
    
    # Metadata
    label = Column(Integer, default=1)  # 1=genuine, 0=impostor
    source = Column(String(50), default="manual")  # manual, typingdna, continuous
    device_info = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuthenticationScore(Base):
    """Authentication scoring results"""
    __tablename__ = "authentication_scores"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), index=True, nullable=False)
    
    # Scoring results
    prob_knn = Column(Float)
    prob_svm = Column(Float)
    prob_avg = Column(Float)
    typingdna_score = Column(Float)
    final_score = Column(Float)
    
    # Decision
    verdict = Column(String(20))  # genuine, impostor, uncertain
    confidence = Column(Float)
    risk_level = Column(String(20))  # low, medium, high, critical
    
    # Context
    session_id = Column(String(255))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    features_used = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

class SecurityEvent(Base):
    """Security events and alerts"""
    __tablename__ = "security_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), index=True)
    event_type = Column(String(50), nullable=False)  # impostor_detected, account_locked, etc.
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    description = Column(Text)
    
    # Context data
    event_metadata = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Response tracking
    notification_sent = Column(Boolean, default=False)
    webhook_sent = Column(Boolean, default=False)
    resolved = Column(Boolean, default=False)
    resolved_by = Column(String(255))
    resolved_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class ModelMetadata(Base):
    """ML model training metadata"""
    __tablename__ = "model_metadata"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), index=True, nullable=False)
    
    # Training info
    model_version = Column(String(50))
    training_samples = Column(Integer)
    positive_samples = Column(Integer)
    negative_samples = Column(Integer)
    
    # Performance metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    
    # Model paths
    scaler_path = Column(String(500))
    knn_path = Column(String(500))
    svm_path = Column(String(500))
    
    # Training parameters
    training_params = Column(JSON)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemMetrics(Base):
    """System performance and usage metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float)
    metric_data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Create all tables
def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(engine)
    print("Database tables created successfully")

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
if __name__ == "__main__":
    init_db()
