/**
 * TypingDNA Integration and Keystroke Dynamics Recorder
 */

class TypingRecorder {
    constructor() {
        this.typing_data = [];
        this.isRecording = false;
        this.startTime = null;
        this.lastKeyTime = null;
        this.textInput = '';
        this.keyDownTimes = {};
        
        // Initialize TypingDNA if available
        this.initializeTypingDNA();
    }
    
    initializeTypingDNA() {
        // TypingDNA recorder integration
        if (typeof TypingDNA !== 'undefined') {
            this.tdna = new TypingDNA();
            this.typingDNAEnabled = true;
            console.log('TypingDNA initialized');
        } else {
            console.log('TypingDNA not available, using custom recorder');
            this.typingDNAEnabled = false;
        }
    }
    
    startRecording(targetElement = null) {
        this.isRecording = true;
        this.typing_data = [];
        this.startTime = Date.now();
        this.lastKeyTime = this.startTime;
        this.textInput = '';
        this.keyDownTimes = {};
        
        // Set up event listeners
        const target = targetElement || document;
        
        target.addEventListener('keydown', this.handleKeyDown.bind(this));
        target.addEventListener('keyup', this.handleKeyUp.bind(this));
        target.addEventListener('keypress', this.handleKeyPress.bind(this));
        
        // TypingDNA recording
        if (this.typingDNAEnabled) {
            this.tdna.start();
        }
        
        console.log('Typing recording started');
    }
    
    stopRecording() {
        this.isRecording = false;
        
        // TypingDNA recording
        let typingPattern = null;
        if (this.typingDNAEnabled) {
            typingPattern = this.tdna.stop();
        }
        
        const features = this.extractFeatures();
        
        console.log('Typing recording stopped');
        console.log('Extracted features:', features);
        
        return {
            features: features,
            typing_pattern: typingPattern,
            raw_data: this.typing_data,
            text_input: this.textInput
        };
    }
    
    handleKeyDown(event) {
        if (!this.isRecording) return;
        
        const currentTime = Date.now();
        const key = event.code || event.keyCode;
        
        this.keyDownTimes[key] = currentTime;
        
        // Record pressure if available (for touch devices)
        const pressure = event.force || event.pressure || 0;
        
        this.typing_data.push({
            type: 'keydown',
            key: key,
            timestamp: currentTime,
            pressure: pressure,
            which: event.which || event.keyCode
        });
    }
    
    handleKeyUp(event) {
        if (!this.isRecording) return;
        
        const currentTime = Date.now();
        const key = event.code || event.keyCode;
        const keyDownTime = this.keyDownTimes[key];
        
        if (keyDownTime) {
            const dwellTime = currentTime - keyDownTime;
            const flightTime = currentTime - this.lastKeyTime;
            
            this.typing_data.push({
                type: 'keyup',
                key: key,
                timestamp: currentTime,
                dwell_time: dwellTime,
                flight_time: flightTime,
                which: event.which || event.keyCode
            });
            
            delete this.keyDownTimes[key];
            this.lastKeyTime = currentTime;
        }
    }
    
    handleKeyPress(event) {
        if (!this.isRecording) return;
        
        const char = String.fromCharCode(event.which || event.keyCode);
        if (char && char !== '\n' && char !== '\r') {
            this.textInput += char;
        }
    }
    
    extractFeatures() {
        if (this.typing_data.length === 0) {
            return this.getDefaultFeatures();
        }
        
        const keyEvents = this.typing_data.filter(event => event.type === 'keyup');
        
        if (keyEvents.length === 0) {
            return this.getDefaultFeatures();
        }
        
        // Extract dwell times
        const dwellTimes = keyEvents
            .map(event => event.dwell_time)
            .filter(time => time > 0 && time < 1000); // Filter outliers
        
        // Extract flight times
        const flightTimes = keyEvents
            .map(event => event.flight_time)
            .filter(time => time > 0 && time < 2000); // Filter outliers
        
        // Extract pressure values
        const pressures = this.typing_data
            .map(event => event.pressure || 0)
            .filter(pressure => pressure > 0);
        
        // Calculate statistics
        const dwellMean = this.calculateMean(dwellTimes);
        const dwellStd = this.calculateStd(dwellTimes, dwellMean);
        const flightMean = this.calculateMean(flightTimes);
        const flightStd = this.calculateStd(flightTimes, flightMean);
        const pressureMean = this.calculateMean(pressures);
        
        // Session metrics
        const sessionTime = (Date.now() - this.startTime) / 1000; // in seconds
        const keyCount = keyEvents.length;
        const typingSpeed = keyCount / (sessionTime / 60); // keys per minute
        
        // Rhythm consistency (coefficient of variation)
        const rhythmConsistency = dwellStd > 0 ? dwellMean / dwellStd : 0;
        
        return {
            dwell_mean: dwellMean,
            dwell_std: dwellStd,
            flight_mean: flightMean,
            flight_std: flightStd,
            key_count: keyCount,
            session_time: sessionTime,
            pressure_mean: pressureMean,
            typing_speed: typingSpeed,
            rhythm_consistency: rhythmConsistency,
            // Additional features for compatibility
            swipe_vel: 0,
            gyro_x: 0,
            gyro_y: 0,
            gyro_z: 0
        };
    }
    
    getDefaultFeatures() {
        return {
            dwell_mean: 0,
            dwell_std: 0,
            flight_mean: 0,
            flight_std: 0,
            key_count: 0,
            session_time: 0,
            pressure_mean: 0,
            typing_speed: 0,
            rhythm_consistency: 0,
            swipe_vel: 0,
            gyro_x: 0,
            gyro_y: 0,
            gyro_z: 0
        };
    }
    
    calculateMean(values) {
        if (values.length === 0) return 0;
        return values.reduce((sum, val) => sum + val, 0) / values.length;
    }
    
    calculateStd(values, mean = null) {
        if (values.length === 0) return 0;
        if (mean === null) mean = this.calculateMean(values);
        
        const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
        return Math.sqrt(variance);
    }
    
    // TypingDNA specific methods
    saveToTypingDNA(userId, textId = '1') {
        if (!this.typingDNAEnabled) {
            return Promise.reject('TypingDNA not available');
        }
        
        const pattern = this.tdna.getTypingPattern({ type: 1, text: this.textInput });
        
        return fetch('/typingdna/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                typing_pattern: pattern,
                text_id: textId
            })
        }).then(response => response.json());
    }
    
    verifyWithTypingDNA(userId, textId = '1') {
        if (!this.typingDNAEnabled) {
            return Promise.reject('TypingDNA not available');
        }
        
        const pattern = this.tdna.getTypingPattern({ type: 0, text: this.textInput });
        
        return fetch('/typingdna/verify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                typing_pattern: pattern,
                text_id: textId
            })
        }).then(response => response.json());
    }
}

// Global typing recorder instance
window.typingRecorder = new TypingRecorder();

// Utility functions for integration
window.BiometricUtils = {
    startTypingCapture: function(elementId = null) {
        const element = elementId ? document.getElementById(elementId) : null;
        window.typingRecorder.startRecording(element);
    },
    
    stopTypingCapture: function() {
        return window.typingRecorder.stopRecording();
    },
    
    captureTypingForDuration: function(durationMs = 5000) {
        return new Promise((resolve) => {
            window.typingRecorder.startRecording();
            setTimeout(() => {
                const result = window.typingRecorder.stopRecording();
                resolve(result);
            }, durationMs);
        });
    }
};

console.log('Typing recorder initialized');
