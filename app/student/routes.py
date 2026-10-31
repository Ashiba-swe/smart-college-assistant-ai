from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import db, Conversation, Document, FAQ, Feedback, DocumentStatus, Role
from app.auth.utils import role_required, log_audit

student_bp = Blueprint('student', __name__)

@student_bp.route('/student/dashboard')
@login_required
def dashboard():
    # User's recent conversations
    recent_convs = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.updated_at.desc()).limit(5).all()
    total_convs = Conversation.query.filter_by(user_id=current_user.id).count()
    
    # Campus stats
    total_approved_docs = Document.query.filter_by(status=DocumentStatus.APPROVED).count()
    total_faqs = FAQ.query.filter_by(is_verified=True).count()
    
    # User feedback submissions
    feedback_count = Feedback.query.filter_by(user_id=current_user.id).count()

    # Recommended topics
    categories = ['Academic Regulations', 'Examinations', 'Library Services', 'Scholarships', 'Hostel & Transport']

    return render_template(
        'student/dashboard.html',
        recent_convs=recent_convs,
        total_convs=total_convs,
        total_approved_docs=total_approved_docs,
        total_faqs=total_faqs,
        feedback_count=feedback_count,
        categories=categories
    )

@student_bp.route('/student/history')
@login_required
def history():
    conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.updated_at.desc()).all()
    return render_template('student/history.html', conversations=conversations)

@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        department = request.form.get('department', '').strip()
        roll_number = request.form.get('roll_number', '').strip()
        new_password = request.form.get('new_password', '')

        if full_name:
            current_user.full_name = full_name
        if department:
            current_user.department = department
        if roll_number:
            current_user.roll_number = roll_number
        if new_password and len(new_password) >= 6:
            current_user.set_password(new_password)
            flash('Password updated successfully.', 'success')

        db.session.commit()
        log_audit(action="PROFILE_UPDATE", target_type="User", target_id=current_user.id, details="User updated profile details.")
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student.profile'))

    return render_template('user/profile.html')

@student_bp.route('/settings')
@login_required
def settings():
    return render_template('user/settings.html')
