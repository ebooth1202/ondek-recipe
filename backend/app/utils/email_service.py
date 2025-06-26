import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, Optional
import logging
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_user = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.admin_email = os.getenv("ADMIN_EMAIL")
        self.is_configured = bool(self.email_user and self.email_password and self.admin_email)

        if not self.is_configured:
            logger.warning("Email service not configured - missing EMAIL_USER, EMAIL_PASSWORD, or ADMIN_EMAIL")

    def send_critical_error_alert(self, error_data: Dict[str, Any]) -> bool:
        """Send critical error alert to admin"""
        if not self.is_configured:
            logger.warning("Cannot send email - service not configured")
            return False

        try:
            subject = f"🚨 CRITICAL ERROR - OnDEK Recipe App"

            # Create email body
            body = self._format_critical_error_email(error_data)

            return self._send_email(
                to_email=self.admin_email,
                subject=subject,
                body=body,
                is_html=True
            )
        except Exception as e:
            logger.error(f"Failed to send critical error email: {e}")
            return False

    def send_new_user_report_notification(self, issue_data: Dict[str, Any]) -> bool:
        """Send notification for new user-reported issues"""
        if not self.is_configured:
            return False

        try:
            issue_type = issue_data.get('type', 'Unknown')
            severity = issue_data.get('severity', 'Medium')

            subject = f"📝 New {issue_type.replace('_', ' ').title()} - {severity} Priority"
            body = self._format_user_report_email(issue_data)

            return self._send_email(
                to_email=self.admin_email,
                subject=subject,
                body=body,
                is_html=True
            )
        except Exception as e:
            logger.error(f"Failed to send user report email: {e}")
            return False

    def _format_critical_error_email(self, error_data: Dict[str, Any]) -> str:
        """Format critical error email with HTML"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background-color: #dc3545; color: white; padding: 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 24px;">🚨 Critical Error Alert</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px;">OnDEK Recipe Application</p>
                </div>

                <div style="padding: 30px;">
                    <h2 style="color: #dc3545; margin-top: 0;">Error Details</h2>

                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; width: 30%;">Time:</td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">{error_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Error:</td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">{error_data.get('error_message', 'Unknown error')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">User:</td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">{error_data.get('username', 'Anonymous')} ({error_data.get('user_role', 'unknown')})</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Page:</td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">{error_data.get('page', 'Unknown page')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Endpoint:</td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">{error_data.get('endpoint', 'N/A')}</td>
                        </tr>
                    </table>

                    {f'''
                    <h3 style="color: #333; margin-top: 30px;">Stack Trace</h3>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 4px; border-left: 4px solid #dc3545; font-family: monospace; font-size: 12px; overflow-x: auto; white-space: pre-wrap;">
{error_data.get('stack_trace', 'No stack trace available')}
                    </div>
                    ''' if error_data.get('stack_trace') else ''}

                    <div style="margin-top: 30px; padding: 15px; background-color: #fff3cd; border-radius: 4px; border-left: 4px solid #ffc107;">
                        <p style="margin: 0; color: #856404;"><strong>Action Required:</strong> Please investigate this critical error immediately.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

    def _format_user_report_email(self, issue_data: Dict[str, Any]) -> str:
        """Format user report email with HTML"""
        issue_type = issue_data.get('type', 'Unknown').replace('_', ' ').title()
        severity_color = {
            'critical': '#dc3545',
            'high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#28a745'
        }.get(issue_data.get('severity', 'medium').lower(), '#6c757d')

        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background-color: {severity_color}; color: white; padding: 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 24px;">📝 New {issue_type}</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px;">User Report - {issue_data.get('severity', 'Medium')} Priority</p>
                </div>

                <div style="padding: 30px;">
                    <h2 style="color: #333; margin-top: 0;">{issue_data.get('title', 'No title provided')}</h2>

                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; width: 30%;">Reported By:</td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">{issue_data.get('username', 'Anonymous')} ({issue_data.get('user_role', 'user')})</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Type:</td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">{issue_type}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Severity:</td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;"><span style="color: {severity_color}; font-weight: bold;">{issue_data.get('severity', 'Medium')}</span></td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Time:</td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">{issue_data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Page:</td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">{issue_data.get('page', 'Unknown page')}</td>
                        </tr>
                    </table>

                    <h3 style="color: #333; margin-top: 30px;">Description</h3>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 4px; border-left: 4px solid {severity_color}; line-height: 1.6;">
                        {issue_data.get('description', 'No description provided')}
                    </div>

                    {f'''
                    <h3 style="color: #333; margin-top: 30px;">Tags</h3>
                    <div style="margin-top: 10px;">
                        {' '.join([f'<span style="background-color: #e9ecef; padding: 4px 8px; border-radius: 12px; font-size: 12px; margin-right: 5px;">{tag}</span>' for tag in issue_data.get('tags', [])])}
                    </div>
                    ''' if issue_data.get('tags') else ''}
                </div>
            </div>
        </body>
        </html>
        """

    def _send_email(self, to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """Send email using SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"OnDEK RECIPE <{self.email_user}>"
            msg['To'] = to_email

            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False


# Global email service instance
email_service = EmailService()


def async_email(func):
    """Decorator to send emails asynchronously"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)

    return wrapper