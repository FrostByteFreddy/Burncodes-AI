import os
import json
from uuid import UUID
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from celery import Celery
from app.logging_config import error_logger

load_dotenv()

celery = Celery(__name__)

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)

def create_app():
    app = Flask(__name__)
    app.json_encoder = CustomJSONEncoder
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # --- Configuration and Directory Setup ---
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_default_secret_key')

    # Define base paths for persistent data
    upload_folder = os.getenv("UPLOAD_FOLDER_BASE", "/data/uploads")
    vector_store_path = os.getenv("VECTOR_STORE_PATH_BASE", "/data/chromadb")
    crawl_cache_path = os.getenv("CRAWL_CACHE_PATH", "/data/crawl4ai_cache")

    app.config['UPLOAD_FOLDER_BASE'] = upload_folder
    app.config['VECTOR_STORE_PATH_BASE'] = vector_store_path
    app.config['CRAWL_CACHE_PATH'] = crawl_cache_path

    # Attempt to create directories at startup, but don't crash if it fails
    try:
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(vector_store_path, exist_ok=True)
        os.makedirs(crawl_cache_path, exist_ok=True)
        error_logger.info("Successfully created/ensured data directories.")
    except PermissionError:
        error_logger.warning(
            f"Could not create data directories ({upload_folder}, {vector_store_path}, {crawl_cache_path}). "
            "This is expected if running without write permissions to the volume. "
            "The application will attempt to create subdirectories as needed."
        )

    # --- Celery Configuration ---
    broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
    result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://127.0.0.1:6379/0')

    app.config.update(
        CELERY_BROKER_URL=broker_url,
        CELERY_RESULT_BACKEND=result_backend,
        CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=True
    )

    celery.conf.update(
        broker_url=broker_url,
        result_backend=result_backend,
        broker_connection_retry_on_startup=True
    )

    celery.conf.beat_schedule = {
        'check-job-completion-every-minute': {
            'task': 'app.data_processing.tasks.check_job_completion_task',
            'schedule': 60.0,
        },
    }

    celery.autodiscover_tasks(['app.chat', 'app.data_processing'])


    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask

    # --- Blueprints ---
    from app.auth.routes import auth_bp
    from app.tenants.routes import tenants_bp
    from app.chat.routes import chat_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tenants_bp, url_prefix='/api/tenants')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')

    return app