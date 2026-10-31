import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from app.models import (
    db, User, Role, Document, DocumentStatus, DocumentVersion,
    DocumentApproval, FAQ, Feedback, ReportedAnswer, AuditLog, EvaluationResult
)
from app.auth.utils import role_required, log_audit
from app.rag.engine import RAGEngine, compute_checksum

admin_bp = Blueprint('admin', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def get_rag_engine():
    return RAGEngine(
        chroma_dir=current_app.config['CHROMA_PERSIST_DIR'],
        gemini_api_key=current_app.config.get('GEMINI_API_KEY', ''),
        model_name=current_app.config.get('GEMINI_MODEL', 'gemini-2.5-flash')
    )

# ----------------- ADMIN DASHBOARD -----------------
@admin_bp.route('/admin/dashboard')
@login_required
@role_required(Role.ADMINISTRATOR)
def dashboard():
    stats = {
        'total_users': User.query.count(),
        'total_students': User.query.filter_by(role=Role.STUDENT).count(),
        'total_faculty': User.query.filter_by(role=Role.FACULTY).count(),
        'total_docs': Document.query.count(),
        'approved_docs': Document.query.filter_by(status=DocumentStatus.APPROVED).count(),
        'pending_docs': Document.query.filter_by(status=DocumentStatus.PENDING).count(),
        'total_faqs': FAQ.query.count(),
        'pending_feedbacks': Feedback.query.filter_by(status='PENDING').count(),
        'reported_answers': ReportedAnswer.query.filter_by(status='OPEN').count()
    }
    
    # Vector store diagnostic count
    try:
        engine = get_rag_engine()
        stats['vector_chunks'] = engine.vector_store.count()
    except Exception:
        stats['vector_chunks'] = 0

    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(8).all()
    pending_approvals = Document.query.filter_by(status=DocumentStatus.PENDING).order_by(Document.created_at.desc()).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        stats=stats,
        recent_logs=recent_logs,
        pending_approvals=pending_approvals
    )

# ----------------- USER MANAGEMENT -----------------
@admin_bp.route('/admin/users')
@login_required
@role_required(Role.ADMINISTRATOR)
def users():
    role_filter = request.args.get('role')
    search_q = request.args.get('q', '').strip()

    query = User.query
    if role_filter and role_filter in Role.ALL:
        query = query.filter_by(role=role_filter)
    if search_q:
        query = query.filter(
            (User.full_name.ilike(f'%{search_q}%')) |
            (User.username.ilike(f'%{search_q}%')) |
            (User.email.ilike(f'%{search_q}%'))
        )

    all_users = query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users, roles=Role.ALL, current_role=role_filter)

@admin_bp.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@role_required(Role.ADMINISTRATOR)
def toggle_user_status(user_id):
    if user_id == current_user.id:
        flash("You cannot modify your own administrative status.", "danger")
        return redirect(url_for('admin.users'))

    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()

    status_str = "activated" if user.is_active else "deactivated"
    log_audit(action="USER_STATUS_CHANGE", target_type="User", target_id=user.id, details=f"User {user.username} was {status_str}.")
    flash(f"User {user.username} has been {status_str}.", "success")
    return redirect(url_for('admin.users'))

@admin_bp.route('/admin/users/<int:user_id>/change-role', methods=['POST'])
@login_required
@role_required(Role.ADMINISTRATOR)
def change_user_role(user_id):
    if user_id == current_user.id:
        flash("You cannot modify your own administrative role.", "danger")
        return redirect(url_for('admin.users'))

    new_role = request.form.get('role')
    if new_role not in Role.ALL:
        flash("Invalid role specified.", "danger")
        return redirect(url_for('admin.users'))

    user = User.query.get_or_404(user_id)
    old_role = user.role
    user.role = new_role
    db.session.commit()

    log_audit(action="USER_ROLE_CHANGE", target_type="User", target_id=user.id, details=f"User {user.username} role changed from {old_role} to {new_role}.")
    flash(f"User {user.username}'s role changed to {new_role}.", "success")
    return redirect(url_for('admin.users'))

