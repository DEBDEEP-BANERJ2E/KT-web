"""
Dashboard component for Behavioral Biometrics System
"""

import json
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import gradio as gr


class BiometricsDashboard:
    """Dashboard for biometric analytics and monitoring"""
    
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
    
    def get_user_metrics(self, user_id: str) -> Tuple[Dict, str]:
        """Get user authentication metrics"""
        if not user_id.strip():
            return {}, "Please enter a User ID"
        
        result = self.api_request(f"/users/{user_id.strip()}/metrics")
        
        if "error" in result:
            return {}, f"Error: {result['error']}"
        
        metrics = result.get('metrics', {})
        if not metrics.get('timestamps'):
            return {}, f"No authentication data found for user: {user_id}"
        
        return metrics, f"Loaded {len(metrics['timestamps'])} authentication records"
    
    def create_score_timeline(self, user_id: str) -> Tuple[go.Figure, str]:
        """Create score timeline chart"""
        metrics, status = self.get_user_metrics(user_id)
        
        if not metrics:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=20
            )
            fig.update_layout(title="Authentication Score Timeline")
            return fig, status
        
        timestamps = [datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in metrics['timestamps']]
        scores = metrics['scores']
        verdicts = metrics['verdicts']
        risk_levels = metrics['risk_levels']
        
        # Create color map for verdicts
        colors = []
        for verdict in verdicts:
            if verdict == 'genuine':
                colors.append('green')
            elif verdict == 'impostor':
                colors.append('red')
            else:
                colors.append('orange')
        
        fig = go.Figure()
        
        # Add score line
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=scores,
            mode='lines+markers',
            name='Authentication Score',
            line=dict(color='blue', width=2),
            marker=dict(
                size=8,
                color=colors,
                line=dict(width=2, color='white')
            ),
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Time: %{x}<br>' +
                         'Score: %{y:.2f}<br>' +
                         'Verdict: %{customdata[0]}<br>' +
                         'Risk: %{customdata[1]}<extra></extra>',
            customdata=list(zip(verdicts, risk_levels))
        ))
        
        # Add threshold lines
        fig.add_hline(y=0.6, line_dash="dash", line_color="green", 
                     annotation_text="Genuine Threshold (0.6)")
        fig.add_hline(y=0.3, line_dash="dash", line_color="red",
                     annotation_text="Impostor Threshold (0.3)")
        
        fig.update_layout(
            title=f"Authentication Score Timeline - {user_id}",
            xaxis_title="Time",
            yaxis_title="Authentication Score",
            yaxis=dict(range=[0, 1]),
            hovermode='x unified',
            template='plotly_white'
        )
        
        return fig, status
    
    def create_risk_distribution(self, user_id: str) -> Tuple[go.Figure, str]:
        """Create risk level distribution chart"""
        metrics, status = self.get_user_metrics(user_id)
        
        if not metrics:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=20
            )
            fig.update_layout(title="Risk Level Distribution")
            return fig, status
        
        risk_levels = metrics['risk_levels']
        risk_counts = pd.Series(risk_levels).value_counts()
        
        colors = {
            'low': 'green',
            'medium': 'orange', 
            'high': 'red',
            'critical': 'darkred'
        }
        
        fig = go.Figure(data=[
            go.Bar(
                x=risk_counts.index,
                y=risk_counts.values,
                marker_color=[colors.get(level, 'gray') for level in risk_counts.index],
                text=risk_counts.values,
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title=f"Risk Level Distribution - {user_id}",
            xaxis_title="Risk Level",
            yaxis_title="Count",
            template='plotly_white'
        )
        
        return fig, status
    
    def create_verdict_pie_chart(self, user_id: str) -> Tuple[go.Figure, str]:
        """Create verdict distribution pie chart"""
        metrics, status = self.get_user_metrics(user_id)
        
        if not metrics:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=20
            )
            fig.update_layout(title="Verdict Distribution")
            return fig, status
        
        verdicts = metrics['verdicts']
        verdict_counts = pd.Series(verdicts).value_counts()
        
        colors = {
            'genuine': 'green',
            'impostor': 'red',
            'uncertain': 'orange'
        }
        
        fig = go.Figure(data=[
            go.Pie(
                labels=verdict_counts.index,
                values=verdict_counts.values,
                marker_colors=[colors.get(verdict, 'gray') for verdict in verdict_counts.index],
                textinfo='label+percent',
                hovertemplate='<b>%{label}</b><br>' +
                             'Count: %{value}<br>' +
                             'Percentage: %{percent}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title=f"Verdict Distribution - {user_id}",
            template='plotly_white'
        )
        
        return fig, status
    
    def get_system_overview(self) -> Tuple[str, str, str]:
        """Get system overview statistics"""
        try:
            # Get all users
            users_result = self.api_request("/users")
            users = users_result.get('users', [])
            
            # Get system status
            status_result = self.api_request("/status")
            user_stats = status_result.get('users', {})
            
            # Calculate overview stats
            total_users = len(users)
            active_users = len([u for u in users if u.get('is_active', True)])
            
            total_samples = sum(stats.get('positives', 0) + stats.get('impostors', 0) 
                              for stats in user_stats.values())
            total_positives = sum(stats.get('positives', 0) for stats in user_stats.values())
            total_negatives = sum(stats.get('impostors', 0) for stats in user_stats.values())
            
            # System health
            health_status = "🟢 Healthy"
            if total_users == 0:
                health_status = "🟡 No Users"
            elif total_samples < 10:
                health_status = "🟡 Limited Data"
            
            overview = f"""
            📊 **System Overview**
            
            👥 **Users**: {total_users} total, {active_users} active
            📈 **Samples**: {total_samples} total ({total_positives} positive, {total_negatives} negative)
            🏥 **Health**: {health_status}
            """
            
            # Recent activity summary
            recent_activity = "📅 **Recent Activity**\n\n"
            if user_stats:
                for user_id, stats in list(user_stats.items())[:5]:
                    recent_activity += f"• {user_id}: {stats.get('positives', 0)} enrollments\n"
            else:
                recent_activity += "No recent activity"
            
            # Configuration status
            config_result = self.api_request("/config")
            config_status = config_result.get('config_status', {})
            
            config_info = "⚙️ **Configuration**\n\n"
            config_info += f"• Database: {'✅' if config_status.get('database') else '❌'}\n"
            config_info += f"• TypingDNA: {'✅' if config_status.get('typingdna') else '❌'}\n"
            config_info += f"• Email: {'✅' if config_status.get('email') else '❌'}\n"
            config_info += f"• Webhook: {'✅' if config_status.get('webhook') else '❌'}\n"
            config_info += f"• Google Drive: {'✅' if config_status.get('google_drive') else '❌'}\n"
            
            return overview, recent_activity, config_info
            
        except Exception as e:
            error_msg = f"❌ Error loading system overview: {str(e)}"
            return error_msg, "", ""
    
    def create_system_metrics_chart(self) -> go.Figure:
        """Create system-wide metrics chart"""
        try:
            status_result = self.api_request("/status")
            user_stats = status_result.get('users', {})
            
            if not user_stats:
                fig = go.Figure()
                fig.add_annotation(
                    text="No user data available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, xanchor='center', yanchor='middle',
                    showarrow=False, font_size=20
                )
                fig.update_layout(title="System Metrics")
                return fig
            
            users = list(user_stats.keys())
            positives = [stats.get('positives', 0) for stats in user_stats.values()]
            negatives = [stats.get('impostors', 0) for stats in user_stats.values()]
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Positive Samples',
                x=users,
                y=positives,
                marker_color='green'
            ))
            
            fig.add_trace(go.Bar(
                name='Negative Samples',
                x=users,
                y=negatives,
                marker_color='red'
            ))
            
            fig.update_layout(
                title='User Sample Distribution',
                xaxis_title='Users',
                yaxis_title='Sample Count',
                barmode='stack',
                template='plotly_white'
            )
            
            return fig
            
        except Exception as e:
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            fig.update_layout(title="System Metrics - Error")
            return fig
    
    def create_interface(self) -> gr.Column:
        """Create dashboard interface"""
        with gr.Column() as dashboard:
            gr.Markdown("## 📊 System Dashboard")
            
            # System Overview
            with gr.Row():
                overview_btn = gr.Button("Refresh Overview", variant="primary")
                
            with gr.Row():
                with gr.Column():
                    system_overview = gr.Markdown("Loading system overview...")
                with gr.Column():
                    recent_activity = gr.Markdown("Loading recent activity...")
                with gr.Column():
                    config_info = gr.Markdown("Loading configuration...")
            
            # System Metrics Chart
            system_chart = gr.Plot(label="System Metrics")
            
            gr.Markdown("---")
            
            # User Analytics
            gr.Markdown("## 👤 User Analytics")
            
            with gr.Row():
                metrics_user_id = gr.Textbox(label="User ID", placeholder="Enter user ID for detailed analytics")
                refresh_btn = gr.Button("Refresh Charts", variant="secondary")
            
            with gr.Row():
                with gr.Column():
                    score_timeline = gr.Plot(label="Score Timeline")
                with gr.Column():
                    risk_distribution = gr.Plot(label="Risk Distribution")
            
            verdict_pie = gr.Plot(label="Verdict Distribution")
            
            # Real-time updates
            gr.Markdown("### 🔄 Real-time Monitoring")
            gr.Markdown("Charts update automatically every 30 seconds when monitoring is enabled.")
            
            # Event handlers
            overview_btn.click(
                self.get_system_overview,
                outputs=[system_overview, recent_activity, config_info]
            )
            
            overview_btn.click(
                self.create_system_metrics_chart,
                outputs=[system_chart]
            )
            
            refresh_btn.click(
                self.create_score_timeline,
                inputs=[metrics_user_id],
                outputs=[score_timeline]
            )
            
            refresh_btn.click(
                self.create_risk_distribution,
                inputs=[metrics_user_id],
                outputs=[risk_distribution]
            )
            
            refresh_btn.click(
                self.create_verdict_pie_chart,
                inputs=[metrics_user_id],
                outputs=[verdict_pie]
            )
            
            # Initialize with system overview
            dashboard.load(
                self.get_system_overview,
                outputs=[system_overview, recent_activity, config_info]
            )
            
            dashboard.load(
                self.create_system_metrics_chart,
                outputs=[system_chart]
            )
        
        return dashboard
