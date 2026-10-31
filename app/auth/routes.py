from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, Role
from app.auth.utils import log_audit

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and request.method == 'GET':
        if current_user.role == Role.ADMINISTRATOR:
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == Role.FACULTY:
            return redirect(url_for('faculty.dashboard'))
        return redirect(url_for('student.dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')
        remember = True if request.form.get('remember') else False

        user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()

        if not user or not user.check_password(password):
            flash('Invalid username/email or password. Please try again.', 'danger')
            return render_template('auth/login.html', identifier=identifier)

        if not user.is_active:
            flash('Your account has been deactivated. Please contact college administration.', 'warning')
            return render_template('auth/login.html')

        login_user(user, remember=remember)
        log_audit(action="USER_LOGIN", target_type="User", target_id=user.id, details=f"User {user.username} logged in.")

        flash(f'Welcome back, {user.full_name}!', 'success')
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)

        if user.role == Role.ADMINISTRATOR:
            return redirect(url_for('admin.dashboard'))
        elif user.role == Role.FACULTY:
            return redirect(url_for('faculty.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('student.dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', Role.STUDENT).upper()
        department = request.form.get('department', 'Computer Science & Engineering')
        roll_number = request.form.get('roll_number', '').strip().upper()

        # Validation
        if not full_name or not username or not email or not password:
            flash('All required fields must be filled.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        # Limit public self-registration to STUDENT or FACULTY
        if role not in [Role.STUDENT, Role.FACULTY]:
            role = Role.STUDENT

        if User.query.filter_by(username=username).first():
            flash('Username is already taken. Please choose another.', 'warning')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Email address is already registered. Please log in.', 'warning')
            return render_template('auth/register.html')

        new_user = User(
            full_name=full_name,
            username=username,
            email=email,
            role=role,
            department=department,
            roll_number=roll_number,
            is_active=True
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        log_audit(action="USER_REGISTER", target_type="User", target_id=new_user.id, details=f"New {role} registered: {username}")
        flash('Registration successful! You can now log in with your credentials.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    log_audit(action="USER_LOGOUT", target_type="User", target_id=current_user.id, details=f"User {current_user.username} logged out.")
    logout_user()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('auth.login'))
