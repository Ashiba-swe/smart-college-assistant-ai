from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user
from app.models import db, AuditLog

def role_required(*roles):
    """
    Decorator to enforce role permissions on backend routes.
    Accepts multiple allowed roles, e.g. @role_required('ADMINISTRATOR') or @role_required('FACULTY', 'ADMINISTRATOR')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            if current_user.role not in roles:
                flash(f"Access denied. This page requires {', '.join(roles)} privileges.", "danger")
                if current_user.role == 'STUDENT':
                    return redirect(url_for('student.dashboard'))
                elif current_user.role == 'FACULTY':
                    return redirect(url_for('faculty.dashboard'))
                elif current_user.role == 'ADMINISTRATOR':
                    return redirect(url_for('admin.dashboard'))
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_audit(action: str, target_type: str = None, target_id: str = None, details: str = None):
    """Utility to record administrative and security actions."""
    try:
        user_id = current_user.id if current_user.is_authenticated else None
        ip = request.remote_addr if request else '127.0.0.1'
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id else None,
            details=details,
            ip_address=ip
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        print(f"Failed to record audit log: {e}")
