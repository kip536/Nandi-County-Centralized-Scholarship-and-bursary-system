from extensions import db
from datetime import datetime

class Applicant(db.Model):
    __tablename__ = "applicants"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    national_id = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    dob = db.Column(db.Date)
    gender = db.Column(db.Enum('male','female','other'))
    sub_county = db.Column(db.String(100))
    ward = db.Column(db.String(100))
    school_name = db.Column(db.String(200))
    education_level = db.Column(db.Enum('secondary','tertiary','university'))
    guardian_name = db.Column(db.String(150))
    guardian_phone = db.Column(db.String(20))
    annual_income = db.Column(db.Float)
    is_orphan = db.Column(db.Boolean, default=False)
    has_disability = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="profile")