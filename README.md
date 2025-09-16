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
    ```
    * `GOOGLE_API_KEY`: Your API key for Google Generative AI.
    * `GEMINI_MODEL`: The Gemini model to use for generating answers.
    * `QUERY_GEMINI_MODEL`: The Gemini model to use for query rewriting and other internal tasks.
    * `FLASK_DEBUG`: Set to `True` for development mode.

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

### Backend

1.  **Make sure your virtual environment is activated.**
2.  **From the `backend` directory, run the Flask application:**
    ```sh
    flask run
    ```
    The backend server will start on `http://127.0.0.1:5000`.

### Frontend

1.  **From the `frontend` directory, run the development server:**
    ```sh
    npm run dev
    ```
    The frontend application will be available at `http://localhost:5173`.

2.  **Open your browser** and navigate to `http://localhost:5173?tenant=der_geruestbauer` to start using the application. You can replace `der_geruestbauer` with any of the other tenant names defined in `backend/instructions.json`.
