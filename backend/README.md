# Backend Architecture

Redis and Celery are used to offload long-running tasks from the main Flask application thread, ensuring the API remains responsive.

### Celery Task Definitions

-   **`app/chat/tasks.py`**: Contains `chat_task`, which handles the entire process of receiving a user query, interacting with the vector database and LLMs, and generating a response.
-   **`app/data_processing/tasks.py`**: Contains tasks for:
    -   `process_local_filepath`: Processing uploaded files.
    -   `process_urls`: Crawling and processing website URLs.
    -   `crawl_links_task`: Discovering links on a given website.

### Triggering Celery Tasks

Tasks are triggered from the Flask API routes using the `.delay()` method.

-   **`app/chat/routes.py`**: The `handle_chat` function calls `chat_task.delay(...)`.
-   **`app/tenants/routes.py`**: The `upload_source`, `crawl_sources`, and `discover_links` functions call their respective data processing tasks.

### Role of Redis

Redis serves two critical functions, configured in `app/__init__.py`:

1.  **Message Broker (`CELERY_BROKER_URL`)**: It acts as a mailbox. The Flask app drops a "task message" into the Redis mailbox.
2.  **Result Backend (`CELERY_RESULT_BACKEND`)**: It acts as a database. The Celery worker picks up the message, executes the task, and then stores the final result (or error) back into Redis. The Flask app can then query Redis to get the status and result of the task.