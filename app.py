from datetime import date, datetime

from flask import Flask, render_template, request, redirect, url_for, flash, session
from extensions import db, migrate
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from models.applicant import Applicant
from models.application import Application
from models.assessment import Assessment
from models.award import Award
from models.interview import Interview
from models.scholarship import Scholarship
from models.user import User
from flask_login import LoginManager, login_required, current_user, login_user, logout_user

# Database credentials
MYSQL_USER = "root"
MYSQL_PASSWORD = "root"
MYSQL_HOST = "127.0.0.1"
MYSQL_DB = "nandi_scholarship_db"

def create_database_if_not_exists(user, password, host, db_name):
    conn = pymysql.connect(
        host=host,
        user=user,
        password=password,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    conn.autocommit(True)
    with conn.cursor() as cursor:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    conn.close()

def create_app():
    # Ensure database exists
    create_database_if_not_exists(MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DB)

    app = Flask(__name__)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"

    # Secret key for sessions and flash messages
    app.config['SECRET_KEY'] = 'supersecret123'  # replace with a strong, random key

    # Configure MySQL connection (replace with your credentials)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@127.0.0.1/nandi_scholarship_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Import models to register with SQLAlchemy
    from models import applicant, application, interview, home_visit, award, audit_log, scholarship, assessment

    # Simple test route
    @app.route('/')
    def landing_page():
        return render_template("landing_page.html")
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            full_name = request.form['full_name']
            email = request.form['email']
            phone = request.form.get('phone')  # optional
            password = request.form['password']
            confirm_password = request.form['confirm_password']

            if password != confirm_password:
                flash("Passwords do not match!", "danger")
                return redirect(url_for('register'))

            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash("Email already registered!", "warning")
                return redirect(url_for('register'))

            # Create new user as applicant
            new_user = User(
                full_name=full_name,
                email=email,
                phone=phone,
                password_hash=generate_password_hash(password),
                role='applicant'
            )
            db.session.add(new_user)
            db.session.commit()

            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))

        return render_template('register.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']

            # Find user by email
            user = User.query.filter_by(email=email).first()

            if user and check_password_hash(user.password_hash, password):
                # Set session variables
                login_user(user)

                flash(f"Welcome, {user.full_name}!", "success")

                # Redirect based on role
                if user.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user.role == 'auditor':
                    return redirect(url_for('auditor_dashboard'))
                elif user.role == 'reviewer':
                    return redirect(url_for('reviewer_dashboard'))
                elif user.role == 'applicant':
                    return redirect(url_for('applicant_dashboard'))
                elif user.role == 'field_officer':
                    return redirect(url_for('field_officer_dashboard'))
                else:
                    return redirect(url_for('login'))
            else:
                flash("Invalid email or password.", "danger")
        return render_template('login.html')
    
    # Admin dashboard with user creation
    @app.route('/admin', methods=['GET', 'POST'])
    @login_required
    def admin_dashboard():
        # Check if user is admin
        if current_user.role != 'admin':
            flash("Access denied. Admin privileges required.", "danger")
            return redirect(url_for('login'))

        if request.method == 'POST':
            full_name = request.form['full_name']
            email = request.form['email']
            phone = request.form.get('phone')
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            role = request.form['role']

            # Validate role
            allowed_roles = ['reviewer', 'field_officer', 'auditor']
            if role not in allowed_roles:
                flash("Invalid role selected.", "danger")
                return redirect(url_for('admin_dashboard'))

            if password != confirm_password:
                flash("Passwords do not match!", "danger")
                return redirect(url_for('admin_dashboard'))

            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash("Email already registered!", "warning")
                return redirect(url_for('admin_dashboard'))

            # Create new user with specified role
            new_user = User(
                full_name=full_name,
                email=email,
                phone=phone,
                password_hash=generate_password_hash(password),
                role=role
            )
            db.session.add(new_user)
            db.session.commit()

            flash(f"User {full_name} created successfully with role {role.replace('_', ' ').title()}.", "success")
            return redirect(url_for('admin_dashboard'))

        # GET request - display dashboard with users list
        # Get all users except applicants for admin view
        users = User.query.filter(User.role.in_(['admin', 'reviewer', 'field_officer', 'auditor', 'applicant'])).order_by(User.created_at.desc()).all()

        return render_template('admin_dashboard.html', users=users)
    
    # Route to delete a user
    @app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
    @login_required
    def delete_user(user_id):
        if current_user.role != 'admin':
            flash("Access denied.", "danger")
            return redirect(url_for('login'))
        
        user = User.query.get_or_404(user_id)
        
        # Prevent admin from deleting themselves
        if user.id == current_user.id:
            flash("You cannot delete your own admin account!", "danger")
            return redirect(url_for('admin_dashboard'))

        db.session.delete(user)
        db.session.commit()
        flash(f"User {user.full_name} has been deleted.", "success")
        return redirect(url_for('admin_dashboard'))

    # Route to update user details
    @app.route('/admin/update_user/<int:user_id>', methods=['POST'])
    @login_required
    def update_user(user_id):
        if current_user.role != 'admin':
            flash("Access denied.", "danger")
            return redirect(url_for('login'))
        
        user = User.query.get_or_404(user_id)
        user.full_name = request.form['full_name']
        user.email = request.form['email']
        user.phone = request.form.get('phone')
        user.role = request.form['role']
        
        # Optional: Update password only if provided
        new_password = request.form.get('password')
        if new_password:
            user.password_hash = generate_password_hash(new_password)
            
        db.session.commit()
        flash(f"User {user.full_name} updated successfully.", "success")
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/scholarships', methods=['GET', 'POST'])
    @login_required
    def manage_scholarships():
        if current_user.role != 'admin':
            flash("Unauthorized access.", "danger")
            return redirect(url_for('login'))

        if request.method == 'POST':
            title = request.form.get('title')
            description = request.form.get('description')
            amount = request.form.get('amount')
            deadline_str = request.form.get('deadline')
            
            # Convert string date to Python date object
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()

            new_scholarship = Scholarship(
                title=title,
                description=description,
                amount=amount,
                deadline=deadline,
                posted_by_id=current_user.id
            )
            db.session.add(new_scholarship)
            db.session.commit()
            flash("New scholarship posted successfully!", "success")

        scholarships = Scholarship.query.order_by(Scholarship.created_at.desc()).all()
        return render_template('manage_scholarships.html', scholarships=scholarships, today=date.today())
    
    @app.route('/admin/scholarship/delete/<int:id>', methods=['POST'])
    @login_required
    def delete_scholarship(id):
        if current_user.role != 'admin':
            flash("Unauthorized.", "danger")
            return redirect(url_for('login'))
        
        scholarship = Scholarship.query.get_or_404(id)
        db.session.delete(scholarship)
        db.session.commit()
        flash(f"Scholarship '{scholarship.title}' deleted.", "success")
        return redirect(url_for('manage_scholarships'))

    @app.route('/admin/scholarship/edit/<int:id>', methods=['POST'])
    @login_required
    def edit_scholarship(id):
        if current_user.role != 'admin':
            flash("Unauthorized.", "danger")
            return redirect(url_for('login'))
        
        scholarship = Scholarship.query.get_or_404(id)
        scholarship.title = request.form.get('title')
        scholarship.description = request.form.get('description')
        scholarship.amount = request.form.get('amount')
        
        deadline_str = request.form.get('deadline')
        scholarship.deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        
        # Toggle active status based on a checkbox
        scholarship.is_active = 'is_active' in request.form
        
        db.session.commit()
        flash("Scholarship updated successfully!", "success")
        return redirect(url_for('manage_scholarships'))
    
    @app.route('/field_officer/dashboard')
    @login_required
    def field_officer_dashboard():
        # Only allow field_officer role
        if current_user.role != 'field_officer':
            flash("Access denied. Field Officer privileges required.", "danger")
            return redirect(url_for('login'))

        # Fetch all applications (excluding drafts if you have a status field)
        applications = Application.query.order_by(Application.created_at.desc()).all()
        return render_template('field_officer_dashboard.html', applications=applications)

    # @app.route('/field_officer/interview/<int:application_id>', methods=['GET', 'POST'])
    # @login_required
    # def conduct_interview(application_id):
    #     if current_user.role != 'field_officer':
    #         flash("Access denied.", "danger")
    #         return redirect(url_for('login'))

    #     application = Application.query.get_or_404(application_id)

    #     if request.method == 'POST':
    #         # Collect form data
    #         score = request.form.get('interview_score')
    #         remarks = request.form.get('remarks')
    #         recommendation = request.form.get('recommendation')

    #         new_interview = Interview(
    #             application_id=application.id,
    #             interviewer_id=current_user.id,
    #             interview_score=float(score),
    #             remarks=remarks,
    #             recommendation=recommendation
    #         )
            
    #         db.session.add(new_interview)
    #         db.session.commit()

    #         flash(f"Interview for {application.applicant.full_name} submitted successfully.", "success")
    #         return redirect(url_for('field_officer_dashboard'))

    #     return render_template('interview_form.html', application=application)
    
    @app.route('/conduct-interview/<int:application_id>', methods=['GET', 'POST'])
    @login_required
    def conduct_interview(application_id):
        # 1. Security Check
        if current_user.role != 'field_officer':
            flash("Unauthorized access.", "danger")
            return redirect(url_for('index'))

        # 2. Get the specific application
        application = Application.query.get_or_404(application_id)

        # 3. Handle Form Submission (POST)
        if request.method == 'POST':
            h_pts = int(request.form.get('housing', 0))
            f_pts = int(request.form.get('family', 0))
            a_pts = int(request.form.get('academic', 0))
            
            total_score = h_pts + f_pts + a_pts

            # Create Interview record
            new_interview = Interview(
                application_id=application_id,
                interviewer_id=current_user.id,
                remarks=request.form.get('remarks'),
                recommendation='Recommend' if total_score >= 50 else 'Not recommend',
                interview_score=float(total_score)
            )
            db.session.add(new_interview)
            db.session.flush() 

            # Create the Detailed Assessment record
            details = Assessment(
                interview_id=new_interview.id,
                housing_score=h_pts,
                family_score=f_pts,
                academic_score=a_pts
            )
            
            # Move status forward
            application.status = 'interviewed'

            db.session.add(details)
            db.session.commit()
            
            flash(f"Assessment complete! Score: {total_score}%", "success")
            flash(f"Interview for {application.applicant.full_name} submitted successfully.", "success")
            return redirect(url_for('field_officer_dashboard'))

        # 4. Handle Page Load (GET)
        # This is what was missing! It renders the form when they first click the button.
        return render_template('conduct_interview.html', app=application)
    
    @app.route('/application/report/<int:app_id>')
    @login_required
    def generate_report(app_id):
        # Ensure only authorized roles (Reviewer, Auditor, Field Officer) can see this
        if current_user.role not in ['reviewer', 'auditor', 'field_officer', 'admin', 'applicant']:
            flash("Unauthorized", "danger")
            return redirect(url_for('login'))

        application = Application.query.get_or_404(app_id)
        
        # We pull the latest interview and its details
        interview = Interview.query.filter_by(application_id=app_id).order_by(Interview.id.desc()).first()
        
        if not interview:
            flash("No interview data found for this application.", "warning")
            return redirect(url_for('index'))

        return render_template('application_report.html', app=application, interview=interview)

    @app.route('/reviewer/dashboard')
    @login_required
    def reviewer_dashboard():
        if current_user.role != 'reviewer':
            flash("Unauthorized access.", "danger")
            return redirect(url_for('index'))

        # Fetch applications along with their linked interviews and scholarship info
        # We use a join to make sure we can see the interview score in the list
        applications = Application.query.order_by(Application.created_at.desc()).all()
        
        return render_template('reviewer_dashboard.html', applications=applications)

    @app.route('/reviewer/verify/<int:app_id>', methods=['POST'])
    @login_required
    def verify_application(app_id):
        if current_user.role != 'reviewer':
            return {"error": "Unauthorized"}, 403
        
        application = Application.query.get_or_404(app_id)
        application.status = 'verified'
        application.reviewer_id = current_user.id # Track who did the verification
        db.session.commit()
        
        flash(f"Application #{app_id} has been verified and moved to the final approval stage.", "success")
        return redirect(url_for('reviewer_dashboard'))
    
    @app.route('/reviewer/reject/<int:app_id>', methods=['POST'])
    @login_required
    def reject_application(app_id):
        if current_user.role != 'reviewer':
            flash("Unauthorized", "danger")
            return redirect(url_for('index'))
        
        application = Application.query.get_or_404(app_id)
        reason = request.form.get('rejection_reason')

        if not reason:
            flash("You must provide a reason for rejection.", "warning")
            return redirect(url_for('reviewer_dashboard'))

        # Update Application
        application.status = 'rejected'
        application.reviewer_id = current_user.id
        
        # We can store the reason in the Interview remarks or a new 'comments' field
        # For now, let's assume you might want to add a 'remarks' column to Application
        # Or simply create a 'rejection' interview entry
        rejection_note = Interview(
            application_id=app_id,
            interviewer_id=current_user.id,
            remarks=f"REJECTION REASON: {reason}",
            recommendation='not_recommend',
            interview_score=0
        )
        
        db.session.add(rejection_note)
        db.session.commit()
        
        flash(f"Application #{app_id} has been rejected.", "danger")
        return redirect(url_for('reviewer_dashboard'))
    
    @app.route('/applicant')
    @login_required
    def applicant_dashboard():
        # Get the applicant record for the current user
        applicant = Applicant.query.filter_by(user_id=current_user.id).first()
        
        if applicant:
            # Get all applications for this applicant
            applications = Application.query.filter_by(applicant_id=applicant.id).all()
            
            # Get all awards by querying awards through applications
            awards = Award.query.join(Application).filter(
                Application.applicant_id == applicant.id
            ).all()
        else:
            applications = []
            awards = []

        return render_template('applicant_dashboard.html',
                               applicant=applicant,
                               applications=applications,
                               awards=awards)
    
    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def applicant_profile():
        if request.method == 'POST':
            applicant = Applicant(
                user_id=current_user.id,
                full_name=request.form['full_name'],
                national_id=request.form['national_id'],
                dob=request.form.get('dob'),
                gender=request.form.get('gender'),
                sub_county=request.form.get('sub_county'),
                ward=request.form.get('ward'),
                school_name=request.form.get('school_name'),
                education_level=request.form.get('education_level'),
                guardian_name=request.form.get('guardian_name'),
                guardian_phone=request.form.get('guardian_phone'),
                annual_income=request.form.get('annual_income'),
                is_orphan=request.form.get('is_orphan') == 'on',
                has_disability=request.form.get('has_disability') == 'on'
            )
            db.session.add(applicant)
            db.session.commit()
            flash('Profile created!', 'success')
            return redirect(url_for('applicant_dashboard'))
        return render_template('applicant_profile.html')
    
    @app.route('/scholarships')
    @login_required
    def browse_scholarships():
        # Fetch scholarships that are active and haven't expired
        available = Scholarship.query.filter(
            Scholarship.is_active == True,
            Scholarship.deadline >= date.today()
        ).all()
        return render_template('browse_scholarships.html', scholarships=available)
    
    @app.route('/apply/<int:scholarship_id>', methods=['GET', 'POST'])
    @login_required
    def apply_scholarship(scholarship_id):
        # 1. Ensure only applicants can apply
        if current_user.role != 'applicant':
            flash("Only students can apply for scholarships.", "warning")
            return redirect(url_for('index'))

        # 2. Get the actual Applicant profile linked to this User
        # This assumes your Applicant model has a field like 'user_id'
        
        applicant_profile = Applicant.query.filter_by(user_id=current_user.id).first()

        if not applicant_profile:
            flash("You need to complete your student profile before applying.", "danger")
            # Redirect them to wherever they fill out their personal details (ID, Ward, etc.)
            return redirect(url_for('applicant_dashboard'))

        scholarship = Scholarship.query.get_or_404(scholarship_id)
        current_year = date.today().year

        # 3. Check for existing application using applicant_profile.id
        existing = Application.query.filter_by(
            applicant_id=applicant_profile.id, 
            scholarship_id=scholarship_id,
            application_year=current_year
        ).first()

        if existing:
            flash(f"You have already submitted an application for {current_year}.", "info")
            return redirect(url_for('applicant_dashboard'))

        if request.method == 'POST':
            try:
                new_app = Application(
                    applicant_id=applicant_profile.id, # Using the profile ID, not User ID
                    scholarship_id=scholarship_id,
                    application_year=current_year,
                    status='pending'
                )
                db.session.add(new_app)
                db.session.commit()
                flash("Application submitted successfully!", "success")
                return redirect(url_for('applicant_dashboard'))
            except Exception as e:
                db.session.rollback()
                print(f"Error saving application: {e}")
                flash("There was an error processing your application.", "danger")
                return redirect(url_for('applicant_dashboard'))

        return render_template('applications.html', scholarship=scholarship)
    
    @app.route('/my-applications')
    @login_required
    def my_applications():
        # 1. Ensure only applicants can access this
        if current_user.role != 'applicant':
            flash("This page is for student applicants only.", "warning")
            return redirect(url_for('index'))

        # 2. Find the Applicant profile linked to this User
        profile = Applicant.query.filter_by(user_id=current_user.id).first()

        if not profile:
            flash("No applicant profile found. Please complete your profile.", "info")
            return render_template('my_applications.html', applications=[])

        # 3. Get all applications for this specific applicant
        # We use the relationship backref if defined, or a direct query
        user_apps = Application.query.filter_by(applicant_id=profile.id).order_by(Application.created_at.desc()).all()

        return render_template('my_applications.html', applications=user_apps)
    
    @app.route('/application/<int:application_id>')
    @login_required
    def view_application(application_id):
        # Fetch the application or return 404
        app_record = Application.query.get_or_404(application_id)

        # Security check: 
        # Only staff OR the specific student who owns the application can view it
        is_staff = current_user.role in ['admin', 'reviewer', 'field_officer']
        
        # Get the applicant profile for the current user to compare IDs
        user_profile = Applicant.query.filter_by(user_id=current_user.id).first()
        is_owner = user_profile and (app_record.applicant_id == user_profile.id)

        if not is_staff and not is_owner:
            flash("Unauthorized access.", "danger")
            return redirect(url_for('index'))

        return render_template('view_application.html', app=app_record)
    
    @app.route('/auditor/dashboard')
    @login_required
    def auditor_dashboard():
        if current_user.role != 'auditor':
            flash("Unauthorized access. Auditor role required.", "danger")
            return redirect(url_for('index'))

        # Auditor only focuses on Verified applications ready for funding
        pending_approval = Application.query.filter_by(status='verified').all()
        
        # Optional: Calculate total committed funds if you have an 'amount' field
        # total_committed = sum(app.scholarship.amount for app in pending_approval)

        return render_template('auditor_dashboard.html', applications=pending_approval)

    @app.route('/auditor/approve/<int:app_id>', methods=['POST'])
    @login_required
    def final_approval(app_id):
        if current_user.role != 'auditor':
            return {"error": "Unauthorized"}, 403
        
        application = Application.query.get_or_404(app_id)
        application.status = 'approved'
        # Track which auditor signed off on this
        application.reviewer_id = current_user.id 
        
        db.session.commit()
        flash(f"Application #{app_id} has been officially APPROVED for funding.", "success")
        return redirect(url_for('auditor_dashboard'))
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out successfully!', 'success')
        return redirect(url_for('login'))

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)