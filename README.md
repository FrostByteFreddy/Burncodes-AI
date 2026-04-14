# BurnCodes AI

BurnCodes AI is a Retrieval-Augmented Generation (RAG) application that allows you to create a personalized question-answering system based on your own documents and websites. You can upload files (PDFs, DOCX, TXT, CSV) or provide a URL, and BurnCodes AI will process and index the content. Once your sources are added, you can ask questions in a chat interface and get answers based on the information in your documents.

This project is built with a Vue.js frontend and a Flask backend.

---

## What it Does

-   **File Upload:** Upload your documents to be included in the knowledge base.
-   **Web Crawling:** Provide a URL, and the application will crawl the website, find all internal links, and add the content of all pages to the knowledge base.
-   **Chat Interface:** Ask questions in a natural language chat interface and get answers based on the indexed documents.
-   **Tenant System:** The application supports a multi-tenant system, where each tenant has their own isolated knowledge base. The tenant is specified via a URL parameter (`?tenant=your_tenant_id`).

---

## Setup and Installation

Burncodes AI is designed to be easily run locally using **Docker Compose**. This will orchestrate the database connection, Redis, Celery workers, the Backend API, and the Frontend Vue application automatically.

### Prerequisites
- Docker & Docker Compose installed on your local machine.

### Local Development Setup

1. **Configure Environment Variables**
   Open the `.env` file in the root directory and ensure you provide the necessary keys:
   ```env
   SUPABASE_SERVICE_KEY=your-supabase-service-key
   GOOGLE_API_KEY=your-google-api-key
   ```
   *(Note: The `VITE_SUPABASE_ANON_KEY` and other standard endpoints are already configured for you).*

2. **Start the Stack**
   From the root directory, run:
   ```sh
   docker compose up --build
   ```
   > **Note:** The initial build may take a few minutes as it downloads Playwright browsers for web crawling.

### Accessing the Application

- **Frontend Dashboard:** [http://localhost:5173](http://localhost:5173) (Hot-reloading enabled)
- **Backend API:** [http://localhost:5000](http://localhost:5000) (Hot-reloading enabled)

### Stopping the Services
To gracefully stop the network, press `Ctrl+C` in your terminal, or run:
```sh
docker compose down
```
