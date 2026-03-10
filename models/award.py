from extensions import db
from datetime import datetime

class Award(db.Model):
    __tablename__ = "awards"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"), nullable=False, unique=True)
    amount_awarded = db.Column(db.Float, nullable=False)
    disbursement_status = db.Column(db.Enum('pending', 'disbursed'), default='pending')
    approved_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    approved_at = db.Column(db.DateTime)

    # Relationships
    application = db.relationship("Application", backref="award")
    approver = db.relationship("User", backref="awards_approved")