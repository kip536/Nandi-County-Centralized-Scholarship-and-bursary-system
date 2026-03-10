from extensions import db

class Assessment(db.Model):
    __tablename__ = "assessments"
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey("interviews.id"), nullable=False)
    
    # Granular data storage
    housing_score = db.Column(db.Integer)    # Points from housing section
    family_score = db.Column(db.Integer)     # Points from family section
    academic_score = db.Column(db.Integer)   # Points from academic section
    
    # Relationship
    # interview = db.relationship("Interview", backref=db.backref("details", uselist=False))