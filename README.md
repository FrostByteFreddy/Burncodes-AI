# SwiftAnswer

SwiftAnswer is a Retrieval-Augmented Generation (RAG) application that allows you to create a personalized question-answering system based on your own documents and websites. You can upload files (PDFs, DOCX, TXT, CSV) or provide a URL, and SwiftAnswer will process and index the content. Once your sources are added, you can ask questions in a chat interface and get answers based on the information in your documents.

This project is built with a Vue.js frontend and a Flask backend.

---

## What it Does

-   **File Upload:** Upload your documents to be included in the knowledge base.
-   **Web Crawling:** Provide a URL, and the application will crawl the website, find all internal links, and add the content of all pages to the knowledge base.
-   **Chat Interface:** Ask questions in a natural language chat interface and get answers based on the indexed documents.
-   **Tenant System:** The application supports a multi-tenant system, where each tenant has their own isolated knowledge base. The tenant is specified via a URL parameter (`?tenant=your_tenant_id`).

---

## Setup and Installation

### Backend

1.  **Navigate to the backend directory:**
    ```sh
    cd backend
    ```
2.  **Create a virtual environment:**
    ```sh
    python -m venv venv
    ```
3.  **Activate the virtual environment:**
    -   **Windows:**
        ```sh
        .\venv\Scripts\activate
        ```
    -   **macOS/Linux:**
        ```sh
        source venv/bin/activate
        ```
4.  **Install the required Python packages:**
    ```sh
    pip install -r requirements.txt
    ```
5.  **Create a `.env` file** in the `backend` directory and add the following environment variables:
    ```env
    GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
    GEMINI_MODEL="gemini-pro"
    QUERY_GEMINI_MODEL="gemini-1.5-flash"
    FLASK_DEBUG=True
    CELERY_BROKER_URL="redis://127.0.0.1:6379/0"
    CELERY_RESULT_BACKEND="redis://127.0.0.1:6379/0"
    ```
    * `GOOGLE_API_KEY`: Your API key for Google Generative AI.
    * `GEMINI_MODEL`: The Gemini model to use for generating answers.
    * `QUERY_GEMINI_MODEL`: The Gemini model to use for query rewriting and other internal tasks.
    * `FLASK_DEBUG`: Set to `True` for development mode.
    * `CELERY_BROKER_URL`: The connection URL for the Redis message broker.
    * `CELERY_RESULT_BACKEND`: The connection URL for the Redis result backend.

### Frontend

1.  **Navigate to the frontend directory:**
    ```sh
    cd frontend
    ```
2.  **Install the required npm packages:**
    ```sh
    npm install
    ```
3.  **Create a `.env` file** in the `frontend` directory and add the following environment variable:
    ```env
    VITE_API_BASE_URL=[http://127.0.0.1:5000/api](http://127.0.0.1:5000/api)
    ```
    * `VITE_API_BASE_URL`: The URL of the backend API.

---

## How to Run the Application

The backend relies on Redis for message broking and Celery for background task processing. These services must be running before you start the Flask application.

### 1. Start Redis

First, you need to have Redis installed and running.

-   **Installation (macOS with Homebrew):**
    ```sh
    brew install redis
    ```
-   **Installation (Debian/Ubuntu):**
    ```sh
    sudo apt-get update
    sudo apt-get install redis-server
    ```

-   **Start the Redis server (in a separate terminal):**
    ```sh
    redis-server
    ```

### 2. Start the Celery Worker

1.  **Open a new terminal window.**
2.  **Navigate to the `backend` directory and activate the virtual environment:**
    ```sh
    cd backend
    source venv/bin/activate
    ```
3.  **Start the Celery worker:**
    ```sh
    celery -A celery_worker.celery worker --loglevel=info
    ```
    This worker will listen for and execute tasks from the queue. Keep this terminal running.

### 3. Start the Flask Application

1.  **Open a third terminal window.**
2.  **Navigate to the `backend` directory and activate the virtual environment.**
3.  **Run the Flask application:**
    ```sh
    python run.py
    ```
    The backend server will start on `http://127.0.0.1:5000`.

### 4. Start the Frontend

1.  **From the `frontend` directory, run the development server:**
    ```sh
    npm run dev
    ```
    The frontend application will be available at `http://localhost:5173`.

2.  **Open your browser** and navigate to `http://localhost:5173` to start using the application.
