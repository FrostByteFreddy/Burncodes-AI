# Custom-Branded RAG Chatbot Platform

## Project Overview

*   **High-level description:** This project is a multi-tenant, Retrieval-Augmented Generation (RAG) application that allows businesses to create and deploy custom-branded chatbots. These chatbots are trained on a company's specific knowledge base, such as websites, documentation, and internal files.

*   **Problem it solves:** Many businesses struggle to provide immediate, accurate, and scalable customer support. This platform addresses that by enabling companies to build their own AI-powered chatbots that can answer user questions based on their own data, reducing the load on human support agents and improving customer satisfaction.

*   **Key features:**
    *   **Multi-Tenant Architecture:** Securely manage multiple client accounts, each with its own isolated data, configuration, and branding.
    *   **Flexible Data Ingestion:** Index data from public websites via a powerful web crawler or by uploading local files (PDF, TXT, CSV, etc.).
    *   **Customizable AI Persona:** Tailor the chatbot's personality and response style to match a company's brand voice.
    *   **History-Aware Conversations:** The chatbot remembers previous turns in the conversation to provide more contextually relevant answers.

## Features

*   **Multi-tenancy:** Each tenant operates in a logically isolated environment. Data sources, chat history, fine-tuning rules, and UI configurations are unique to each tenant, ensuring data privacy and security.

*   **Data ingestion:**
    *   **Web Crawler:** A sophisticated, distributed web crawler can index an entire website or a specific section. It handles dynamic content, respects `robots.txt`, and can be configured to exclude specific paths.
    *   **File Upload:** Supports a wide range of file formats, including PDF, TXT, CSV, and more. Uploaded files are processed, chunked, and added to the tenant's knowledge base.

*   **RAG pipeline:** The core of the application is a state-of-the-art RAG pipeline built with LangChain. It uses a vector store for efficient similarity searches and leverages powerful language models to generate human-like responses.

*   **Chat functionality:** The frontend provides a clean, real-time chat interface for end-users. It maintains a history of the conversation, allowing the AI to understand context and follow-up questions.

*   **UI Customization:** The appearance of the chat widget is highly customizable to match a company's branding. Through a tenant-specific configuration, you can control:
    *   **Colors:** Customize the colors of the header, user and bot messages, buttons, and input fields.
    *   **Logo:** Display a custom logo in the chat header.
    *   **Text:** Change the chatbot's title and the input placeholder text.

## How it Works

### Data Indexing Pipeline

1.  **Crawling:** When a new website is submitted, a Celery task is initiated to crawl the site. The crawler fetches the content of the pages and extracts the raw text. For file uploads, the content is extracted directly from the file.

2.  **Processing:** The raw text is then processed to remove any unnecessary HTML tags, navigation menus, and other boilerplate content. This ensures that only the most relevant information is indexed.

3.  **Chunking:** The cleaned text is divided into smaller, semantically meaningful chunks. This is a crucial step for the RAG pipeline, as it allows the retriever to find the most relevant pieces of information to answer a user's query.

4.  **Embedding and Storage:** Each chunk of text is then passed through an embedding model (Google's `gemini-embedding-001`) to create a vector representation. These vectors, along with the original text, are stored in a ChromaDB vector store, which is specific to each tenant.

### Chat Pipeline (RAG)

1.  **Query:** A user enters a query into the chat interface.

2.  **History-aware query rewriting:** The user's query and the chat history are passed to a language model to generate a new, standalone query. This is important for follow-up questions, as it provides the necessary context for the retrieval step.

3.  **Retrieval:** The rewritten query is used to search the tenant's vector store. The retriever finds the most relevant chunks of text (documents) from the knowledge base using a Maximal Marginal Relevance (MMR) search.

4.  **Generation:** The retrieved documents, the original query, and the chat history are passed to the final language model (Gemini). The model uses this information to generate a comprehensive and contextually accurate answer.

5.  **Response:** The generated answer is streamed back to the user in the chat interface. The conversation history is updated, and the chat log is stored in the database for future reference.

## Technical Stack

### Backend

*   **Framework:** Flask
*   **Asynchronous tasks:** Celery and Redis
*   **Database:** Supabase (PostgreSQL)
*   **Vector store:** ChromaDB
*   **LLM and embeddings:** Google Gemini and LangChain

### Frontend

*   **Framework:** Vue.js
*   **UI components:** Tailwind CSS
*   **State management:** Pinia
