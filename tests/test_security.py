import io
import pytest

def test_unauthenticated_protected_route_redirect(client):
    res = client.get('/chat')
    assert res.status_code == 302
    assert '/login' in res.location

    res_admin = client.get('/admin/dashboard')
    assert res_admin.status_code == 302
    assert '/login' in res_admin.location

def test_student_cannot_access_admin_dashboard(auth_client):
    res = auth_client.get('/admin/dashboard', follow_redirects=True)
    # Role decorator redirects student with flash message
    assert b"Access denied" in res.data
    assert b"Student Portal" in res.data or b"Dashboard" in res.data

def test_faculty_cannot_access_admin_user_management(faculty_client):
    res = faculty_client.get('/admin/users', follow_redirects=True)
    assert b"Access denied" in res.data

def test_admin_can_access_admin_pages(admin_client):
    res = admin_client.get('/admin/dashboard')
    assert res.status_code == 200
    assert b"Administrator Master Console" in res.data

    res_users = admin_client.get('/admin/users')
    assert res_users.status_code == 200
    assert b"User Directory" in res_users.data

def test_upload_file_extension_validation(admin_client):
    # Attempt uploading malicious script file
    data = {
        'title': 'Dangerous File',
        'file': (io.BytesIO(b'print("malicious script")'), 'exploit.py')
    }
    res = admin_client.post('/admin/documents/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert b"Allowed file extensions: .pdf, .docx, .txt" in res.data
