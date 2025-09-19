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

    # --- Configuration ---
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_default_secret_key')
    app.config['UPLOAD_FOLDER_BASE'] = os.getenv("UPLOADS_DIR", "uploads")
    app.config['VECTOR_STORE_PATH_BASE'] = os.getenv("CHROMADB_PATH", "chromadb")

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