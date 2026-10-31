import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'apex-smart-college-secret-key-prod-2026'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload and File Management
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(basedir, 'data', 'uploads')
    SAMPLE_DOCS_FOLDER = os.path.join(basedir, 'data', 'sample_docs')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
    
    # ChromaDB Vector Store
    CHROMA_PERSIST_DIR = os.environ.get('CHROMA_PERSIST_DIR') or os.path.join(basedir, 'instance', 'chroma_db')
    
    # AI / LLM Configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY') or ''
    AI_PROVIDER = os.environ.get('AI_PROVIDER', 'gemini')
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')
    
    # Session Security
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Application Info
    APP_NAME = "Smart College Assistant AI"
    INSTITUTION_NAME = "Apex Institute of Technology"

class DevelopmentConfig(Config):
    DEBUG = True
    db_path = os.path.join(basedir, 'instance', 'college_assistant.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or f"sqlite:///{db_path}"

class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    test_db = os.path.join(basedir, 'instance', 'test_college.db')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{test_db}"
    CHROMA_PERSIST_DIR = os.path.join(basedir, 'instance', 'chroma_db_test')
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False
    # Render or cloud PostgreSQL URL handling (SQLAlchemy requires postgresql:// instead of postgres://)
    raw_db_url = os.environ.get('DATABASE_URL')
    if raw_db_url and raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = raw_db_url or f"sqlite:///{os.path.join(basedir, 'instance', 'college_assistant.db')}"
    SESSION_COOKIE_SECURE = True

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
