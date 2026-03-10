from extensions import db
from datetime import datetime

class HomeVisit(db.Model):
    __tablename__ = "home_visits"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"), nullable=False)
    officer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    visit_notes = db.Column(db.Text)
    verified_income = db.Column(db.Float)
    visit_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    application = db.relationship("Application", backref="home_visits")
    officer = db.relationship("User", backref="home_visits_conducted")