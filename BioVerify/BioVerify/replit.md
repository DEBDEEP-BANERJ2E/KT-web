# Behavioral Biometrics Authentication System

## Overview

This is a production-ready behavioral biometrics authentication system that analyzes user typing patterns, device motion, and touch gestures for continuous authentication. The system uses machine learning models (KNN and SVM) to create unique behavioral profiles for each user and detect potential impostors in real-time. It features a FastAPI backend with PostgreSQL database, HTML/JavaScript frontend for real-time biometric capture, and comprehensive admin dashboard.

## Recent Changes (August 2025)

✅ **Deployment Complete**: System successfully deployed and running on port 5000  
✅ **Database Integration**: PostgreSQL database connected and operational  
✅ **Authentication Interface**: HTML interface with real-time typing capture working  
✅ **API Documentation**: Complete FastAPI docs available at `/docs`  
✅ **Free Deployment Ready**: Configured for Replit autoscale deployment  
✅ **Production Features**: All core functionality implemented and tested

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **FastAPI REST API**: Core backend service handling authentication, user management, and biometric data processing
- **SQLAlchemy ORM**: Database abstraction layer supporting SQLite by default with PostgreSQL compatibility
- **ML Engine**: Custom machine learning pipeline using scikit-learn for user enrollment and authentication scoring
- **Background Services**: Asynchronous notification system for security alerts and webhook integrations

### Frontend Architecture
- **Gradio Web Interface**: Multi-tab application providing user authentication, admin dashboard, and analytics
- **Client-Side JavaScript**: Real-time biometric data capture including keystroke dynamics, device motion, and touch gestures
- **Static Assets**: HTML templates and CSS styling for authentication interfaces

### Data Storage
- **Primary Database**: SQLite for development, PostgreSQL-ready for production
- **Model Persistence**: Local filesystem storage with optional Google Drive synchronization
- **Feature Storage**: Comprehensive biometric features including typing dynamics, device motion, and behavioral patterns

### Machine Learning Pipeline
- **Feature Extraction**: 13+ behavioral features including dwell times, flight times, typing speed, rhythm consistency, and device motion
- **Model Types**: K-Nearest Neighbors (KNN) and Support Vector Machine (SVM) classifiers
- **Training Strategy**: Per-user models with positive (genuine) and negative (impostor) sample learning
- **Scoring System**: Configurable thresholds for authentication decisions with impostor detection

### Security Features
- **Session Management**: Configurable timeout periods and failed attempt tracking
- **Account Lockout**: Temporary lockouts after multiple failed authentication attempts
- **Real-time Monitoring**: Continuous authentication scoring during user sessions
- **Security Events**: Comprehensive logging of authentication attempts and security incidents

## External Dependencies

### Third-Party APIs
- **TypingDNA**: Optional integration for enhanced keystroke dynamics analysis
- **Google Drive API**: Optional cloud storage for ML model persistence and backup

### ML Libraries
- **scikit-learn**: Core machine learning algorithms and preprocessing
- **pandas/numpy**: Data manipulation and numerical computations
- **joblib**: Model serialization and persistence

### Web Framework
- **FastAPI**: REST API framework with automatic OpenAPI documentation
- **Gradio**: Interactive web interface generation
- **SQLAlchemy**: Database ORM with multi-database support

### Notification Services
- **SMTP Email**: Security alert notifications via configurable email servers
- **Webhooks**: Custom endpoint integration for external security monitoring systems

### Client-Side Libraries
- **TypingDNA SDK**: Professional keystroke dynamics capture
- **Plotly.js**: Interactive data visualization for analytics dashboard
- **Device Motion API**: Mobile device accelerometer and gyroscope data capture