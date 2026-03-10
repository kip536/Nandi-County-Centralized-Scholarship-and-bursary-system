from extensions import db
from datetime import datetime

class Scholarship(db.Model):
    __tablename__ = "scholarships"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Float)
    deadline = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # If you want to track which admin posted it
    posted_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = db.relationship("User", backref="posted_scholarships")