from typing import List, Optional
from pydantic import BaseModel, EmailStr


# ---------- Scam Report Schemas ----------

class ScamReportBase(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    description: str

class ScamReportCreate(ScamReportBase):
    pass

class ScamReport(ScamReportBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True


# ---------- User Schemas ----------

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    scam_reports: List[ScamReport] = []

    class Config:
        from_attributes = True

# ---------- Token Schemas ----------

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class OTPSendRequest(BaseModel):
    phone_number: str

class OTPVerifyRequest(BaseModel):
    phone_number: str
    otp: str

# ---------- Email OTP Schemas ----------

class EmailOTPRequest(BaseModel):
    email: EmailStr

class EmailOTPVerify(BaseModel):
    email: EmailStr
    otp: str