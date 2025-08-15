/**
 * Behavioral Biometrics Client-Side Library
 * Handles device motion, touch gestures, and continuous authentication
 */

class BiometricCapture {
    constructor() {
        this.isCapturing = false;
        this.motionData = [];
        this.touchData = [];
        this.sessionId = this.generateSessionId();
        this.deviceInfo = this.getDeviceInfo();
        
        this.initializeCapture();
    }
    
    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }
    
    getDeviceInfo() {
        return {
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            screenWidth: screen.width,
            screenHeight: screen.height,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            language: navigator.language,
            touchSupport: 'ontouchstart' in window,
            devicePixelRatio: window.devicePixelRatio || 1
        };
    }
    
    initializeCapture() {
        // Request device motion permissions for iOS 13+
        if (typeof DeviceMotionEvent !== 'undefined' && typeof DeviceMotionEvent.requestPermission === 'function') {
            this.requestMotionPermission();
        }
        
        // Set up event listeners
        this.setupMotionListeners();
        this.setupTouchListeners();
    }
    
    requestMotionPermission() {
        DeviceMotionEvent.requestPermission()
            .then(response => {
                if (response === 'granted') {
                    console.log('Device motion permission granted');
                } else {
                    console.log('Device motion permission denied');
                }
            })
            .catch(console.error);
    }
    
    setupMotionListeners() {
        // Device motion (accelerometer/gyroscope)
        window.addEventListener('devicemotion', (event) => {
            if (!this.isCapturing) return;
            
            const motionEvent = {
                timestamp: Date.now(),
                acceleration: {
                    x: event.acceleration ? event.acceleration.x : 0,
                    y: event.acceleration ? event.acceleration.y : 0,
                    z: event.acceleration ? event.acceleration.z : 0
                },
                accelerationIncludingGravity: {
                    x: event.accelerationIncludingGravity ? event.accelerationIncludingGravity.x : 0,
                    y: event.accelerationIncludingGravity ? event.accelerationIncludingGravity.y : 0,
                    z: event.accelerationIncludingGravity ? event.accelerationIncludingGravity.z : 0
                },
                rotationRate: {
                    alpha: event.rotationRate ? event.rotationRate.alpha : 0,
                    beta: event.rotationRate ? event.rotationRate.beta : 0,
                    gamma: event.rotationRate ? event.rotationRate.gamma : 0
                }
            };
            
            this.motionData.push(motionEvent);
        });
        
        // Device orientation
        window.addEventListener('deviceorientation', (event) => {
            if (!this.isCapturing) return;
            
            this.lastOrientation = {
                timestamp: Date.now(),
                alpha: event.alpha || 0,
                beta: event.beta || 0,
                gamma: event.gamma || 0
            };
        });
    }
    
    setupTouchListeners() {
        // Touch events for mobile devices
        document.addEventListener('touchstart', (event) => {
            if (!this.isCapturing) return;
            this.handleTouchEvent('touchstart', event);
        });
        
        document.addEventListener('touchmove', (event) => {
            if (!this.isCapturing) return;
            this.handleTouchEvent('touchmove', event);
        });
        
        document.addEventListener('touchend', (event) => {
            if (!this.isCapturing) return;
            this.handleTouchEvent('touchend', event);
        });
        
        // Mouse events for desktop (simulate touch)
        document.addEventListener('mousedown', (event) => {
            if (!this.isCapturing) return;
            this.handleMouseEvent('mousedown', event);
        });
        
        document.addEventListener('mousemove', (event) => {
            if (!this.isCapturing) return;
            this.handleMouseEvent('mousemove', event);
        });
        
        document.addEventListener('mouseup', (event) => {
            if (!this.isCapturing) return;
            this.handleMouseEvent('mouseup', event);
        });
    }
    
    handleTouchEvent(type, event) {
        const touches = Array.from(event.touches || event.changedTouches || []);
        
        touches.forEach(touch => {
            const touchEvent = {
                type: type,
                timestamp: Date.now(),
                x: touch.clientX,
                y: touch.clientY,
                force: touch.force || 0,
                radiusX: touch.radiusX || 0,
                radiusY: touch.radiusY || 0,
                rotationAngle: touch.rotationAngle || 0,
                identifier: touch.identifier
            };
            
            this.touchData.push(touchEvent);
        });
    }
    
    handleMouseEvent(type, event) {
        const mouseEvent = {
            type: type.replace('mouse', 'touch'), // Normalize event names
            timestamp: Date.now(),
            x: event.clientX,
            y: event.clientY,
            force: event.pressure || 0,
            radiusX: 0,
            radiusY: 0,
            rotationAngle: 0,
            identifier: 0 // Single mouse pointer
        };
        
        this.touchData.push(mouseEvent);
    }
    
    startCapture() {
        this.isCapturing = true;
        this.motionData = [];
        this.touchData = [];
        this.startTime = Date.now();
        
        console.log('Biometric capture started');
    }
    
    stopCapture() {
        this.isCapturing = false;
        
        const features = this.extractFeatures();
        
        console.log('Biometric capture stopped');
        console.log('Extracted features:', features);
        
        return {
            features: features,
            device_info: this.deviceInfo,
            session_id: this.sessionId,
            raw_motion: this.motionData,
            raw_touch: this.touchData
        };
    }
    
    extractFeatures() {
        const features = {
            // Default values
            dwell_mean: 0,
            dwell_std: 0,
            flight_mean: 0,
            flight_std: 0,
            key_count: 0,
            session_time: 0,
            pressure_mean: 0,
            swipe_vel: 0,
            gyro_x: 0,
            gyro_y: 0,
            gyro_z: 0,
            typing_speed: 0,
            rhythm_consistency: 0
        };
        
        // Extract motion features
        if (this.motionData.length > 0) {
            const gyroData = this.motionData.map(m => m.rotationRate);
            features.gyro_x = this.calculateMean(gyroData.map(g => g.alpha));
            features.gyro_y = this.calculateMean(gyroData.map(g => g.beta));
            features.gyro_z = this.calculateMean(gyroData.map(g => g.gamma));
        }
        
        // Extract touch/gesture features
        if (this.touchData.length > 0) {
            const pressures = this.touchData.map(t => t.force).filter(f => f > 0);
            features.pressure_mean = this.calculateMean(pressures);
            
            // Calculate swipe velocity
            const swipeVelocities = this.calculateSwipeVelocities();
            features.swipe_vel = this.calculateMean(swipeVelocities);
        }
        
        // Session metrics
        features.session_time = this.startTime ? (Date.now() - this.startTime) / 1000 : 0;
        
        return features;
    }
    
    calculateSwipeVelocities() {
        const velocities = [];
        const touches = this.touchData;
        
        for (let i = 1; i < touches.length; i++) {
            const current = touches[i];
            const previous = touches[i - 1];
            
            if (current.identifier === previous.identifier) {
                const deltaX = current.x - previous.x;
                const deltaY = current.y - previous.y;
                const deltaTime = (current.timestamp - previous.timestamp) / 1000; // seconds
                
                if (deltaTime > 0) {
                    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
                    const velocity = distance / deltaTime; // pixels per second
                    velocities.push(velocity);
                }
            }
        }
        
        return velocities;
    }
    
    calculateMean(values) {
        if (values.length === 0) return 0;
        return values.reduce((sum, val) => sum + (val || 0), 0) / values.length;
    }
    
    calculateStd(values, mean = null) {
        if (values.length === 0) return 0;
        if (mean === null) mean = this.calculateMean(values);
        
        const variance = values.reduce((sum, val) => sum + Math.pow((val || 0) - mean, 2), 0) / values.length;
        return Math.sqrt(variance);
    }
}

