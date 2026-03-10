from extensions import db
from datetime import datetime

class Interview(db.Model):
    __tablename__ = "interviews"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"), nullable=False)
    interviewer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    remarks = db.Column(db.Text)
    recommendation = db.Column(db.Enum('recommend','not_recommend'))
    interview_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    application = db.relationship("Application", backref="interviews")
    interviewer = db.relationship("User", backref="interviews_conducted")
    details = db.relationship("Assessment", backref="interview", uselist=False)