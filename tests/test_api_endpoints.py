import pytest

def test_health_check_endpoint(client):
    res = client.get('/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'healthy'
    assert data['database'] == 'connected'
    assert data['vector_store'] == 'operational'

def test_public_pages_render(client):
    res_home = client.get('/')
    assert res_home.status_code == 200
    assert b"Your Smart Campus." in res_home.data

    res_sources = client.get('/sources')
    assert res_sources.status_code == 200
    assert b"Official Document Library" in res_sources.data

    res_faqs = client.get('/faqs')
    assert res_faqs.status_code == 200
    assert b"Frequently Asked Questions" in res_faqs.data

def test_chat_send_api(auth_client):
    res = auth_client.post('/api/chat/send', json={
        'message': 'When does the library open?'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert 'conversation_id' in data
    assert 'assistant_message' in data
    assert 'content' in data['assistant_message']

    conv_id = data['conversation_id']

    # List conversations
    res_list = auth_client.get('/api/chat/conversations')
    assert res_list.status_code == 200
    convs = res_list.get_json()
    assert any(c['id'] == conv_id for c in convs)

    # Delete conversation
    res_del = auth_client.delete(f'/api/chat/conversations/{conv_id}')
    assert res_del.status_code == 200
    assert res_del.get_json()['success'] is True
