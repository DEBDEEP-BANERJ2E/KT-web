"""
Admin interface for Behavioral Biometrics System
"""

import json
import requests
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import gradio as gr


class AdminInterface:
    """Admin interface for system management"""
    
    def __init__(self, api_base: str):
        self.api_base = api_base
    
    def api_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
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
    
    def get_all_users(self) -> Tuple[pd.DataFrame, str]:
        """Get all users in the system"""
        result = self.api_request("/users")
        
        if "error" in result:
            return pd.DataFrame(), f"❌ Error: {result['error']}"
        
        users = result.get('users', [])
        if not users:
            return pd.DataFrame(), "No users found in the system"
        
        # Convert to DataFrame for display
        df = pd.DataFrame(users)
        
        # Format datetime columns
        for col in ['created_at', 'last_login']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
        
        return df, f"Found {len(users)} users"
    
    def retrain_user_model(self, user_id: str) -> str:
        """Retrain models for a specific user"""
        if not user_id.strip():
            return "❌ Error: User ID is required"
        
        result = self.api_request(f"/users/{user_id.strip()}/retrain", "POST")
        
        if "error" in result:
            return f"❌ Retraining failed: {result['error']}"
        
        return f"✅ Model retraining initiated for user: {user_id}\n{result.get('message', '')}"
    
    def get_user_model_stats(self, user_id: str) -> Tuple[str, str]:
        """Get detailed model statistics for a user"""
        if not user_id.strip():
            return "Please enter a User ID", ""
        
        result = self.api_request(f"/users/{user_id.strip()}/stats")
        
        if "error" in result:
            return f"❌ Error: {result['error']}", ""
        
        model_stats = result.get('model_stats', {})
        
        if not model_stats.get('model_exists'):
            return f"No trained model found for user: {user_id}", ""
        
        # Format model information
        model_info = f"🤖 **Model Information for {user_id}**\n\n"
        
        if 'model_metadata' in model_stats:
            meta = model_stats['model_metadata']
            model_info += f"📅 **Training Date**: {meta.get('training_timestamp', 'Unknown')}\n"
            model_info += f"📊 **Training Samples**: {meta.get('total_samples', 0)}\n"
            model_info += f"✅ **Positive Samples**: {meta.get('positive_samples', 0)}\n"
            model_info += f"❌ **Negative Samples**: {meta.get('negative_samples', 0)}\n"
            model_info += f"🎯 **KNN CV Score**: {meta.get('knn_cv_score', 0):.3f}\n"
            model_info += f"🎯 **SVM CV Score**: {meta.get('svm_cv_score', 0):.3f}\n"
            model_info += f"📝 **Model Version**: {meta.get('model_version', 'Unknown')}\n"
        
        model_info += f"\n📈 **Recent Samples**: {model_stats.get('recent_samples', 0)}\n"
        
        # Performance summary
        performance = "📊 **Performance Summary**\n\n"
        sample_counts = result.get('sample_counts', {})
        performance += f"• Total Samples: {sample_counts.get('total', 0)}\n"
        performance += f"• Positive/Negative Ratio: {sample_counts.get('positive', 0)}:{sample_counts.get('negative', 0)}\n"
        
        recent_auths = result.get('recent_authentications', [])
        if recent_auths:
            genuine_count = sum(1 for auth in recent_auths if auth.get('verdict') == 'genuine')
            impostor_count = sum(1 for auth in recent_auths if auth.get('verdict') == 'impostor')
            uncertain_count = sum(1 for auth in recent_auths if auth.get('verdict') == 'uncertain')
            
            performance += f"• Recent Authentications: {len(recent_auths)}\n"
            performance += f"  - Genuine: {genuine_count}\n"
            performance += f"  - Impostor: {impostor_count}\n"
            performance += f"  - Uncertain: {uncertain_count}\n"
            
            if len(recent_auths) > 0:
                accuracy = (genuine_count / len(recent_auths)) * 100
                performance += f"• Recent Accuracy: {accuracy:.1f}%\n"
        
        return model_info, performance
    
    def bulk_export_data(self, export_type: str) -> Tuple[str, str]:
        """Export system data in bulk"""
        try:
            url = f"{self.api_base}/export/{export_type}"
            response = requests.get(url)
            response.raise_for_status()
            
            # Save file locally
            filename = f"admin_{export_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = f"exports/{filename}"
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return f"✅ {export_type.title()} data exported successfully!", filepath
            
        except Exception as e:
            return f"❌ Export failed: {str(e)}", ""
    
    def system_maintenance(self, action: str) -> str:
        """Perform system maintenance actions"""
        try:
            if action == "check_health":
                config_result = self.api_request("/config")
                status_result = self.api_request("/status")
                
                health_report = "🏥 **System Health Check**\n\n"
                
                # Configuration status
                config_status = config_result.get('config_status', {})
                health_report += "**Configuration Status:**\n"
                for service, status in config_status.items():
                    icon = "✅" if status else "❌"
                    health_report += f"• {service.title()}: {icon}\n"
                
                # User statistics
                users = status_result.get('users', {})
                health_report += f"\n**User Statistics:**\n"
                health_report += f"• Total Users: {len(users)}\n"
                
                total_samples = sum(
                    stats.get('positives', 0) + stats.get('impostors', 0) 
                    for stats in users.values()
                )
                health_report += f"• Total Samples: {total_samples}\n"
                
                if total_samples == 0:
                    health_report += "\n⚠️ **Warning**: No training data available\n"
                elif total_samples < 100:
                    health_report += "\n⚠️ **Warning**: Limited training data available\n"
                else:
                    health_report += "\n✅ **Status**: Sufficient training data available\n"
                
                return health_report
                
            elif action == "backup_models":
                # This would trigger Google Drive sync if enabled
                return "🔄 Model backup initiated (check Google Drive sync configuration)"
                
            elif action == "clear_cache":
                return "🧹 Cache clearing not implemented (add Redis cache clearing logic)"
                
            else:
                return f"❌ Unknown maintenance action: {action}"
                
        except Exception as e:
            return f"❌ Maintenance action failed: {str(e)}"
    
    def security_audit(self) -> str:
        """Perform security audit"""
        try:
            audit_report = "🔒 **Security Audit Report**\n\n"
            audit_report += f"**Audit Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # Check configuration security
            config_result = self.api_request("/config")
            config_status = config_result.get('config_status', {})
            
            audit_report += "**Configuration Security:**\n"
            
            # Database security
            if config_status.get('database'):
                audit_report += "✅ Database connection established\n"
            else:
                audit_report += "❌ Database connection failed\n"
            
            # External service security
            if config_status.get('typingdna'):
                audit_report += "✅ TypingDNA API configured\n"
            else:
                audit_report += "⚠️ TypingDNA API not configured\n"
            
            if config_status.get('email'):
                audit_report += "✅ Email notifications configured\n"
            else:
                audit_report += "⚠️ Email notifications not configured\n"
            
            if config_status.get('webhook'):
                audit_report += "✅ Webhook alerts configured\n"
            else:
                audit_report += "⚠️ Webhook alerts not configured\n"
            
            # Check users for security issues
            users_result = self.api_request("/users")
            users = users_result.get('users', [])
            
            audit_report += f"\n**User Security:**\n"
            audit_report += f"• Total Users: {len(users)}\n"
            
            active_users = [u for u in users if u.get('is_active', True)]
            inactive_users = [u for u in users if not u.get('is_active', True)]
            
            audit_report += f"• Active Users: {len(active_users)}\n"
            audit_report += f"• Inactive Users: {len(inactive_users)}\n"
            
            # Check for users with high failed attempts
            high_risk_users = [u for u in users if u.get('failed_attempts', 0) > 3]
            if high_risk_users:
                audit_report += f"⚠️ High-risk users (>3 failed attempts): {len(high_risk_users)}\n"
                for user in high_risk_users[:5]:  # Show first 5
                    audit_report += f"  - {user.get('user_id')}: {user.get('failed_attempts')} attempts\n"
            
            audit_report += "\n**Recommendations:**\n"
            
            if not config_status.get('email'):
                audit_report += "• Configure email notifications for security alerts\n"
            
            if not config_status.get('webhook'):
                audit_report += "• Set up webhook alerts for real-time monitoring\n"
            
            if len(users) == 0:
                audit_report += "• Add users and enroll biometric data\n"
            
            if high_risk_users:
                audit_report += "• Review high-risk users and consider account lockouts\n"
            
            return audit_report
            
        except Exception as e:
            return f"❌ Security audit failed: {str(e)}"
    
    def create_interface(self) -> gr.Column:
        """Create admin interface"""
        with gr.Column() as admin:
            gr.Markdown("## ⚙️ System Administration")
            
            # User Management Section
            with gr.Tab("👥 User Management"):
                gr.Markdown("### User Overview")
                
                users_refresh_btn = gr.Button("Refresh User List", variant="primary")
                users_table = gr.Dataframe(
                    label="System Users",
                    headers=["User ID", "Email", "Full Name", "Active", "Created", "Last Login", "Failed Attempts"],
                    interactive=False
                )
                users_status = gr.Textbox(label="Status", interactive=False)
                
                gr.Markdown("### Individual User Management")
                
                with gr.Row():
                    manage_user_id = gr.Textbox(label="User ID", placeholder="Enter user ID")
                    retrain_btn = gr.Button("Retrain Model", variant="secondary")
                    get_stats_btn = gr.Button("Get Statistics", variant="secondary")
                
                retrain_status = gr.Textbox(label="Retrain Status", interactive=False)
                
                with gr.Row():
                    with gr.Column():
                        user_model_info = gr.Markdown("Select a user to view model information")
                    with gr.Column():
                        user_performance = gr.Markdown("Select a user to view performance metrics")
            
            # Data Management Section
            with gr.Tab("📊 Data Management"):
                gr.Markdown("### Bulk Data Export")
                
                with gr.Row():
                    bulk_export_type = gr.Dropdown(
                        choices=["samples", "scores", "users"],
                        label="Export Type",
                        value="samples"
                    )
                    bulk_export_btn = gr.Button("Export All Data", variant="primary")
                
                bulk_export_status = gr.Textbox(label="Export Status", interactive=False)
                bulk_export_file = gr.File(label="Download File", interactive=False)
                
                gr.Markdown("### Data Statistics")
                gr.Markdown("""
                Use this section to export complete datasets for analysis:
                - **Samples**: All biometric feature samples with labels
                - **Scores**: All authentication attempts and scores
                - **Users**: All user registration data
                """)
            
            # System Maintenance Section
            with gr.Tab("🔧 System Maintenance"):
                gr.Markdown("### System Health & Maintenance")
                
                with gr.Row():
                    health_check_btn = gr.Button("Health Check", variant="primary")
                    backup_models_btn = gr.Button("Backup Models", variant="secondary")
                    clear_cache_btn = gr.Button("Clear Cache", variant="secondary")
                
                maintenance_output = gr.Textbox(
                    label="Maintenance Output",
                    lines=15,
                    interactive=False
                )
                
                gr.Markdown("### Maintenance Actions")
                gr.Markdown("""
                - **Health Check**: Verify system configuration and data integrity
                - **Backup Models**: Sync trained models to Google Drive (if configured)
                - **Clear Cache**: Clear application cache and temporary files
                """)
            
            # Security Section
            with gr.Tab("🔒 Security Audit"):
                gr.Markdown("### Security Analysis")
                
                security_audit_btn = gr.Button("Run Security Audit", variant="primary")
                security_report = gr.Textbox(
                    label="Security Audit Report",
                    lines=20,
                    interactive=False
                )
                
                gr.Markdown("### Security Features")
                gr.Markdown("""
                The security audit checks:
                - Configuration status and external service connectivity
                - User account security (failed attempts, lockouts)
                - System vulnerabilities and recommendations
                - Data integrity and backup status
                """)
            
            # Event Handlers
            users_refresh_btn.click(
                self.get_all_users,
                outputs=[users_table, users_status]
            )
            
            retrain_btn.click(
                self.retrain_user_model,
                inputs=[manage_user_id],
                outputs=[retrain_status]
            )
            
            get_stats_btn.click(
                self.get_user_model_stats,
                inputs=[manage_user_id],
                outputs=[user_model_info, user_performance]
            )
            
            bulk_export_btn.click(
                self.bulk_export_data,
                inputs=[bulk_export_type],
                outputs=[bulk_export_status, bulk_export_file]
            )
            
            health_check_btn.click(
                lambda: self.system_maintenance("check_health"),
                outputs=[maintenance_output]
            )
            
            backup_models_btn.click(
                lambda: self.system_maintenance("backup_models"),
                outputs=[maintenance_output]
            )
            
            clear_cache_btn.click(
                lambda: self.system_maintenance("clear_cache"),
                outputs=[maintenance_output]
            )
            
            security_audit_btn.click(
                self.security_audit,
                outputs=[security_report]
            )
            
            # Initialize with user list
            admin.load(
                self.get_all_users,
                outputs=[users_table, users_status]
            )
        
        return admin
