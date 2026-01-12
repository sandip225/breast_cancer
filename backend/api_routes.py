# api_routes.py - API routes for database operations

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import timedelta
import json

from database import get_db, User, Patient, Analysis, Report, AuditLog
from schemas import (
    UserCreate, UserResponse, UserUpdate, UserLogin,
    PatientCreate, PatientResponse, PatientUpdate,
    AnalysisResponse, AnalysisDetailResponse,
    ReportResponse, Token, DashboardStats
)
from auth import (
    authenticate_user, create_user, create_access_token,
    get_current_active_user, get_optional_user, get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Create routers
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
users_router = APIRouter(prefix="/users", tags=["Users"])
patients_router = APIRouter(prefix="/patients", tags=["Patients"])
analyses_router = APIRouter(prefix="/analyses", tags=["Analyses"])
reports_router = APIRouter(prefix="/reports", tags=["Reports"])
dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# ==================== AUTH ROUTES ====================

@auth_router.post("/signup", response_model=UserResponse)
async def signup(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = create_user(db, user_data.email, user_data.name, user_data.password)
    
    # Get IP address (check forwarded header first, then client)
    ip_address = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if not ip_address:
        ip_address = request.client.host if request.client else "unknown"
    
    # Log the signup
    audit = AuditLog(
        user_id=user.id, 
        action="signup", 
        details="New user registered",
        ip_address=ip_address,
        user_agent=request.headers.get("user-agent", "")[:500]
    )
    db.add(audit)
    db.commit()
    
    return user


@auth_router.post("/login", response_model=Token)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    # Get IP address
    ip_address = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if not ip_address:
        ip_address = request.client.host if request.client else "unknown"
    
    # Log the login
    audit = AuditLog(
        user_id=user.id, 
        action="login", 
        details="User logged in",
        ip_address=ip_address,
        user_agent=request.headers.get("user-agent", "")[:500]
    )
    db.add(audit)
    db.commit()
    
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/login/json", response_model=Token)
async def login_json(user_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    """Login with JSON body (for frontend)"""
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    # Get IP address
    ip_address = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if not ip_address:
        ip_address = request.client.host if request.client else "unknown"
    
    # Log the login
    audit = AuditLog(
        user_id=user.id, 
        action="login", 
        details="User logged in via JSON",
        ip_address=ip_address,
        user_agent=request.headers.get("user-agent", "")[:500]
    )
    db.add(audit)
    db.commit()
    
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current user profile"""
    return current_user


# ==================== USER ROUTES ====================

@users_router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@users_router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_data.name:
        user.name = user_data.name
    if user_data.email:
        user.email = user_data.email
    if user_data.password:
        user.password_hash = get_password_hash(user_data.password)
    
    db.commit()
    db.refresh(user)
    return user


# ==================== PATIENT ROUTES ====================

@patients_router.post("/", response_model=PatientResponse)
async def create_patient(
    patient_data: PatientCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new patient"""
    # Check if patient HN exists
    existing = db.query(Patient).filter(Patient.patient_hn == patient_data.patient_hn).first()
    if existing:
        raise HTTPException(status_code=400, detail="Patient HN already exists")
    
    patient = Patient(
        **patient_data.dict(),
        created_by=current_user.id
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@patients_router.get("/", response_model=List[PatientResponse])
async def get_patients(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all patients"""
    query = db.query(Patient)
    if search:
        query = query.filter(
            (Patient.name.ilike(f"%{search}%")) |
            (Patient.patient_hn.ilike(f"%{search}%"))
        )
    patients = query.offset(skip).limit(limit).all()
    return patients


@patients_router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific patient"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@patients_router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a patient"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    for key, value in patient_data.dict(exclude_unset=True).items():
        setattr(patient, key, value)
    
    db.commit()
    db.refresh(patient)
    return patient


@patients_router.delete("/{patient_id}")
async def delete_patient(
    patient_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a patient"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    db.delete(patient)
    db.commit()
    return {"message": "Patient deleted successfully"}


# ==================== ANALYSIS ROUTES ====================

@analyses_router.get("/", response_model=List[AnalysisResponse])
async def get_analyses(
    skip: int = 0,
    limit: int = 100,
    patient_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all analyses"""
    query = db.query(Analysis).filter(Analysis.user_id == current_user.id)
    if patient_id:
        query = query.filter(Analysis.patient_id == patient_id)
    analyses = query.order_by(Analysis.analyzed_at.desc()).offset(skip).limit(limit).all()
    return analyses


@analyses_router.get("/{analysis_id}", response_model=AnalysisDetailResponse)
async def get_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific analysis with full details"""
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@analyses_router.delete("/{analysis_id}")
async def delete_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an analysis"""
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    db.delete(analysis)
    db.commit()
    return {"message": "Analysis deleted successfully"}


# ==================== REPORT ROUTES ====================

@reports_router.get("/", response_model=List[ReportResponse])
async def get_reports(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all reports"""
    reports = db.query(Report).join(Analysis).filter(
        Analysis.user_id == current_user.id
    ).order_by(Report.generated_at.desc()).offset(skip).limit(limit).all()
    return reports


@reports_router.get("/{report_id}")
async def get_report_pdf(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific report PDF"""
    report = db.query(Report).join(Analysis).filter(
        Report.id == report_id,
        Analysis.user_id == current_user.id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    from fastapi.responses import Response
    return Response(
        content=report.pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="report_{report.report_number}.pdf"'}
    )


# ==================== DASHBOARD ROUTES ====================

@dashboard_router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics"""
    total_analyses = db.query(Analysis).filter(Analysis.user_id == current_user.id).count()
    total_patients = db.query(Patient).filter(Patient.created_by == current_user.id).count()
    total_reports = db.query(Report).join(Analysis).filter(Analysis.user_id == current_user.id).count()
    
    malignant_count = db.query(Analysis).filter(
        Analysis.user_id == current_user.id,
        Analysis.result.ilike("%malignant%")
    ).count()
    
    benign_count = db.query(Analysis).filter(
        Analysis.user_id == current_user.id,
        Analysis.result.ilike("%benign%")
    ).count()
    
    high_risk_count = db.query(Analysis).filter(
        Analysis.user_id == current_user.id,
        Analysis.risk_level.in_(["High Risk", "Very High Risk", "Moderate-High Risk"])
    ).count()
    
    recent_analyses = db.query(Analysis).filter(
        Analysis.user_id == current_user.id
    ).order_by(Analysis.analyzed_at.desc()).limit(5).all()
    
    return DashboardStats(
        total_analyses=total_analyses,
        total_patients=total_patients,
        total_reports=total_reports,
        malignant_count=malignant_count,
        benign_count=benign_count,
        high_risk_count=high_risk_count,
        recent_analyses=recent_analyses
    )
