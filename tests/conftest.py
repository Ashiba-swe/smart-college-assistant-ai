import os
import shutil
import tempfile
import pytest
from app import create_app
from app.models import db, User, Role

@pytest.fixture(scope='session')
def temp_chroma_dir():
    temp_dir = tempfile.mkdtemp(prefix="test_chroma_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def app(temp_chroma_dir):
    os.environ['CHROMA_PERSIST_DIR'] = temp_chroma_dir
    os.environ['FLASK_ENV'] = 'testing'
    
    app = create_app('testing')
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['CHROMA_PERSIST_DIR'] = temp_chroma_dir
    
    with app.app_context():
        db.create_all()
        # Seed basic test users
        if not User.query.filter_by(username='admin_test').first():
            admin = User(
                username='admin_test',
                email='admin_test@apextech.edu',
                full_name='Test Admin',
                role=Role.ADMINISTRATOR,
                department='Admin',
                is_active=True
            )
            admin.set_password('AdminPass@123')
            db.session.add(admin)

        if not User.query.filter_by(username='faculty_test').first():
            faculty = User(
                username='faculty_test',
                email='faculty_test@apextech.edu',
                full_name='Test Faculty',
                role=Role.FACULTY,
                department='Information Technology',
                is_active=True
            )
            faculty.set_password('FacultyPass@123')
            db.session.add(faculty)

        if not User.query.filter_by(username='student_test').first():
            student = User(
                username='student_test',
                email='student_test@apextech.edu',
                full_name='Test Student',
                role=Role.STUDENT,
                department='Computer Science & Engineering',
                roll_number='22CS099',
                is_active=True
            )
            student.set_password('StudentPass@123')
            db.session.add(student)

        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(app):
    """Client logged in as a student."""
    c = app.test_client()
    c.get('/logout')
    c.post('/login', data={'identifier': 'student_test', 'password': 'StudentPass@123'})
    return c

@pytest.fixture
def admin_client(app):
    """Client logged in as an administrator."""
    c = app.test_client()
    c.get('/logout')
    c.post('/login', data={'identifier': 'admin_test', 'password': 'AdminPass@123'})
    return c

@pytest.fixture
def faculty_client(app):
    """Client logged in as a faculty member."""
    c = app.test_client()
    c.get('/logout')
    c.post('/login', data={'identifier': 'faculty_test', 'password': 'FacultyPass@123'})
    return c