// Continuous Authentication Manager
class ContinuousAuth {
    constructor(options = {}) {
        this.userId = options.userId || null;
        this.interval = options.interval || 30000; // 30 seconds
        this.isActive = false;
        this.intervalId = null;
        this.biometricCapture = new BiometricCapture();
        this.typingRecorder = window.typingRecorder;
        
        this.authEndpoint = '/authenticate';
        this.onAuthResult = options.onAuthResult || this.defaultAuthHandler;
        this.onImpostorDetected = options.onImpostorDetected || this.defaultImpostorHandler;
    }
    
    start(userId) {
        if (this.isActive) {
            console.log('Continuous authentication already active');
            return;
        }
        
        this.userId = userId;
        this.isActive = true;
        
        console.log(`Starting continuous authentication for user: ${userId}`);
        
        // Start initial capture
        this.startCapture();
        
        // Set up periodic authentication
        this.intervalId = setInterval(() => {
            this.performAuthentication();
        }, this.interval);
    }
    
    stop() {
        if (!this.isActive) return;
        
        this.isActive = false;
        
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        
        // Stop current capture
        this.biometricCapture.stopCapture();
        
        console.log('Continuous authentication stopped');
    }
    
    startCapture() {
        this.biometricCapture.startCapture();
        this.typingRecorder.startRecording();
    }
    
