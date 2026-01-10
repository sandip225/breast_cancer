# database.py - Database configuration and models

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment variables")

# Database URL - Use environment variable or default to SQLite
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./breast_cancer.db")

# For PostgreSQL on production, use:
# DATABASE_URL = "postgresql://user:password@localhost/breast_cancer_db"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==================== MODELS ====================

class User(Base):
    """User authentication and profile"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user")  # user, doctor, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    analyses = relationship("Analysis", back_populates="user")
    patients = relationship("Patient", back_populates="created_by_user")


class Patient(Base):
    """Patient information for medical reports"""
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_hn = Column(String(100), unique=True, index=True)  # Hospital Number
    name = Column(String(255), nullable=False)
    age = Column(String(20))
    sex = Column(String(20), default="Female")
    date_of_birth = Column(DateTime)
    phone = Column(String(50))
    email = Column(String(255))
    address = Column(Text)
    medical_history = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    created_by_user = relationship("User", back_populates="patients")
    analyses = relationship("Analysis", back_populates="patient")


class Analysis(Base):
    """Mammogram analysis results"""
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    
    # Image information
    filename = Column(String(255))
    file_format = Column(String(50))
    image_width = Column(Integer)
    image_height = Column(Integer)
    
    # Analysis results
    result = Column(String(100))  # "Malignant (Cancerous)" or "Benign (Non-Cancerous)"
    confidence = Column(Float)
    benign_prob = Column(Float)
    malignant_prob = Column(Float)
    risk_level = Column(String(50))
    risk_icon = Column(String(10))
    risk_color = Column(String(20))
    
    # View analysis (CC/MLO)
    view_type = Column(String(50))  # CC, MLO, L-MLO, R-MLO, etc.
    laterality = Column(String(20))  # Left, Right
    
    # Image statistics
    mean_intensity = Column(Float)
    std_intensity = Column(Float)
    min_intensity = Column(Float)
    max_intensity = Column(Float)
    brightness = Column(Float)
    contrast = Column(Float)
    
    # Detailed findings (JSON stored as text)
    findings_json = Column(Text)
    
    # Images stored as base64 (optional - can be large)
    original_image_b64 = Column(Text)
    overlay_image_b64 = Column(Text)
    heatmap_image_b64 = Column(Text)
    bbox_image_b64 = Column(Text)
    
    # Timestamps
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="analyses")
    patient = relationship("Patient", back_populates="analyses")
    reports = relationship("Report", back_populates="analysis")


class Report(Base):
    """Generated PDF reports history"""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"))
    
    # Report metadata
    report_number = Column(String(100), unique=True, index=True)
    
    # Doctor information
    department = Column(String(100), default="Radiology")
    request_doctor = Column(String(255))
    report_by = Column(String(255))
    
    # Report content (PDF stored as binary)
    pdf_data = Column(LargeBinary)
    
    # Timestamps
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="reports")


class UploadHistory(Base):
    """Track upload history for users"""
    __tablename__ = "upload_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String(255))
    file_size = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=True)


class AuditLog(Base):
    """Audit log for tracking user actions"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100))  # login, logout, analyze, generate_report, etc.
    details = Column(Text)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== DATABASE FUNCTIONS ====================

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create tables on import
if __name__ == "__main__":
    create_tables()
