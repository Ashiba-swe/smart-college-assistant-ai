from datetime import datetime
import json
import uuid
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Role:
    STUDENT = 'STUDENT'
    FACULTY = 'FACULTY'
    ADMINISTRATOR = 'ADMINISTRATOR'
    ALL = [STUDENT, FACULTY, ADMINISTRATOR]

class DocumentStatus:
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    ARCHIVED = 'ARCHIVED'

class FeedbackType:
    HELPFUL = 'HELPFUL'
    INCORRECT = 'INCORRECT'
    MISSING_INFO = 'MISSING_INFO'
    OUTDATED = 'OUTDATED'
    UNHELPFUL = 'UNHELPFUL'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(30), nullable=False, default=Role.STUDENT)
    department = db.Column(db.String(100), nullable=True, default='General')
    roll_number = db.Column(db.String(50), nullable=True) # or Employee ID
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    conversations = db.relationship('Conversation', backref='user', lazy=True, cascade='all, delete-orphan')
    feedbacks = db.relationship('Feedback', foreign_keys='Feedback.user_id', backref='user', lazy=True)
    uploaded_documents = db.relationship('Document', foreign_keys='Document.uploaded_by_id', backref='uploader', lazy=True)
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_admin(self):
        return self.role == Role.ADMINISTRATOR
        
    @property
    def is_faculty(self):
        return self.role in [Role.FACULTY, Role.ADMINISTRATOR]

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'department': self.department,
            'roll_number': self.roll_number,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }

class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False, default='New Consultation')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan', order_by='Message.created_at')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'created_at': self.created_at.strftime('%b %d, %Y %I:%M %p') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%b %d, %Y %I:%M %p') if self.updated_at else None,
            'message_count': len(self.messages)
        }

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.String(36), db.ForeignKey('conversations.id'), nullable=False, index=True)
    sender = db.Column(db.String(20), nullable=False) # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    sources_json = db.Column(db.Text, nullable=True) # Serialized list of citations
    tokens_used = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    feedbacks = db.relationship('Feedback', backref='message', lazy=True, cascade='all, delete-orphan')

    @property
    def sources(self):
        if self.sources_json:
            try:
                return json.loads(self.sources_json)
            except Exception:
                return []
        return []

    def set_sources(self, sources_list):
        self.sources_json = json.dumps(sources_list)

    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender': self.sender,
            'content': self.content,
            'sources': self.sources,
            'created_at': self.created_at.strftime('%I:%M %p') if self.created_at else None
        }

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(10), nullable=False) # 'pdf', 'docx', 'txt'
    file_size = db.Column(db.Integer, default=0) # bytes
    category = db.Column(db.String(100), default='General Regulations')
    department = db.Column(db.String(100), default='All Departments')
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(30), default=DocumentStatus.PENDING)
    version = db.Column(db.Integer, default=1)
    checksum = db.Column(db.String(64), nullable=True, index=True)
    chunk_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    versions = db.relationship('DocumentVersion', backref='document', lazy=True, cascade='all, delete-orphan')
    approvals = db.relationship('DocumentApproval', backref='document', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'filename': self.filename,
            'file_type': self.file_type.upper(),
            'file_size_kb': round(self.file_size / 1024, 1) if self.file_size else 0,
            'category': self.category,
            'department': self.department,
            'uploader': self.uploader.full_name if self.uploader else 'System Demo',
            'status': self.status,
            'version': self.version,
            'chunk_count': self.chunk_count,
            'created_at': self.created_at.strftime('%b %d, %Y') if self.created_at else None
        }

class DocumentVersion(db.Model):
    __tablename__ = 'document_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    checksum = db.Column(db.String(64), nullable=True)
    change_summary = db.Column(db.String(300), default='Document upload/update')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DocumentApproval(db.Model):
    __tablename__ = 'document_approvals'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(30), nullable=False) # 'APPROVED', 'REJECTED'
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    reviewer = db.relationship('User', foreign_keys=[reviewer_id])

class FAQ(db.Model):
    __tablename__ = 'faqs'
    
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(300), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), default='General')
    department = db.Column(db.String(100), default='All Departments')
    is_verified = db.Column(db.Boolean, default=True)
    source_doc_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    source_document = db.relationship('Document', foreign_keys=[source_doc_id])
    author = db.relationship('User', foreign_keys=[created_by_id])

    def to_dict(self):
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'category': self.category,
            'department': self.department,
            'is_verified': self.is_verified,
            'source_doc_title': self.source_document.title if self.source_document else 'Direct Knowledge Base',
            'view_count': self.view_count,
            'created_at': self.created_at.strftime('%b %d, %Y') if self.created_at else None
        }

class Feedback(db.Model):
    __tablename__ = 'feedbacks'
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False) # 1 (Helpful) or -1 (Unhelpful/Reported)
    feedback_type = db.Column(db.String(30), default=FeedbackType.HELPFUL)
    comments = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default='PENDING') # PENDING, REVIEWED, RESOLVED
    resolution_notes = db.Column(db.Text, nullable=True)
    resolved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    resolver = db.relationship('User', foreign_keys=[resolved_by_id])

    def to_dict(self):
        return {
            'id': self.id,
            'message_id': self.message_id,
            'user_name': self.user.full_name if self.user else 'Anonymous',
            'rating': self.rating,
            'feedback_type': self.feedback_type,
            'comments': self.comments or '',
            'status': self.status,
            'question_snippet': self.message.conversation.title if (self.message and self.message.conversation) else 'General Inquiry',
            'answer_snippet': (self.message.content[:150] + '...') if (self.message and self.message.content) else '',
            'created_at': self.created_at.strftime('%b %d, %Y %I:%M %p') if self.created_at else None
        }

class ReportedAnswer(db.Model):
    __tablename__ = 'reported_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default='OPEN') # OPEN, RESOLVED, REJECTED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    message_ref = db.relationship('Message', foreign_keys=[message_id])
    reporter = db.relationship('User', foreign_keys=[user_id])

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(50), nullable=True)
    target_id = db.Column(db.String(50), nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_name': self.user.full_name if self.user else 'System',
            'action': self.action,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.strftime('%b %d, %Y %I:%M:%S %p') if self.created_at else None
        }

class EvaluationResult(db.Model):
    __tablename__ = 'evaluation_results'
    
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(100), nullable=False) # e.g. 'Groundedness', 'Context Relevance', 'Answer Accuracy'
    score = db.Column(db.Float, nullable=False) # 0.0 to 100.0 %
    sample_size = db.Column(db.Integer, default=0)
    details_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'metric_name': self.metric_name,
            'score': round(self.score, 1),
            'sample_size': self.sample_size,
            'created_at': self.created_at.strftime('%b %d, %Y') if self.created_at else None
        }
