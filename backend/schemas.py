# schemas.py - Pydantic schemas for API request/response validation

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ==================== USER SCHEMAS ====================

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


# ==================== PATIENT SCHEMAS ====================

class PatientCreate(BaseModel):
    patient_hn: str
    name: str
    age: Optional[str] = None
    sex: Optional[str] = "Female"
    date_of_birth: Optional[datetime] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    medical_history: Optional[str] = None


class PatientResponse(BaseModel):
    id: int
    patient_hn: str
    name: str
    age: Optional[str]
    sex: str
    phone: Optional[str]
    email: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[str] = None
    sex: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    medical_history: Optional[str] = None


# ==================== ANALYSIS SCHEMAS ====================

class AnalysisResponse(BaseModel):
    id: int
    filename: Optional[str]
    result: str
    confidence: float
    benign_prob: float
    malignant_prob: float
    risk_level: str
    view_type: Optional[str]
    laterality: Optional[str]
    analyzed_at: datetime

    class Config:
        from_attributes = True


class AnalysisDetailResponse(AnalysisResponse):
    image_width: Optional[int]
    image_height: Optional[int]
    mean_intensity: Optional[float]
    std_intensity: Optional[float]
    brightness: Optional[float]
    contrast: Optional[float]
    findings_json: Optional[str]
    original_image_b64: Optional[str]
    overlay_image_b64: Optional[str]
    heatmap_image_b64: Optional[str]
    bbox_image_b64: Optional[str]


# ==================== REPORT SCHEMAS ====================

class ReportCreate(BaseModel):
    analysis_id: int
    department: Optional[str] = "Radiology"
    request_doctor: Optional[str] = None
    report_by: Optional[str] = None


class ReportResponse(BaseModel):
    id: int
    report_number: str
    analysis_id: int
    department: str
    request_doctor: Optional[str]
    report_by: Optional[str]
    generated_at: datetime

    class Config:
        from_attributes = True


# ==================== AUTH SCHEMAS ====================

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None


# ==================== DASHBOARD SCHEMAS ====================

class DashboardStats(BaseModel):
    total_analyses: int
    total_patients: int
    total_reports: int
    malignant_count: int
    benign_count: int
    high_risk_count: int
    recent_analyses: List[AnalysisResponse]
