"""
Gradio Frontend Application for Behavioral Biometrics System
"""

import os
import json
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import gradio as gr

from frontend.dashboard import BiometricsDashboard
from frontend.admin import AdminInterface
from config import config
from utils.helpers import generate_qr_code


class BiometricsApp:
    """Main Gradio application for behavioral biometrics"""
    
    def __init__(self):
        self.api_base = "http://localhost:8000"
        self.dashboard = BiometricsDashboard(self.api_base)
        self.admin = AdminInterface(self.api_base)
        self.current_user = None
        self.session_data = {}
        
    def api_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """Make API request to backend"""
        try:
            url = f"{self.api_base}{endpoint}"
            
            if method == "GET":
                response = requests.get(url, params=data or {})
            elif method == "POST":
                response = requests.post(url, json=data or {})
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "failed"}
    
    def register_user(self, user_id: str, email: str, full_name: str) -> Tuple[str, str]:
        """Register a new user"""
        if not user_id.strip():
            return "❌ Error: User ID is required", "error"
        
        result = self.api_request("/register", "POST", {
            "user_id": user_id.strip(),
            "email": email.strip() if email.strip() else None,
            "full_name": full_name.strip() if full_name.strip() else None
        })
        
        if "error" in result:
            return f"❌ Registration failed: {result['error']}", "error"
        
        return f"✅ User '{user_id}' registered successfully!", "success"
    
    def enroll_user_biometrics(self, user_id: str, typing_text: str) -> Tuple[str, str, str]:
        """Enroll user biometric data"""
        if not user_id.strip():
            return "❌ Error: User ID is required", "", "error"
        
        if not typing_text.strip():
            return "❌ Error: Please type some text for enrollment", "", "error"
        
        # Simulate feature extraction (in real app, this comes from frontend JS)
        features = self._simulate_typing_features(typing_text)
        
        result = self.api_request("/enroll", "POST", {
            "user_id": user_id.strip(),
            "features": features
        })
        
        if "error" in result:
            return f"❌ Enrollment failed: {result['error']}", "", "error"
        
        status_msg = f"✅ Enrollment successful!\n"
        status_msg += f"👤 User: {result['user_id']}\n"
        status_msg += f"📊 Enrollments: {result['enrollment_count']}\n"
        
        if result.get('train_info'):
            status_msg += f"🤖 Training: {result['train_info']}\n"
        
        can_auth = "✅ Ready for authentication" if result.get('can_authenticate') else "⏳ Need more enrollments"
        
        return status_msg, can_auth, "success"
    
    def authenticate_user(self, user_id: str, typing_text: str) -> Tuple[str, str, str, str]:
        """Authenticate user"""
        if not user_id.strip():
            return "❌ Error: User ID is required", "", "", "error"
        
        if not typing_text.strip():
            return "❌ Error: Please type some text for authentication", "", "", "error"
        
        # Simulate feature extraction
        features = self._simulate_typing_features(typing_text)
        
        result = self.api_request("/authenticate", "POST", {
            "user_id": user_id.strip(),
            "features": features
        })
        
        if "error" in result:
            return f"❌ Authentication failed: {result['error']}", "", "", "error"
        
        if result.get("status") == "insufficient_enrollment":
            return f"⏳ {result['message']}\nCurrent enrollments: {result['current_enrollments']}", "", "", "warning"
        
        # Format results
        verdict = result.get('verdict', 'unknown')
        confidence = result.get('confidence', 0) * 100
        risk_level = result.get('risk_level', 'unknown')
        final_score = result.get('final_score', 0) * 100
        
        # Status message with emoji
        if verdict == "genuine":
            status_icon = "✅"
            status_class = "success"
        elif verdict == "impostor":
            status_icon = "🚨"
            status_class = "error"
        else:
            status_icon = "⚠️"
            status_class = "warning"
        
        status_msg = f"{status_icon} Authentication Result\n"
        status_msg += f"👤 User: {user_id}\n"
        status_msg += f"🎯 Verdict: {verdict.upper()}\n"
        status_msg += f"📊 Confidence: {confidence:.1f}%\n"
        status_msg += f"⚡ Risk Level: {risk_level.upper()}\n"
        status_msg += f"🔢 Final Score: {final_score:.1f}%"
        
        # Detailed scores
        scores = result.get('scores', {})
        score_details = f"ML Average: {scores.get('ml_average', 0)*100:.1f}%\n"
        score_details += f"KNN Score: {scores.get('knn', 0)*100:.1f}%\n"
        score_details += f"SVM Score: {scores.get('svm', 0)*100:.1f}%\n"
        if scores.get('typingdna'):
            score_details += f"TypingDNA: {scores.get('typingdna', 0)*100:.1f}%"
        
        # Step-up authentication warning
        step_up_msg = ""
        if result.get('requires_step_up'):
            step_up_msg = "🔐 Additional verification required!\nPlease check your email for OTP."
        
        return status_msg, score_details, step_up_msg, status_class
    
    def get_user_stats(self, user_id: str) -> Tuple[str, str]:
        """Get user statistics"""
        if not user_id.strip():
            return "Please enter a User ID", ""
        
        result = self.api_request(f"/users/{user_id.strip()}/stats")
        
        if "error" in result:
            return f"❌ Error: {result['error']}", ""
        
        # Format statistics
        stats = f"📊 User Statistics for: {user_id}\n\n"
        
        sample_counts = result.get('sample_counts', {})
        stats += f"🔢 Sample Counts:\n"
        stats += f"  ✅ Positive: {sample_counts.get('positive', 0)}\n"
        stats += f"  ❌ Negative: {sample_counts.get('negative', 0)}\n"
        stats += f"  📈 Total: {sample_counts.get('total', 0)}\n\n"
        
        # Recent authentications
        recent_auths = result.get('recent_authentications', [])
        if recent_auths:
            stats += f"🕒 Recent Authentications ({len(recent_auths)}):\n"
            for auth in recent_auths[:5]:  # Show last 5
                timestamp = auth.get('timestamp', '')
                verdict = auth.get('verdict', 'unknown')
                confidence = auth.get('confidence', 0) * 100
                risk = auth.get('risk_level', 'unknown')
                
                stats += f"  {timestamp[:19]} | {verdict} ({confidence:.1f}%) | {risk}\n"
        else:
            stats += "🕒 No recent authentications\n"
        
        # Model information
        model_stats = result.get('model_stats', {})
        model_info = ""
        if model_stats.get('model_exists'):
            model_info = f"🤖 Model Status: Active\n"
            if 'model_metadata' in model_stats:
                meta = model_stats['model_metadata']
                model_info += f"📅 Last Training: {meta.get('training_timestamp', 'Unknown')}\n"
                model_info += f"📊 Training Samples: {meta.get('total_samples', 0)}\n"
        else:
            model_info = "🤖 Model Status: Not trained"
        
        return stats, model_info
    
    def get_qr_code(self) -> str:
        """Generate QR code for mobile access"""
        result = self.api_request("/qr-code")
        
        if "error" in result:
            return "Error generating QR code"
        
        return result.get('qr_code', '')
    
    def export_user_data(self, data_type: str, user_id: Optional[str] = None) -> Tuple[str, str]:
        """Export user data to CSV"""
        params = {}
        if user_id and user_id.strip():
            params['user_id'] = user_id.strip()
        
        try:
            url = f"{self.api_base}/export/{data_type}"
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Save file locally
            filename = f"{data_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join("exports", filename)
            os.makedirs("exports", exist_ok=True)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return f"✅ Data exported successfully!", filepath
            
        except Exception as e:
            return f"❌ Export failed: {str(e)}", ""
    
    def _simulate_typing_features(self, text: str) -> Dict[str, float]:
        """Simulate typing features (placeholder for real frontend integration)"""
        import random
        
        # In real implementation, these come from JavaScript typing recorder
        # This is just for demonstration
        char_count = len(text)
        word_count = len(text.split())
        
        return {
            "dwell_mean": random.uniform(80, 150),
            "dwell_std": random.uniform(20, 40),
            "flight_mean": random.uniform(100, 200),
            "flight_std": random.uniform(30, 60),
            "key_count": float(char_count),
            "session_time": random.uniform(10, 60),
            "pressure_mean": random.uniform(0.3, 0.8),
            "typing_speed": random.uniform(200, 400),  # characters per minute
            "rhythm_consistency": random.uniform(0.6, 0.9),
            "swipe_vel": 0,
            "gyro_x": random.uniform(-0.1, 0.1),
            "gyro_y": random.uniform(-0.1, 0.1),
            "gyro_z": random.uniform(-0.1, 0.1)
        }
    
    def create_interface(self) -> gr.Blocks:
        """Create the main Gradio interface"""
        
        with gr.Blocks(
            title="Behavioral Biometrics Authentication System",
            css="""
                .success { background-color: #d4edda !important; }
                .error { background-color: #f8d7da !important; }
                .warning { background-color: #fff3cd !important; }
                .center { text-align: center; }
            """
        ) as app:
            
            gr.HTML("""
                <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #007bff, #0056b3); color: white; margin-bottom: 20px; border-radius: 10px;">
                    <h1>🔐 Behavioral Biometrics Authentication System</h1>
                    <p>Real-time typing dynamics and continuous authentication</p>
                </div>
            """)
            
            # Load external JavaScript libraries
            gr.HTML("""
                <script src="/static/typing_recorder.js"></script>
                <script src="/static/biometrics.js"></script>
                <script src="https://cdn.typingdna.com/typingdna-3.0.0.min.js"></script>
            """)
            
            with gr.Tabs():
                
                # Authentication Tab
                with gr.Tab("🔑 Authentication"):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### User Registration & Enrollment")
                            
                            with gr.Row():
                                reg_user_id = gr.Textbox(label="User ID", placeholder="Enter unique user ID")
                                reg_email = gr.Textbox(label="Email (optional)", placeholder="user@example.com")
                            
                            reg_full_name = gr.Textbox(label="Full Name (optional)", placeholder="John Doe")
                            register_btn = gr.Button("Register User", variant="primary")
                            register_status = gr.Textbox(label="Registration Status", interactive=False)
                            
                            gr.Markdown("---")
                            
                            enroll_user_id = gr.Textbox(label="User ID for Enrollment", placeholder="Enter user ID")
                            enroll_text = gr.Textbox(
                                label="Type text for enrollment (minimum 50 characters)",
                                placeholder="Please type a sentence or paragraph for biometric enrollment...",
                                lines=3
                            )
                            enroll_btn = gr.Button("Enroll Biometrics", variant="secondary")
                            enroll_status = gr.Textbox(label="Enrollment Status", interactive=False)
                            enroll_ready = gr.Textbox(label="Authentication Readiness", interactive=False)
                        
                        with gr.Column():
                            gr.Markdown("### Authentication")
                            
                            auth_user_id = gr.Textbox(label="User ID", placeholder="Enter user ID to authenticate")
                            auth_text = gr.Textbox(
                                label="Type text for authentication",
                                placeholder="Please type naturally for authentication...",
                                lines=3
                            )
                            auth_btn = gr.Button("Authenticate", variant="primary")
                            
                            auth_status = gr.Textbox(label="Authentication Result", interactive=False)
                            score_details = gr.Textbox(label="Score Details", interactive=False)
                            step_up_warning = gr.Textbox(label="Security Alerts", interactive=False)
                
                # Dashboard Tab
                with gr.Tab("📊 Dashboard"):
                    with gr.Row():
                        with gr.Column():
                            dashboard_user_id = gr.Textbox(label="User ID", placeholder="Enter user ID for statistics")
                            stats_btn = gr.Button("Get User Statistics", variant="primary")
                            user_stats = gr.Textbox(label="User Statistics", lines=10, interactive=False)
                        
                        with gr.Column():
                            model_info = gr.Textbox(label="Model Information", lines=5, interactive=False)
                            
                            gr.Markdown("### Data Export")
                            export_type = gr.Dropdown(
                                choices=["samples", "scores", "users"],
                                label="Export Type",
                                value="samples"
                            )
                            export_user_id = gr.Textbox(label="User ID (optional)", placeholder="Leave empty for all users")
                            export_btn = gr.Button("Export Data", variant="secondary")
                            export_status = gr.Textbox(label="Export Status", interactive=False)
                            export_file = gr.File(label="Download File", interactive=False)
                
                # Admin Tab
                with gr.Tab("⚙️ Admin"):
                    admin_interface = self.admin.create_interface()
                
                # Mobile Access Tab
                with gr.Tab("📱 Mobile Access"):
                    gr.Markdown("### QR Code for Mobile Testing")
                    gr.Markdown("Scan this QR code with your mobile device to access the authentication interface:")
                    
                    qr_btn = gr.Button("Generate QR Code", variant="primary")
                    qr_code = gr.HTML()
                    
                    gr.Markdown("""
                        ### Instructions for Mobile Testing:
                        1. Click "Generate QR Code" above
                        2. Scan the QR code with your mobile device
                        3. Use the mobile interface for touch-based biometric capture
                        4. Test typing dynamics and gesture recognition
                    """)
                
                # System Status Tab
                with gr.Tab("🔧 System Status"):
                    gr.Markdown("### System Configuration")
                    
                    config_btn = gr.Button("Check System Status", variant="primary")
                    config_status = gr.JSON(label="Configuration Status")
                    
                    gr.Markdown("### Feature Configuration")
                    features_display = gr.JSON(label="Biometric Features")
                    
                    gr.Markdown("### API Endpoints")
                    gr.Markdown(f"""
                        - **Backend API**: `{self.api_base}`
                        - **TypingDNA Integration**: {'✅ Enabled' if config.TYPINGDNA_API_KEY else '❌ Disabled'}
                        - **Google Drive Sync**: {'✅ Enabled' if config.GOOGLE_DRIVE_ENABLED else '❌ Disabled'}
                        - **Email Notifications**: {'✅ Enabled' if config.EMAIL_USER else '❌ Disabled'}
                        - **Webhook Alerts**: {'✅ Enabled' if config.WEBHOOK_URL else '❌ Disabled'}
                    """)
            
            # Event handlers
            register_btn.click(
                self.register_user,
                inputs=[reg_user_id, reg_email, reg_full_name],
                outputs=[register_status]
            )
            
            enroll_btn.click(
                self.enroll_user_biometrics,
                inputs=[enroll_user_id, enroll_text],
                outputs=[enroll_status, enroll_ready]
            )
            
            auth_btn.click(
                self.authenticate_user,
                inputs=[auth_user_id, auth_text],
                outputs=[auth_status, score_details, step_up_warning]
            )
            
            stats_btn.click(
                self.get_user_stats,
                inputs=[dashboard_user_id],
                outputs=[user_stats, model_info]
            )
            
            export_btn.click(
                self.export_user_data,
                inputs=[export_type, export_user_id],
                outputs=[export_status, export_file]
            )
            
            qr_btn.click(
                self.get_qr_code,
                outputs=[qr_code]
            )
            
            config_btn.click(
                lambda: self.api_request("/config"),
                outputs=[config_status]
            )
            
        return app


def create_gradio_app():
    """Create and return the Gradio application"""
    app_instance = BiometricsApp()
    return app_instance.create_interface()


if __name__ == "__main__":
    app = create_gradio_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=5000,
        share=False
    )
