import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.models import db, Document, FAQ, DocumentStatus, Role
from app.auth.utils import role_required, log_audit
from app.rag.engine import compute_checksum

faculty_bp = Blueprint('faculty', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@faculty_bp.route('/faculty/dashboard')
@login_required
@role_required(Role.FACULTY, Role.ADMINISTRATOR)
def dashboard():
    my_docs = Document.query.filter_by(uploaded_by_id=current_user.id).order_by(Document.created_at.desc()).all()
    my_faqs = FAQ.query.filter_by(created_by_id=current_user.id).order_by(FAQ.created_at.desc()).all()
    
    pending_docs = sum(1 for d in my_docs if d.status == DocumentStatus.PENDING)
    approved_docs = sum(1 for d in my_docs if d.status == DocumentStatus.APPROVED)
    
    return render_template(
        'faculty/dashboard.html',
        my_docs=my_docs,
        my_faqs=my_faqs,
        pending_docs=pending_docs,
        approved_docs=approved_docs
    )

@faculty_bp.route('/faculty/documents/upload', methods=['GET', 'POST'])
@login_required
@role_required(Role.FACULTY, Role.ADMINISTRATOR)
def upload_document():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', 'Departmental Notices')
        department = request.form.get('department') or current_user.department or 'All Departments'
        file = request.files.get('file')

        if not title or not file or file.filename == '':
            flash('Please specify a title and select a valid document file.', 'danger')
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash('Invalid file format. Allowed formats: .pdf, .docx, .txt', 'danger')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)

        # Unique filename prefix if needed
        dest_filename = f"{current_user.id}_{int(os.path.getmtime(upload_folder) if os.path.exists(upload_folder) else 0)}_{filename}"
        dest_path = os.path.join(upload_folder, dest_filename)
        file.save(dest_path)

        # File properties
        file_size = os.path.getsize(dest_path)
        file_type = filename.rsplit('.', 1)[1].lower()
        checksum = compute_checksum(dest_path)

        # Create Document record with PENDING status
        new_doc = Document(
            title=title,
            filename=dest_filename,
            file_path=dest_path,
            file_type=file_type,
            file_size=file_size,
            category=category,
            department=department,
            uploaded_by_id=current_user.id,
            status=DocumentStatus.PENDING,
            version=1,
            checksum=checksum,
            chunk_count=0
        )
        db.session.add(new_doc)
        db.session.commit()

        log_audit(
            action="DOCUMENT_SUBMITTED",
            target_type="Document",
            target_id=new_doc.id,
            details=f"Faculty {current_user.full_name} submitted document '{title}' for approval."
        )

        flash('Document submitted successfully! It is now in the review queue for Administrator approval.', 'success')
        return redirect(url_for('faculty.dashboard'))

    categories = [
        'Academic Regulations',
        'Examination & Assessment',
        'Departmental Notices',
        'Laboratories & Safety',
        'Internship & Placements',
        'Student Welfare & Scholarships'
    ]
    return render_template('faculty/submit_doc.html', categories=categories)

@faculty_bp.route('/faculty/faqs/submit', methods=['GET', 'POST'])
@login_required
@role_required(Role.FACULTY, Role.ADMINISTRATOR)
def submit_faq():
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        answer = request.form.get('answer', '').strip()
        category = request.form.get('category', 'Departmental')
        department = request.form.get('department') or current_user.department or 'All Departments'

        if not question or not answer:
            flash('Both question and answer are required.', 'danger')
            return redirect(request.url)

        new_faq = FAQ(
            question=question,
            answer=answer,
            category=category,
            department=department,
            is_verified=False, # Requires admin approval
            created_by_id=current_user.id
        )
        db.session.add(new_faq)
        db.session.commit()

        log_audit(
            action="FAQ_SUBMITTED",
            target_type="FAQ",
            target_id=new_faq.id,
            details=f"Faculty {current_user.full_name} submitted FAQ: '{question[:40]}...'"
        )

        flash('FAQ submitted successfully. It will become active once verified by an administrator.', 'success')
        return redirect(url_for('faculty.dashboard'))

    return render_template('faculty/submit_faq.html')
