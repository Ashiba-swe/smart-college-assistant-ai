import pytest
from app.models import db, Message, Conversation, Feedback, FAQ, User, Role
from app.rag.engine import RAGEngine

def test_feedback_submission_and_faq_resolution(app, auth_client, admin_client):
    with app.app_context():
        user = User.query.filter_by(username='student_test').first()
        conv = Conversation(user_id=user.id, title="Test Thread")
        db.session.add(conv)
        db.session.commit()

        msg = Message(
            conversation_id=conv.id,
            sender='assistant',
            content='Old policy: Bus pass renewal is Rs 10,000.'
        )
        db.session.add(msg)
        db.session.commit()
        msg_id = msg.id

    # 1. Student reports incorrect answer
    res = auth_client.post('/api/feedback/submit', json={
        'message_id': msg_id,
        'rating': -1,
        'feedback_type': 'OUTDATED',
        'comments': 'The transport fee was revised to Rs 28,000 for this academic year.'
    })
    assert res.status_code == 200
    assert res.json['success'] is True

    # 2. Check Feedback recorded in DB
    with app.app_context():
        fb = Feedback.query.filter_by(message_id=msg_id).first()
        assert fb is not None
        assert fb.status == 'PENDING'
        fb_id = fb.id

    # 3. Admin converts feedback to verified FAQ
    resolve_res = admin_client.post(f'/admin/feedback/{fb_id}/convert-to-faq', data={
        'question': 'What is the revised annual bus pass fee?',
        'answer': 'The official annual RFID bus pass fee is Rs. 28,000 per academic year.',
        'category': 'Hostel & Transport'
    }, follow_redirects=True)
    assert resolve_res.status_code == 200

    # 4. Verify FAQ was created and status is RESOLVED
    with app.app_context():
        updated_fb = Feedback.query.get(fb_id)
        assert updated_fb.status == 'RESOLVED'

        faq = FAQ.query.filter_by(question='What is the revised annual bus pass fee?').first()
        assert faq is not None
        assert faq.is_verified is True
        assert '28,000' in faq.answer

        # Test query to check vector store retrieved this new verified knowledge
        engine = RAGEngine(chroma_dir=app.config['CHROMA_PERSIST_DIR'])
        rag_res = engine.query('annual bus pass fee')
        assert '28,000' in rag_res['answer'] or any('28,000' in s['snippet'] for s in rag_res['sources'])
