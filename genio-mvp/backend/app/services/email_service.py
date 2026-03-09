"""
Email service using SendGrid.
"""
from typing import Optional
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Try to import SendGrid, but don't fail if not installed
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    logger.warning("SendGrid not installed. Email sending will be logged only.")


class EmailService:
    """Service for sending emails."""
    
    def __init__(self):
        self.api_key = getattr(settings, 'SENDGRID_API_KEY', None)
        self.from_email = getattr(settings, 'FROM_EMAIL', 'noreply@genio.ai')
        self.enabled = SENDGRID_AVAILABLE and self.api_key
        
        if self.enabled:
            self.sg = SendGridAPIClient(self.api_key)
        else:
            self.sg = None
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML body
            text_content: Plain text body (optional)
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            # Log email for development
            logger.info(
                "Email would be sent (SendGrid not configured)",
                to=to_email,
                subject=subject,
                html_preview=html_content[:200] + "..." if len(html_content) > 200 else html_content
            )
            return True
        
        try:
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            if text_content:
                message.add_content(Content("text/plain", text_content))
            
            response = self.sg.send(message)
            
            if response.status_code in [200, 202]:
                logger.info("Email sent successfully", to=to_email, subject=subject)
                return True
            else:
                logger.error(
                    "Failed to send email",
                    to=to_email,
                    status_code=response.status_code,
                    body=response.body
                )
                return False
                
        except Exception as e:
            logger.error("Error sending email", to=to_email, error=str(e))
            return False
    
    async def send_password_reset(self, to_email: str, reset_token: str, reset_url: str) -> bool:
        """Send password reset email."""
        subject = "Reset your Genio password"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Your Password</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #7c3aed;">Genio</h1>
                </div>
                
                <h2>Reset Your Password</h2>
                
                <p>Hello,</p>
                
                <p>We received a request to reset your password for your Genio account. 
                Click the button below to reset it:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background-color: #7c3aed; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="background-color: #f3f4f6; padding: 10px; border-radius: 5px; 
                          word-break: break-all;">
                    {reset_url}
                </p>
                
                <p>This link will expire in 1 hour for security reasons.</p>
                
                <p>If you didn't request a password reset, you can safely ignore this email. 
                Your password will remain unchanged.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                
                <p style="font-size: 12px; color: #6b7280;">
                    Genio Knowledge OS<br>
                    <a href="https://genio.ai">genio.ai</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Reset Your Genio Password

Hello,

We received a request to reset your password. Visit this link to reset it:

{reset_url}

This link will expire in 1 hour.

If you didn't request this, you can safely ignore this email.

Genio Knowledge OS
https://genio.ai
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)
    
    async def send_daily_brief(self, to_email: str, brief_html: str, brief_date: str) -> bool:
        """Send daily brief email."""
        subject = f"Your Daily Brief - {brief_date}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Your Daily Brief</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #7c3aed;">Genio Daily Brief</h1>
                    <p style="color: #6b7280;">{brief_date}</p>
                </div>
                
                {brief_html}
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                
                <p style="font-size: 12px; color: #6b7280; text-align: center;">
                    You're receiving this because you subscribed to Genio Daily Brief.<br>
                    <a href="https://genio.ai/settings">Manage preferences</a> | 
                    <a href="https://genio.ai/unsubscribe">Unsubscribe</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, html_content)
    
    async def send_welcome_email(self, to_email: str, user_name: str) -> bool:
        """Send welcome email to new users."""
        subject = "Welcome to Genio!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to Genio</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #7c3aed;">Welcome to Genio, {user_name}!</h1>
                </div>
                
                <p>We're excited to have you on board. Genio helps you:</p>
                
                <ul>
                    <li>Aggregate content from your favorite sources</li>
                    <li>Discover insights with AI-powered analysis</li>
                    <li>Build your personal knowledge graph</li>
                    <li>Stay informed with personalized daily briefs</li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://genio.ai/onboarding" 
                       style="background-color: #7c3aed; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Complete Setup
                    </a>
                </div>
                
                <p>Need help? Reply to this email or visit our <a href="https://docs.genio.ai">documentation</a>.</p>
                
                <p>Best,<br>The Genio Team</p>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, html_content)


# Singleton instance
email_service = EmailService()