# ----------------- DOCUMENT MANAGEMENT & APPROVALS -----------------
@admin_bp.route('/admin/documents')
@login_required
@role_required(Role.ADMINISTRATOR)
def documents():
    status_filter = request.args.get('status')
    query = Document.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    all_docs = query.order_by(Document.created_at.desc()).all()
    return render_template('admin/documents.html', documents=all_docs, current_status=status_filter)

@admin_bp.route('/admin/documents/upload', methods=['GET', 'POST'])
@login_required
@role_required(Role.ADMINISTRATOR)
def upload_document():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', 'General Regulations')
        department = request.form.get('department', 'All Departments')
        file = request.files.get('file')

        if not title or not file or file.filename == '':
            flash('Please provide a title and select a valid file.', 'danger')
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash('Allowed file extensions: .pdf, .docx, .txt', 'danger')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)

        dest_filename = f"admin_{int(os.path.getmtime(upload_folder) if os.path.exists(upload_folder) else 0)}_{filename}"
        dest_path = os.path.join(upload_folder, dest_filename)
        file.save(dest_path)

        file_size = os.path.getsize(dest_path)
        file_type = filename.rsplit('.', 1)[1].lower()
        checksum = compute_checksum(dest_path)

        # Create approved document record
        doc = Document(
            title=title,
            filename=dest_filename,
            file_path=dest_path,
            file_type=file_type,
            file_size=file_size,
            category=category,
            department=department,
            uploaded_by_id=current_user.id,
            status=DocumentStatus.APPROVED,
            version=1,
            checksum=checksum,
            chunk_count=0
        )
        db.session.add(doc)
        db.session.commit()

        # Ingest & index into ChromaDB immediately
        engine = get_rag_engine()
        chunks_indexed = engine.process_and_index_document(doc.to_dict() | {'file_path': dest_path})
        doc.chunk_count = chunks_indexed
        db.session.commit()

        log_audit(action="DOCUMENT_UPLOAD_ADMIN", target_type="Document", target_id=doc.id, details=f"Admin uploaded & indexed '{title}' ({chunks_indexed} chunks).")
        flash(f"Document '{title}' uploaded and indexed successfully ({chunks_indexed} chunks added to vector store).", 'success')
        return redirect(url_for('admin.documents'))

    return render_template('admin/document_upload.html')

@admin_bp.route('/admin/documents/<int:doc_id>/approve', methods=['POST'])
@login_required
@role_required(Role.ADMINISTRATOR)
def approve_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    comments = request.form.get('comments', 'Approved by administrator.')

    # Index document into ChromaDB
    engine = get_rag_engine()
    chunks_indexed = engine.process_and_index_document(doc.to_dict() | {'file_path': doc.file_path})

    doc.status = DocumentStatus.APPROVED
    doc.chunk_count = chunks_indexed

    approval = DocumentApproval(
        document_id=doc.id,
        reviewer_id=current_user.id,
        action='APPROVED',
        comments=comments
    )
    db.session.add(approval)
    db.session.commit()

    log_audit(action="DOCUMENT_APPROVED", target_type="Document", target_id=doc.id, details=f"Approved '{doc.title}', indexed {chunks_indexed} chunks.")
    flash(f"Document '{doc.title}' has been approved and successfully indexed ({chunks_indexed} chunks).", "success")
    return redirect(url_for('admin.documents'))

@admin_bp.route('/admin/documents/<int:doc_id>/reject', methods=['POST'])
@login_required
@role_required(Role.ADMINISTRATOR)
def reject_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    comments = request.form.get('comments', 'Rejected by administrator.')

    doc.status = DocumentStatus.REJECTED
    approval = DocumentApproval(
        document_id=doc.id,
        reviewer_id=current_user.id,
        action='REJECTED',
        comments=comments
    )
    db.session.add(approval)
    db.session.commit()

    log_audit(action="DOCUMENT_REJECTED", target_type="Document", target_id=doc.id, details=f"Rejected '{doc.title}': {comments}")
    flash(f"Document '{doc.title}' has been marked as rejected.", "warning")
    return redirect(url_for('admin.documents'))

