from flask import Blueprint, render_template, jsonify, current_app
from app.models import db, Document, FAQ, DocumentStatus
from app.rag.engine import RAGEngine

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    approved_docs_count = Document.query.filter_by(status=DocumentStatus.APPROVED).count()
    verified_faqs_count = FAQ.query.filter_by(is_verified=True).count()
    
    sample_faqs = FAQ.query.filter_by(is_verified=True).limit(6).all()
    
    return render_template(
        'main/index.html',
        docs_count=approved_docs_count,
        faqs_count=verified_faqs_count,
        sample_faqs=sample_faqs
    )

@main_bp.route('/sources')
def sources():
    approved_docs = Document.query.filter_by(status=DocumentStatus.APPROVED).all()
    categories = sorted(list(set(d.category for d in approved_docs if d.category)))
    return render_template('main/sources.html', documents=approved_docs, categories=categories)

@main_bp.route('/faqs')
def faqs():
    all_faqs = FAQ.query.filter_by(is_verified=True).order_by(FAQ.view_count.desc()).all()
    categories = sorted(list(set(f.category for f in all_faqs if f.category)))
    return render_template('main/faqs.html', faqs=all_faqs, categories=categories)

@main_bp.route('/health')
def health():
    """
    Health check endpoint for Render, container orchestrators, and uptime monitors.
    """
    health_status = {
        'status': 'healthy',
        'database': 'connected',
        'vector_store': 'operational',
        'app_name': current_app.config.get('APP_NAME'),
        'ai_provider': current_app.config.get('AI_PROVIDER')
    }

    # Verify Database Connection
    try:
        db.session.execute(db.text('SELECT 1'))
    except Exception as e:
        health_status['status'] = 'degraded'
        health_status['database'] = f'error: {str(e)}'

    # Verify Vector Store
    try:
        engine = RAGEngine(chroma_dir=current_app.config['CHROMA_PERSIST_DIR'])
        stats = engine.get_stats()
        health_status['vector_chunks'] = stats['total_indexed_chunks']
    except Exception as e:
        health_status['vector_store'] = f'error: {str(e)}'

    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code
