from app import create_app
from models.user import User
from werkzeug.security import generate_password_hash
from extensions import db

app = create_app()

with app.app_context():
    # Check if admin exists
    admin = User.query.filter_by(role='admin').first()
    if admin:
        print(f"Admin user already exists: {admin.email}")
    else:
        # Create admin user
        admin_user = User(
            full_name='Administrator',
            email='admin@nandi.edu',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created successfully!")
        print("Email: admin@nandi.edu")
        print("Password: admin123")