@admin_bp.route('/admin/documents/<int:doc_id>/archive', methods=['POST'])
@login_required
@role_required(Role.ADMINISTRATOR)
def archive_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    
    # De-index from vector store to remove obsolete chunks
    engine = get_rag_engine()
    engine.deindex_document(doc.id)

    doc.status = DocumentStatus.ARCHIVED
    doc.chunk_count = 0
    db.session.commit()

    log_audit(action="DOCUMENT_ARCHIVED", target_type="Document", target_id=doc.id, details=f"Archived '{doc.title}' and removed its vector chunks.")
    flash(f"Document '{doc.title}' archived. All associated vector embeddings were safely removed from knowledge base.", "info")
    return redirect(url_for('admin.documents'))

# ----------------- KNOWLEDGE BASE & VECTOR DASHBOARD -----------------
@admin_bp.route('/admin/knowledge-base')
@login_required
@role_required(Role.ADMINISTRATOR)
def knowledge_base():
    engine = get_rag_engine()
    kb_stats = engine.get_stats()
    approved_docs = Document.query.filter_by(status=DocumentStatus.APPROVED).all()
    verified_faqs = FAQ.query.filter_by(is_verified=True).all()
    
    return render_template(
        'admin/knowledge_base.html',
        kb_stats=kb_stats,
        approved_docs=approved_docs,
        verified_faqs=verified_faqs
    )

@admin_bp.route('/admin/knowledge-base/test-search', methods=['POST'])
@login_required
@role_required(Role.ADMINISTRATOR)
def test_search():
    query_text = request.form.get('query', '').strip()
    if not query_text:
        return jsonify({'error': 'Query string is required.'}), 400

    engine = get_rag_engine()
    retrieved = engine.vector_store.search(query_text, k=4)
    return jsonify({
        'query': query_text,
        'results_count': len(retrieved),
        'results': retrieved
    })

@admin_bp.route('/admin/knowledge-base/reindex-all', methods=['POST'])
@login_required
@role_required(Role.ADMINISTRATOR)
def reindex_all():
    engine = get_rag_engine()
    # 1. Clear vector store
    engine.vector_store.clear()

    total_chunks = 0
    approved_docs = Document.query.filter_by(status=DocumentStatus.APPROVED).all()
    for doc in approved_docs:
        if os.path.exists(doc.file_path):
            count = engine.process_and_index_document(doc.to_dict() | {'file_path': doc.file_path})
            doc.chunk_count = count
            total_chunks += count

    # 2. Re-index verified FAQs
    verified_faqs = FAQ.query.filter_by(is_verified=True).all()
    for faq in verified_faqs:
        engine.index_faq(faq.to_dict())
        total_chunks += 1

    db.session.commit()
    log_audit(action="KNOWLEDGE_BASE_REINDEXED", details=f"Full re-indexing completed: {len(approved_docs)} documents, {len(verified_faqs)} FAQs, {total_chunks} total chunks.")
    flash(f"Knowledge Base successfully rebuilt! Total {total_chunks} chunks indexed.", "success")
    return redirect(url_for('admin.knowledge_base'))

# ----------------- FAQ MANAGEMENT -----------------
@admin_bp.route('/admin/faqs', methods=['GET', 'POST'])
@login_required
@role_required(Role.ADMINISTRATOR)
def faqs():
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        answer = request.form.get('answer', '').strip()
        category = request.form.get('category', 'General')
        department = request.form.get('department', 'All Departments')

        if not question or not answer:
            flash("Question and Answer are required.", "danger")
            return redirect(url_for('admin.faqs'))

        new_faq = FAQ(
            question=question,
            answer=answer,
            category=category,
            department=department,
            is_verified=True,
            created_by_id=current_user.id
        )
        db.session.add(new_faq)
        db.session.commit()

        # Index directly into ChromaDB
        engine = get_rag_engine()
        engine.index_faq(new_faq.to_dict())

        log_audit(action="FAQ_CREATED", target_type="FAQ", target_id=new_faq.id, details=f"Created verified FAQ: '{question[:30]}...'")
        flash("FAQ created and immediately added to active vector knowledge base!", "success")
        return redirect(url_for('admin.faqs'))

    all_faqs = FAQ.query.order_by(FAQ.created_at.desc()).all()
    return render_template('admin/faqs.html', faqs=all_faqs)

