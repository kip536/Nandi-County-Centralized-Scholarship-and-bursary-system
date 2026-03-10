from extensions import db
from datetime import datetime

class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey("applicants.id"), nullable=False)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarships.id"), nullable=False)
    application_year = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum('pending','interviewed','verified','rejected','approved'), default='pending')
    score = db.Column(db.Float)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    scholarship = db.relationship("Scholarship", backref="applications")
    applicant = db.relationship("Applicant", backref="applications")
    reviewer = db.relationship("User", backref="reviewed_applications")