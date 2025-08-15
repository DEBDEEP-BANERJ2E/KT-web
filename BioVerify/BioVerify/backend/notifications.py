"""
Notification service for security alerts and events
"""

import os
import json
import smtplib
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
from config import config

class NotificationService:
    """Service for sending security notifications"""
    
    def __init__(self):
        self.email_enabled = bool(config.EMAIL_USER and config.EMAIL_PASSWORD)
        self.webhook_enabled = bool(config.WEBHOOK_URL)
    
    def send_email_alert(self, subject: str, body: str, recipient: Optional[str] = None):
        """Send email alert"""
        if not self.email_enabled:
            print("Email notifications not configured")
            return False
        
        try:
            recipient = recipient or config.ALERT_EMAIL
            if not recipient:
                print("No email recipient configured")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = config.EMAIL_USER
            msg['To'] = recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
            server.starttls()
            server.login(config.EMAIL_USER, config.EMAIL_PASSWORD)
            text = msg.as_string()
            server.sendmail(config.EMAIL_USER, recipient, text)
            server.quit()
            
            print(f"Email alert sent to {recipient}")
            return True
            
        except Exception as e:
            print(f"Failed to send email alert: {e}")
            return False
    
    def send_webhook_alert(self, payload: Dict):
        """Send webhook alert"""
        if not self.webhook_enabled:
            print("Webhook notifications not configured")
            return False
        
        try:
            headers = {'Content-Type': 'application/json'}
            if config.WEBHOOK_SECRET:
                headers['X-Webhook-Secret'] = config.WEBHOOK_SECRET
            
            response = requests.post(
                config.WEBHOOK_URL,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("Webhook alert sent successfully")
                return True
            else:
                print(f"Webhook alert failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Failed to send webhook alert: {e}")
            return False
    
    def send_security_alert(self, user_id: str, event_type: str, metadata: Dict):
        """Send security alert via all configured channels"""
        timestamp = datetime.utcnow().isoformat()
        
        # Prepare alert data
        alert_data = {
            'timestamp': timestamp,
            'user_id': user_id,
            'event_type': event_type,
            'metadata': metadata,
            'severity': 'HIGH' if event_type == 'impostor_detected' else 'MEDIUM'
        }
        
        # Email alert
        if self.email_enabled:
            subject = f"🚨 Security Alert: {event_type.replace('_', ' ').title()}"
            body = self._create_email_body(alert_data)
            self.send_email_alert(subject, body)
        
        # Webhook alert
        if self.webhook_enabled:
            self.send_webhook_alert(alert_data)
    
    def _create_email_body(self, alert_data: Dict) -> str:
        """Create HTML email body for security alert"""
        severity_color = "#dc3545" if alert_data['severity'] == 'HIGH' else "#fd7e14"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .alert-box {{ 
                    border-left: 4px solid {severity_color}; 
                    background-color: #f8f9fa; 
                    padding: 20px; 
                    margin: 20px 0; 
                }}
                .header {{ color: {severity_color}; font-size: 24px; font-weight: bold; }}
                .details {{ margin: 15px 0; }}
                .metadata {{ background-color: #e9ecef; padding: 10px; border-radius: 4px; }}
                .footer {{ color: #6c757d; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="alert-box">
                <div class="header">🚨 Security Alert</div>
                
                <div class="details">
                    <strong>Event Type:</strong> {alert_data['event_type'].replace('_', ' ').title()}<br>
                    <strong>User ID:</strong> {alert_data['user_id']}<br>
                    <strong>Severity:</strong> {alert_data['severity']}<br>
                    <strong>Timestamp:</strong> {alert_data['timestamp']}<br>
                </div>
                
                <div class="details">
                    <strong>Event Details:</strong>
                    <div class="metadata">
                        <pre>{json.dumps(alert_data['metadata'], indent=2)}</pre>
                    </div>
                </div>
                
                <div class="footer">
                    This is an automated security alert from the Behavioral Biometrics System.
                </div>
            </div>
        </body>
        </html>
        """
        return html_body
    
    def send_otp_alert(self, user_id: str, otp_code: str, recipient_email: str):
        """Send OTP via email for step-up authentication"""
        if not self.email_enabled:
            return False
        
        subject = "🔐 Security Verification Required"
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .otp-box {{ 
                    border: 2px solid #007bff; 
                    background-color: #f8f9fa; 
                    padding: 20px; 
                    margin: 20px 0; 
                    text-align: center;
                    border-radius: 8px;
                }}
                .otp-code {{ 
                    font-size: 36px; 
                    font-weight: bold; 
                    color: #007bff; 
                    letter-spacing: 5px; 
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="otp-box">
                <h2>🔐 Identity Verification Required</h2>
                <p>Your behavioral pattern indicates additional verification is needed.</p>
                <p>Please use the following verification code:</p>
                <div class="otp-code">{otp_code}</div>
                <p><small>This code will expire in 5 minutes.</small></p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email_alert(subject, body, recipient_email)

# Global notification service instance
notification_service = NotificationService()
