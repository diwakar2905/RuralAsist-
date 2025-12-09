"""
Email Service using Brevo (formerly Sendinblue)
Handles all email sending operations including OTP delivery
"""

import os
import requests
from dotenv import load_dotenv
from typing import Tuple

# Load environment variables
load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@ruralassist.com")
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def send_otp_email(receiver_email: str, otp: str, user_name: str = None) -> Tuple[int, str]:
    """
    Send OTP email via Brevo API
    
    Args:
        receiver_email: Recipient email address
        otp: 6-digit OTP code
        user_name: Optional user name for personalization
    
    Returns:
        Tuple of (status_code, message)
    """
    
    # Validate API key
    if not BREVO_API_KEY or BREVO_API_KEY in {
        "your_brevo_api_key_here",
        "your_actual_brevo_api_key_here"
    }:
        return 500, "❌ Email service not configured. Please set BREVO_API_KEY."
    
    # Prepare email payload
    payload = {
        "sender": {
            "name": "RuralAssist",
            "email": SENDER_EMAIL
        },
        "to": [
            {"email": receiver_email, "name": user_name or receiver_email.split('@')[0]}
        ],
        "subject": "🔐 Your RuralAssist Login OTP",
        "htmlContent": f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin:0;padding:0;font-family:'Inter','Arial',sans-serif;background-color:#f8fafc;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f8fafc;padding:40px 20px;">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:16px;box-shadow:0 4px 20px rgba(0,0,0,0.08);overflow:hidden;">
                            
                            <!-- Header -->
                            <tr>
                                <td style="background:linear-gradient(135deg, #34A853, #2E8E46);padding:32px 40px;text-align:center;">
                                    <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:700;">RuralAssist</h1>
                                    <p style="margin:8px 0 0;color:rgba(255,255,255,0.9);font-size:14px;">Empowering Rural India 🇮🇳</p>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding:40px;">
                                    <h2 style="margin:0 0 16px;color:#1a1a1a;font-size:22px;font-weight:600;">Login Verification Code</h2>
                                    <p style="margin:0 0 24px;color:#6b7280;font-size:15px;line-height:1.6;">
                                        Hello{' ' + user_name if user_name else ''},<br><br>
                                        You requested a One-Time Password (OTP) to log in to your RuralAssist account. 
                                        Use the code below to complete your login:
                                    </p>
                                    
                                    <!-- OTP Box -->
                                    <table width="100%" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td align="center" style="padding:24px 0;">
                                                <div style="background:linear-gradient(135deg, rgba(52,168,83,0.1), rgba(46,142,70,0.1));border:2px solid #34A853;border-radius:12px;padding:24px;display:inline-block;">
                                                    <p style="margin:0 0 8px;color:#6b7280;font-size:13px;text-transform:uppercase;letter-spacing:1px;">Your OTP</p>
                                                    <h1 style="margin:0;color:#34A853;font-size:42px;font-weight:700;letter-spacing:8px;">{otp}</h1>
                                                </div>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <!-- Warning Box -->
                                    <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:24px;">
                                        <tr>
                                            <td style="background:rgba(239,68,68,0.05);border-left:4px solid #EF4444;padding:16px;border-radius:8px;">
                                                <p style="margin:0;color:#dc2626;font-size:14px;font-weight:600;">⏰ Important:</p>
                                                <p style="margin:8px 0 0;color:#6b7280;font-size:13px;line-height:1.5;">
                                                    • This OTP expires in <strong>5 minutes</strong><br>
                                                    • Never share this code with anyone<br>
                                                    • RuralAssist will never ask for your OTP via phone or email
                                                </p>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <p style="margin:24px 0 0;color:#9ca3af;font-size:13px;line-height:1.6;">
                                        If you didn't request this code, please ignore this email. Your account is safe.
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="background:#f8fafc;padding:24px 40px;border-top:1px solid #e5e7eb;">
                                    <p style="margin:0;color:#9ca3af;font-size:12px;text-align:center;line-height:1.6;">
                                        © 2025 RuralAssist | Made in India 🇮🇳<br>
                                        <a href="{os.getenv('FRONTEND_URL', 'http://localhost:5500')}" style="color:#34A853;text-decoration:none;">Visit Website</a> •
                                        <a href="{os.getenv('FRONTEND_URL', 'http://localhost:5500')}/privacy.html" style="color:#34A853;text-decoration:none;">Privacy Policy</a>
                                    </p>
                                </td>
                            </tr>
                            
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """,
        "textContent": f"""
RuralAssist - Login Verification Code

Hello{' ' + user_name if user_name else ''},

Your OTP for RuralAssist login is: {otp}

This OTP expires in 5 minutes.

Important:

If you didn't request this code, please ignore this email.

© 2025 RuralAssist | Made in India
        """
    }
    
    # Headers for Brevo API
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    
    try:
        # Send email via Brevo
        response = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 201:
            return 201, f"✅ OTP sent successfully to {receiver_email}"
        else:
            error_msg = response.json().get('message', 'Unknown error')
            return response.status_code, f"❌ Email send failed: {error_msg}"
            
    except requests.exceptions.Timeout:
        return 500, "❌ Email service timeout. Please try again."
    except requests.exceptions.ConnectionError:
        return 500, "❌ Cannot connect to email service. Check your internet connection."
    except Exception as e:
        return 500, f"❌ Email send error: {str(e)}"


def send_welcome_email(receiver_email: str, user_name: str = None) -> Tuple[int, str]:
    """
    Send welcome email to new users
    
    Args:
        receiver_email: Recipient email address
        user_name: User's name
    
    Returns:
        Tuple of (status_code, message)
    """
    
    if not BREVO_API_KEY or BREVO_API_KEY in {
        "your_brevo_api_key_here",
        "your_actual_brevo_api_key_here"
    }:
        return 500, "❌ Email service not configured. Please set BREVO_API_KEY."
    
    payload = {
        "sender": {"name": "RuralAssist", "email": SENDER_EMAIL},
        "to": [{"email": receiver_email, "name": user_name or receiver_email.split('@')[0]}],
        "subject": "🎉 Welcome to RuralAssist!",
        "htmlContent": f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family:Arial,sans-serif;background-color:#f8fafc;padding:40px 20px;">
            <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:16px;padding:40px;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
                <h1 style="color:#34A853;margin:0 0 24px;">Welcome to RuralAssist! 🎉</h1>
                <p style="color:#6b7280;font-size:15px;line-height:1.6;">
                    Hi {user_name or 'there'},<br><br>
                    Thank you for joining RuralAssist! We're excited to help you access government schemes, digital services, and AI-powered assistance.
                </p>
                <h3 style="color:#1a1a1a;margin:24px 0 16px;">What you can do:</h3>
                <ul style="color:#6b7280;font-size:14px;line-height:1.8;">
                    <li>🏛️ Browse 50+ Government Schemes</li>
                    <li>📄 Scan Documents with OCR</li>
                    <li>🛡️ Detect & Report Scams</li>
                    <li>💬 Chat with AI Assistant</li>
                    <li>❓ Access FAQs & Support</li>
                </ul>
                <a href="{os.getenv('FRONTEND_URL', 'http://localhost:5500')}" 
                   style="display:inline-block;margin:24px 0;padding:14px 32px;background:#34A853;color:#fff;text-decoration:none;border-radius:50px;font-weight:600;">
                    Get Started
                </a>
                <p style="color:#9ca3af;font-size:12px;margin:32px 0 0;border-top:1px solid #e5e7eb;padding-top:24px;">
                    © 2025 RuralAssist | Made in India 🇮🇳
                </p>
            </div>
        </body>
        </html>
        """
    }
    
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    
    try:
        response = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=10)
        return response.status_code, "Welcome email sent" if response.status_code == 201 else "Failed"
    except Exception as e:
        return 500, str(e)
