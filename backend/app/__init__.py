import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

def create_app():
    load_dotenv()

    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # --- Configuration ---
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_default_secret_key')
    app.config['UPLOAD_FOLDER_BASE'] = 'uploads'
    app.config['VECTOR_STORE_PATH_BASE'] = 'chromadb'
    os.makedirs(app.config['UPLOAD_FOLDER_BASE'], exist_ok=True)

    # --- Blueprints ---
    from app.auth.routes import auth_bp
    from app.tenants.routes import tenants_bp
    from app.chat.routes import chat_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tenants_bp, url_prefix='/api/tenants')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')

    return app
