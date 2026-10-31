from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models import db, Conversation, Message, Feedback, ReportedAnswer, FeedbackType
from app.rag.engine import RAGEngine
import uuid

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat')
@chat_bp.route('/chat/<conversation_id>')
@login_required
def chat_view(conversation_id=None):
    # Fetch all user conversations for sidebar
    user_conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.updated_at.desc()).all()
    
    current_conv = None
    messages = []
    
    if conversation_id:
        current_conv = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first()
        if current_conv:
            messages = current_conv.messages

    suggested_questions = [
        "When is the examination?",
        "What are the attendance rules?",
        "How do I apply for a bonafide?",
        "What are the library timings?",
        "Tell me about internship procedures."
    ]

    return render_template(
        'chat/index.html',
        conversations=user_conversations,
        current_conv=current_conv,
        messages=messages,
        suggested_questions=suggested_questions
    )

@chat_bp.route('/api/chat/send', methods=['POST'])
@login_required
def send_message():
    data = request.get_json() or {}
    user_query = data.get('message', '').strip()
    conversation_id = data.get('conversation_id')
    category_filter = data.get('category')

    if not user_query:
        return jsonify({'error': 'Message cannot be empty.'}), 400

    # 1. Manage Conversation Session
    conv = None
    if conversation_id:
        conv = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first()

    if not conv:
        # Generate friendly title from first query
        title = user_query[:40] + ('...' if len(user_query) > 40 else '')
        conv = Conversation(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            title=title
        )
        db.session.add(conv)
        db.session.commit()

    # 2. Record User Message
    user_msg = Message(
        conversation_id=conv.id,
        sender='user',
        content=user_query
    )
    db.session.add(user_msg)
    db.session.commit()

    # 3. Query RAG Engine
    engine = RAGEngine(
        chroma_dir=current_app.config['CHROMA_PERSIST_DIR'],
        gemini_api_key=current_app.config.get('GEMINI_API_KEY', ''),
        model_name=current_app.config.get('GEMINI_MODEL', 'gemini-2.5-flash')
    )

    rag_result = engine.query(user_query, category=category_filter)

    # 4. Record Assistant Message with Grounded Sources
    assistant_msg = Message(
        conversation_id=conv.id,
        sender='assistant',
        content=rag_result['answer']
    )
    assistant_msg.set_sources(rag_result['sources'])
    
    db.session.add(assistant_msg)
    conv.updated_at = db.func.now()
    db.session.commit()

    return jsonify({
        'success': True,
        'conversation_id': conv.id,
        'conversation_title': conv.title,
        'user_message': user_msg.to_dict(),
        'assistant_message': assistant_msg.to_dict(),
        'is_no_answer': rag_result['is_no_answer'],
        'top_similarity': rag_result['top_similarity']
    })

@chat_bp.route('/api/chat/conversations', methods=['GET'])
@login_required
def list_conversations():
    convs = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.updated_at.desc()).all()
    return jsonify([c.to_dict() for c in convs])

@chat_bp.route('/api/chat/conversations/<conversation_id>', methods=['DELETE'])
@login_required
def delete_conversation(conversation_id):
    conv = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first()
    if not conv:
        return jsonify({'error': 'Conversation not found'}), 404
        
    db.session.delete(conv)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Conversation deleted.'})

@chat_bp.route('/api/feedback/submit', methods=['POST'])
@login_required
def submit_feedback():
    data = request.get_json() or {}
    message_id = data.get('message_id')
    rating = data.get('rating', 1) # 1 or -1
    feedback_type = data.get('feedback_type', FeedbackType.HELPFUL)
    comments = data.get('comments', '').strip()
    reason = data.get('reason', '')

    msg = Message.query.get(message_id)
    if not msg:
        return jsonify({'error': 'Referenced message not found.'}), 404

    # Create feedback entry
    fb = Feedback(
        message_id=msg.id,
        user_id=current_user.id,
        rating=int(rating),
        feedback_type=feedback_type,
        comments=comments or reason,
        status='PENDING'
    )
    db.session.add(fb)

    # If it is reported as incorrect / missing / outdated, also log to ReportedAnswer table
    if rating == -1 or feedback_type != FeedbackType.HELPFUL:
        rep = ReportedAnswer(
            message_id=msg.id,
            user_id=current_user.id,
            reason=reason or feedback_type,
            details=comments,
            status='OPEN'
        )
        db.session.add(rep)

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Thank you! Your feedback has been received and routed to academic administrators for knowledge base review.'
    })
