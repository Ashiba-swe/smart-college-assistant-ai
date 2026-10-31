import os
from flask import Flask, render_template
from flask_login import LoginManager
from app.config import config_by_name
from app.models import db, User

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this feature.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # Ensure upload and chroma directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['CHROMA_PERSIST_DIR'], exist_ok=True)
    os.makedirs(app.config['SAMPLE_DOCS_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register Blueprints
    from app.main import main_bp
    from app.auth import auth_bp
    from app.chat import chat_bp
    from app.student import student_bp
    from app.faculty import faculty_bp
    from app.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(faculty_bp)
    app.register_blueprint(admin_bp)

    # Error Handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Context processors for global template access
    @app.context_processor
    def inject_global_vars():
        return {
            'app_name': app.config.get('APP_NAME', 'Smart College Assistant AI'),
            'institution_name': app.config.get('INSTITUTION_NAME', 'Apex Institute of Technology'),
            'gemini_configured': bool(app.config.get('GEMINI_API_KEY'))
        }

    # Initialize tables
    with app.app_context():
        db.create_all()

    return app
