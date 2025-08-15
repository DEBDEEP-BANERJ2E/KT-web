# 🔐 Behavioral Biometrics Authentication System

A production-ready behavioral biometrics authentication system that analyzes typing patterns, device motion, and touch gestures for continuous user authentication.

## 🚀 **System Status: DEPLOYED & RUNNING**

- **Backend API**: Running on port 5000
- **Database**: PostgreSQL connected and operational
- **Authentication**: Real-time typing dynamics capture active
- **Documentation**: Available at `/docs`

## 📋 **Quick Start Guide**

### 1. Access the System
- **Main Interface**: Your Replit preview URL
- **API Documentation**: `[your-url]/docs`
- **Authentication Interface**: `[your-url]/auth`

### 2. Test Authentication Flow

**Step 1: Register a User**
```bash
curl -X POST "[your-url]/register" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo_user", "email": "demo@example.com"}'
```

**Step 2: Enroll Biometric Data**
```bash
curl -X POST "[your-url]/enroll" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_user",
    "features": {
      "dwell_mean": 120.5,
      "flight_mean": 150.3,
      "typing_speed": 250.0,
      "rhythm_consistency": 0.85
    }
  }'
```

**Step 3: Authenticate**
```bash
curl -X POST "[your-url]/authenticate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_user",
    "features": {
      "dwell_mean": 118.2,
      "flight_mean": 148.7,
      "typing_speed": 245.0,
      "rhythm_consistency": 0.82
    }
  }'
```

## 🎯 **Key Features**

### Authentication Engine
- **KNN & SVM Models**: Dual machine learning approach
- **Real-time Scoring**: Instant authentication decisions
- **Continuous Monitoring**: Session-based authentication
- **Impostor Detection**: Automatic threat identification

### Biometric Capture
- **Keystroke Dynamics**: Dwell time, flight time, rhythm
- **Device Motion**: Gyroscope and accelerometer data
- **Touch Patterns**: Pressure and swipe velocity
- **TypingDNA Integration**: Professional-grade capture

### Security Features
- **Step-up Authentication**: OTP for suspicious activity
- **Account Lockouts**: Failed attempt protection
- **Real-time Alerts**: Email and webhook notifications
- **Security Events**: Comprehensive audit logging

### Admin Dashboard
- **User Management**: Registration and enrollment
- **Analytics**: Performance metrics and trends
- **Data Export**: CSV export for analysis
- **System Monitoring**: Health checks and status

## 💳 **Free Deployment on Replit**

### Autoscale Deployment (Recommended)
1. **Click Deploy Button** in your Replit interface
2. **Select "Autoscale"** deployment type
3. **Configure Resources**: 
   - CPU: 0.25 vCPU (sufficient for testing)
   - RAM: 512MB (handles ML models)
4. **Deploy**: Uses your monthly Replit credits
5. **Auto-scaling**: Scales to zero when idle = no costs

### Cost Optimization
- **Database**: PostgreSQL idles after 5 minutes (no charges)
- **Backend**: Only charged during active requests
- **Monthly Credits**: Core plan includes $25/month
- **Idle Scaling**: Zero costs when not in use

## 🔧 **Configuration**

### Environment Variables (Optional)
```bash
# TypingDNA Integration
TYPINGDNA_API_KEY=your_api_key
TYPINGDNA_API_SECRET=your_secret

# Email Notifications
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Webhook Alerts
WEBHOOK_URL=https://your-webhook-endpoint.com

# Google Drive Sync
GOOGLE_DRIVE_ENABLED=true
GOOGLE_DRIVE_FOLDER_ID=your_folder_id
```

### ML Model Tuning
```python
# config.py settings
USER_ENROLL_MIN_POSITIVES = 3    # Minimum samples for training
KNN_NEIGHBORS = 5                # K-nearest neighbors
SCORE_THRESHOLD = 0.60          # Authentication threshold
IMPOSTOR_THRESHOLD = 0.30       # Impostor detection threshold
```

## 📊 **API Endpoints**

### Authentication
- `POST /register` - Register new user
- `POST /enroll` - Enroll biometric data
- `POST /authenticate` - Authenticate user
- `POST /continuous-auth` - Continuous authentication

### User Management
- `GET /users` - List all users
- `GET /users/{user_id}/stats` - User statistics
- `POST /users/{user_id}/retrain` - Retrain model

### Analytics
- `GET /export/samples` - Export biometric samples
- `GET /export/scores` - Export authentication scores
- `GET /qr-code` - Generate mobile QR code

### System
- `GET /status` - System status
- `GET /config` - Configuration status
- `GET /docs` - API documentation

## 🛡️ **Security Best Practices**

### Production Deployment
1. **Enable HTTPS**: Use Replit's automatic SSL
2. **Set Strong Thresholds**: Adjust authentication sensitivity
3. **Monitor Alerts**: Configure email/webhook notifications
4. **Regular Backups**: Enable Google Drive sync
5. **Rate Limiting**: Implement API rate limits

### Privacy Protection
- **Data Encryption**: All biometric data encrypted at rest
- **Minimal Storage**: Only essential features stored
- **User Consent**: Clear privacy policy required
- **GDPR Compliance**: Data deletion capabilities

## 📱 **Mobile Testing**

1. **Generate QR Code**: `GET /qr-code`
2. **Scan with Phone**: Access authentication interface
3. **Test Touch Patterns**: Capture mobile biometrics
4. **Device Motion**: Test gyroscope/accelerometer

## 🔍 **Troubleshooting**

### Common Issues
- **Database Timeout**: Restart workflow if PostgreSQL disconnects
- **Model Training**: Ensure minimum 3 samples per user
- **Authentication Fails**: Check threshold settings
- **API Errors**: View logs in `/docs` interface

### Debug Mode
```bash
# Check system status
curl [your-url]/status

# View configuration
curl [your-url]/config

# Check user statistics
curl [your-url]/users/demo_user/stats
```

## 📈 **Next Steps**

1. **Deploy to Production**: Click the deploy button
2. **Add Users**: Register test accounts
3. **Collect Data**: Enroll biometric patterns
4. **Monitor Performance**: Check analytics dashboard
5. **Scale Up**: Increase resources as needed

Your behavioral biometrics system is ready for production use with free deployment on Replit!