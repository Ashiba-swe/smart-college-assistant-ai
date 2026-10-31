import pytest
from app.models import User, Role

def test_user_password_hashing():
    u = User(username='hash_test', email='hash@test.com', full_name='Hash Test')
    u.set_password('MySecret@2026')
    assert u.password_hash != 'MySecret@2026'
    assert u.check_password('MySecret@2026') is True
    assert u.check_password('WrongPass') is False

def test_student_registration(client, app):
    res = client.post('/register', data={
        'full_name': 'New Student',
        'username': 'new_student',
        'email': 'new_student@apextech.edu',
        'password': 'Password@123',
        'confirm_password': 'Password@123',
        'role': 'STUDENT',
        'department': 'Information Technology',
        'roll_number': '23IT101'
    }, follow_redirects=True)
    assert res.status_code == 200
    with app.app_context():
        user = User.query.filter_by(username='new_student').first()
        assert user is not None
        assert user.role == Role.STUDENT
        assert user.check_password('Password@123') is True

def test_registration_duplicate_username(client):
    res = client.post('/register', data={
        'full_name': 'Duplicate User',
        'username': 'student_test', # Already exists
        'email': 'different_email@apextech.edu',
        'password': 'Password@123',
        'confirm_password': 'Password@123',
        'role': 'STUDENT'
    }, follow_redirects=True)
    assert b"Username is already taken" in res.data

def test_login_success_and_logout(client):
    # Login
    res = client.post('/login', data={
        'identifier': 'student_test',
        'password': 'StudentPass@123'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Student Portal" in res.data or b"Welcome back" in res.data

    # Logout
    logout_res = client.get('/logout', follow_redirects=True)
    assert b"logged out" in logout_res.data

def test_login_invalid_password(client):
    res = client.post('/login', data={
        'identifier': 'student_test',
        'password': 'WrongPassword999'
    }, follow_redirects=True)
    assert b"Invalid username/email or password" in res.data
