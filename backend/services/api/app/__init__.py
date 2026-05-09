"""
services/api/app/__init__.py
Lean Flask factory — only registers HTTP blueprints.
No task imports, no crawl4ai, no langchain at module level.
"""
import os
import json
import time
import uuid
from flask import Flask, g, request
from flask_cors import CORS
from dotenv import load_dotenv
from celery import Celery
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.logging_config import error_logger
from uuid import UUID

load_dotenv()

celery = Celery(__name__)
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    default_limits=["200 per hour"],
)

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)

def create_app():
    app = Flask(__name__)
    app.json_encoder = CustomJSONEncoder

    cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:5173,http://localhost:3000').split(',')
    cors_origins = [o.strip() for o in cors_origins if o.strip()]
    CORS(app, resources={r"/api/*": {"origins": cors_origins}}, supports_credentials=True)
    limiter.init_app(app)

    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        raise RuntimeError("CRITICAL: SECRET_KEY environment variable is not set.")
    app.config['SECRET_KEY'] = secret_key

    # Directory setup
    upload_folder    = os.getenv("UPLOAD_FOLDER_BASE",        "/app/data/uploads")
    vector_store_path = os.getenv("CRAWL4_AI_BASE_DIRECTORY", "/app/data/chromadb")
    log_dir           = os.getenv("LOG_DIR",                   "/app/data/logs")

    app.config['UPLOAD_FOLDER_BASE']       = upload_folder
    app.config['CRAWL4_AI_BASE_DIRECTORY'] = vector_store_path

    try:
        os.makedirs(upload_folder,     exist_ok=True)
        os.makedirs(vector_store_path, exist_ok=True)
        os.makedirs(log_dir,           exist_ok=True)
        error_logger.info("Data directories ready")
    except PermissionError as e:
        error_logger.warning("Could not create data directories: %s", e)

    # Celery config (API only needs to dispatch tasks, not run them)
    broker_url     = os.environ.get('CELERY_BROKER_URL',     'redis://redis:6379/0')
    result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
    celery.conf.update(
        broker_url=broker_url,
        result_backend=result_backend,
        broker_connection_retry_on_startup=True,
        task_default_queue='fast',
        task_routes={
            'app.data_processing.tasks.crawl_tasks.process_single_url_task': {'queue': 'heavy'},
            'app.chat.tasks.chat_task': {'queue': 'chat'},
        },
    )

    # Request/Response logging
    @app.before_request
    def _before():
        g.req_id    = str(uuid.uuid4())[:8]
        g.req_start = time.monotonic()
        error_logger.info("→ %s %s  ip=%s  req_id=%s",
                          request.method, request.path, request.remote_addr, g.req_id)

    @app.after_request
    def _after(response):
        elapsed_ms = int((time.monotonic() - g.req_start) * 1000)
        level = (
            error_logger.error   if response.status_code >= 500 else
            error_logger.warning if response.status_code >= 400 else
            error_logger.info
        )
        level("← %s %s %s  %dms  req_id=%s",
              response.status_code, request.method, request.path, elapsed_ms, g.req_id)
        response.headers["X-Request-ID"] = g.req_id
        return response

    # Blueprints — lazy imports so heavy packages don't bleed in
    from app.auth.routes import auth_bp
    from app.tenants.routes import tenants_bp
    from app.tenants.sources import sources_bp
    from app.tenants.widget import widget_bp
    from app.chat.routes import chat_bp
    from app.billing import billing_bp

    app.register_blueprint(auth_bp,     url_prefix='/api/auth')
    app.register_blueprint(tenants_bp,  url_prefix='/api/tenants')
    app.register_blueprint(sources_bp,  url_prefix='/api/tenants')
    app.register_blueprint(widget_bp,   url_prefix='/api/tenants')
    app.register_blueprint(chat_bp,     url_prefix='/api/chat')
    app.register_blueprint(billing_bp,  url_prefix='/api/billing')

    @app.route('/api/health')
    def health_check():
        from flask import jsonify as _jsonify
        status = {"status": "ok", "service": "swiftanswer-api"}
        try:
            from app.database.supabase_client import supabase
            supabase.table('tenants').select("id").limit(1).execute()
            status["database"] = "ok"
        except Exception:
            status["database"] = "error"
            status["status"]   = "degraded"
        return _jsonify(status), 200 if status["status"] == "ok" else 503

    return app
