from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import random
import re
import os
from jose import jwt
from hashlib import sha256
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import email service
try:
    from email_service import send_otp_email, send_welcome_email
    EMAIL_ENABLED = True
except ImportError:
    print("⚠️ Warning: email_service.py not found. Emails will be logged to console only.")
    EMAIL_ENABLED = False


# ----- CONFIG -----
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable not set.")
JWT_ALGO = os.getenv("JWT_ALGO", "HS256")
OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "5"))

router = APIRouter()

# Store OTPs temporarily in-memory (hashed for security)
otp_store = {}  # { email: { otp_hash: str, expires_at: datetime, attempts: int } }

# Track first-time users for welcome email
first_time_users = set()


class SendOtpRequest(BaseModel):
    email: str


class VerifyOtpRequest(BaseModel):
    email: str
    otp: str


class AuthResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None


def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r"^[\w\.-]+@[\w\.-]+\.[\w-]+$"
    return re.match(pattern, email) is not None


def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return str(random.randint(100000, 999999))


def hash_otp(otp: str) -> str:
    """Hash OTP for secure storage"""
    return sha256(otp.encode()).hexdigest()


from fastapi import Request

# --- Lightweight Rate Limiting ---
import time
RATE_LIMIT = {}  # (ip, endpoint): [timestamps]
def check_rate_limit(ip, endpoint, max_req=3, window=10):
    now = time.time()
    key = (ip, endpoint)
    timestamps = RATE_LIMIT.get(key, [])
    # Remove old timestamps
    timestamps = [t for t in timestamps if now - t < window]
    if len(timestamps) >= max_req:
        raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")
    timestamps.append(now)
    RATE_LIMIT[key] = timestamps

@router.post("/send-email-otp", response_model=AuthResponse)
def send_email_otp_endpoint(req: SendOtpRequest, request: Request):
    client_ip = request.client.host
    check_rate_limit(client_ip, 'send-otp')
    """Send OTP via email using Brevo"""
    email = req.email.lower().strip()

    if not is_valid_email(email):
        raise HTTPException(status_code=400, detail="Invalid email format.")

    # Generate OTP
    otp = generate_otp()
    otp_hashed = hash_otp(otp)
    expiry = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    # Store hashed OTP with expiry and attempt counter
    otp_store[email] = {
        "otp_hash": otp_hashed,
        "expires_at": expiry,
        "attempts": 0
    }

    # Send email via Brevo
    if EMAIL_ENABLED:
        try:
            status_code, message = send_otp_email(email, otp)
            if status_code == 201:
                # Track if this is first login
                if email not in first_time_users:
                    first_time_users.add(email)
                return AuthResponse(
                    success=True,
                    message=f"✅ OTP sent to {email}. Check your inbox!",
                    token=None
                )
            else:
                print(f"⚠️ Email send failed for {email}: {message}")
                print(f"📧 OTP for {email}: {otp} (Console fallback)")
                return AuthResponse(
                    success=True,
                    message="Failed to send OTP. Email service not configured or unreachable.",
                    token=None
                )
        except Exception as e:
            print(f"❌ Email error for {email}: {str(e)}")
            print(f"📧 OTP for {email}: {otp} (Console fallback)")
            return AuthResponse(
                success=True,
                message="Failed to send OTP. Email service not configured or unreachable.",
                token=None
            )
    else:
        print(f"📧 [DEVELOPMENT] OTP for {email}: {otp}")
        return AuthResponse(
            success=True,
            message="OTP sent (check console in development mode)",
            token=None
        )


@router.post("/verify-email-otp", response_model=AuthResponse)
def verify_email_otp_endpoint(req: VerifyOtpRequest, request: Request):
    client_ip = request.client.host
    check_rate_limit(client_ip, 'verify-otp')
    """Verify OTP and issue JWT token"""
    email = req.email.lower().strip()

    if email not in otp_store:
        raise HTTPException(status_code=400, detail="OTP expired. Please request a new one.")

    record = otp_store[email]
    
    # Check expiry
    if datetime.utcnow() > record["expires_at"]:
        del otp_store[email]
        raise HTTPException(status_code=400, detail="OTP expired. Please request a new one.")
    
    # Check attempts (max 3 attempts)
    if record["attempts"] >= 3:
        del otp_store[email]
        raise HTTPException(
            status_code=400, 
            detail="Too many failed attempts. Please request a new OTP."
        )
    
    # Verify OTP (compare hashed values)
    entered_otp_hash = hash_otp(req.otp.strip())
    if entered_otp_hash != record["otp_hash"]:
        record["attempts"] += 1
        remaining_attempts = 3 - record["attempts"]
        if remaining_attempts > 0:
            raise HTTPException(
                status_code=400, 
                detail="Invalid OTP. Please try again."
            )
        else:
            del otp_store[email]
            raise HTTPException(
                status_code=400, 
                detail="Too many failed attempts. Please request a new OTP."
            )

    # OTP correct → generate JWT
    token = jwt.encode(
        {
            "email": email,
            "exp": datetime.utcnow() + timedelta(hours=12),
            "iat": datetime.utcnow()
        },
        JWT_SECRET,
        algorithm=JWT_ALGO,
    )

    # Clean up used OTP
    del otp_store[email]
    
    # Send welcome email for first-time users (async, don't block)
    if EMAIL_ENABLED and email in first_time_users:
        try:
            send_welcome_email(email)
            first_time_users.remove(email)
        except Exception as e:
            print(f"⚠️ Welcome email failed for {email}: {str(e)}")

    return AuthResponse(
        success=True,
        message="✅ Login successful!",
        token=token
    )


@router.post("/resend-otp", response_model=AuthResponse)
def resend_otp(req: SendOtpRequest):
    """Resend OTP (same as send-email-otp but with rate limiting)"""
    email = req.email.lower().strip()
    
    # Check if there's an active OTP
    if email in otp_store:
        time_since_last = datetime.utcnow() - (otp_store[email]["expires_at"] - timedelta(minutes=OTP_EXPIRY_MINUTES))
        if time_since_last < timedelta(seconds=30):
            raise HTTPException(
                status_code=429, 
                detail="Please wait 30 seconds before requesting a new OTP."
            )
    
    # Reuse send OTP logic
    return send_email_otp_endpoint(req)