@admin_bp.route('/admin/faqs/<int:faq_id>/verify', methods=['POST'])
@login_required
@role_required(Role.ADMINISTRATOR)
def verify_faq(faq_id):
    faq = FAQ.query.get_or_404(faq_id)
    faq.is_verified = True
    db.session.commit()

    # Index into vector store
    engine = get_rag_engine()
    engine.index_faq(faq.to_dict())

    log_audit(action="FAQ_VERIFIED", target_type="FAQ", target_id=faq.id, details=f"Approved & indexed faculty FAQ: '{faq.question[:30]}...'")
    flash("Faculty FAQ verified and indexed into the AI knowledge base.", "success")
    return redirect(url_for('admin.faqs'))

@admin_bp.route('/admin/faqs/<int:faq_id>/delete', methods=['POST'])
@login_required
@role_required(Role.ADMINISTRATOR)
def delete_faq(faq_id):
    faq = FAQ.query.get_or_404(faq_id)
    db.session.delete(faq)
    db.session.commit()

    log_audit(action="FAQ_DELETED", target_type="FAQ", target_id=faq_id, details="Deleted FAQ.")
    flash("FAQ removed.", "info")
    return redirect(url_for('admin.faqs'))

# ----------------- FEEDBACK & ADAPTIVE LEARNING -----------------
@admin_bp.route('/admin/feedback')
@login_required
@role_required(Role.ADMINISTRATOR)
def feedback():
    all_feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()
    reported_list = ReportedAnswer.query.order_by(ReportedAnswer.created_at.desc()).all()
    return render_template('admin/feedback.html', feedbacks=all_feedbacks, reported_answers=reported_list)

@admin_bp.route('/admin/feedback/<int:feedback_id>/convert-to-faq', methods=['POST'])
@login_required
@role_required(Role.ADMINISTRATOR)
def convert_feedback_to_faq(feedback_id):
    """
    Adaptive Knowledge Loop:
    Converts student report/correction into a verified FAQ and immediately indexes it into vector database.
    """
    fb = Feedback.query.get_or_404(feedback_id)
    verified_question = request.form.get('question', '').strip()
    verified_answer = request.form.get('answer', '').strip()
    category = request.form.get('category', 'Administrative Procedures')

    if not verified_question or not verified_answer:
        flash("Both verified question and authoritative answer are required.", "danger")
        return redirect(url_for('admin.feedback'))

    # 1. Create verified FAQ
    new_faq = FAQ(
        question=verified_question,
        answer=verified_answer,
        category=category,
        is_verified=True,
        created_by_id=current_user.id
    )
    db.session.add(new_faq)

    # 2. Update feedback status
    fb.status = 'RESOLVED'
    fb.resolved_by_id = current_user.id
    fb.resolution_notes = f"Converted to verified FAQ #{new_faq.id}"

    db.session.commit()

    # 3. Index immediately into ChromaDB
    engine = get_rag_engine()
    engine.index_faq(new_faq.to_dict())

    log_audit(
        action="FEEDBACK_CONVERTED_TO_FAQ",
        target_type="Feedback",
        target_id=fb.id,
        details=f"Student feedback converted to verified FAQ #{new_faq.id}: '{verified_question[:40]}...'"
    )

    flash("Feedback resolved! A verified FAQ has been created and indexed into the vector database. Future AI responses will use this verified knowledge.", "success")
    return redirect(url_for('admin.feedback'))

# ----------------- AI EVALUATION DASHBOARD -----------------
@admin_bp.route('/admin/evaluations')
@login_required
@role_required(Role.ADMINISTRATOR)
def evaluations():
    recent_evals = EvaluationResult.query.order_by(EvaluationResult.created_at.desc()).all()
    return render_template('admin/evaluations.html', evals=recent_evals)

# ----------------- AUDIT LOGS -----------------
@admin_bp.route('/admin/audit-logs')
@login_required
@role_required(Role.ADMINISTRATOR)
def audit_logs():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(100).all()
    return render_template('admin/audit_logs.html', logs=logs)