    async performAuthentication() {
        if (!this.isActive || !this.userId) return;
        
        try {
            // Stop current capture and get features
            const biometricData = this.biometricCapture.stopCapture();
            const typingData = this.typingRecorder.stopRecording();
            
            // Combine features
            const combinedFeatures = {
                ...biometricData.features,
                ...typingData.features
            };
            
            // Send authentication request
            const response = await fetch(this.authEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: this.userId,
                    features: combinedFeatures,
                    session_id: biometricData.session_id,
                    device_info: biometricData.device_info,
                    typingdna_pattern: typingData.typing_pattern
                })
            });
            
            const result = await response.json();
            
            // Handle authentication result
            this.handleAuthResult(result);
            
            // Start new capture for next iteration
            this.startCapture();
            
        } catch (error) {
            console.error('Continuous authentication error:', error);
            
            // Restart capture on error
            this.startCapture();
        }
    }
    
    handleAuthResult(result) {
        console.log('Authentication result:', result);
        
        // Call custom handler
        this.onAuthResult(result);
        
        // Handle impostor detection
        if (result.verdict === 'impostor' || result.requires_step_up) {
            this.onImpostorDetected(result);
        }
    }
    
    defaultAuthHandler(result) {
        // Update UI with authentication status
        const statusElement = document.getElementById('auth-status');
        if (statusElement) {
            statusElement.textContent = `Status: ${result.verdict} (${(result.confidence * 100).toFixed(1)}% confidence)`;
            statusElement.className = `auth-status ${result.risk_level}`;
        }
    }
    
    defaultImpostorHandler(result) {
        console.warn('Impostor detected:', result);
        
        // Show step-up authentication dialog
        this.showStepUpDialog(result);
    }
    
    showStepUpDialog(result) {
        // Create step-up authentication modal
        const modal = document.createElement('div');
        modal.className = 'step-up-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <h3>🔐 Additional Verification Required</h3>
                <p>For your security, additional verification is needed.</p>
                <p>Risk Level: <span class="risk-${result.risk_level}">${result.risk_level}</span></p>
                <p>Please enter the verification code sent to your email:</p>
                <input type="text" id="otp-input" placeholder="Enter OTP" maxlength="6">
                <div class="modal-buttons">
                    <button onclick="this.verifyOTP()" class="btn-primary">Verify</button>
                    <button onclick="this.logout()" class="btn-secondary">Logout</button>
                </div>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(modal);
        
        // Focus on input
        document.getElementById('otp-input').focus();
    }
    
    verifyOTP() {
        const otpInput = document.getElementById('otp-input');
        const otp = otpInput.value;
        
        if (otp.length === 6) {
            // Send OTP verification (implement as needed)
            console.log('Verifying OTP:', otp);
            
            // Close modal
            const modal = document.querySelector('.step-up-modal');
            if (modal) {
                modal.remove();
            }
        } else {
            alert('Please enter a 6-digit verification code');
        }
    }
    
    logout() {
        // Implement logout logic
        console.log('User logging out due to security alert');
        
        // Stop continuous authentication
        this.stop();
        
        // Redirect to login page or clear session
        window.location.href = '/login';
    }
}

// Global instances
window.biometricCapture = new BiometricCapture();
window.continuousAuth = new ContinuousAuth();

// Utility functions
window.BiometricAuth = {
    startCapture: function() {
        window.biometricCapture.startCapture();
    },
    
    stopCapture: function() {
        return window.biometricCapture.stopCapture();
    },
    
    startContinuousAuth: function(userId, options = {}) {
        window.continuousAuth = new ContinuousAuth(options);
        window.continuousAuth.start(userId);
    },
    
    stopContinuousAuth: function() {
        window.continuousAuth.stop();
    },
    
    authenticate: async function(userId, features = null) {
        if (!features) {
            const data = window.biometricCapture.stopCapture();
            features = data.features;
        }
        
        const response = await fetch('/authenticate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                features: features
            })
        });
        
        return response.json();
    }
};

console.log('Biometric capture system initialized');
