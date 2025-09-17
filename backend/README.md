# Backend Documentation

This document provides technical details about the backend services, including how to run them, debug them, and understand the architecture.

---

## 1. How to Start the Services

The backend consists of three main services that must be run simultaneously in separate terminals: **Redis**, the **Celery Worker**, and the **Flask Application**.

### Terminal 1: Start Redis

Redis is the message broker that queues tasks for Celery.

```sh
redis-server
```
*Keep this terminal open.*

### Terminal 2: Start the Celery Worker

The Celery worker picks up tasks from the Redis queue and executes them. This is where all the heavy lifting (like data processing and LLM calls) happens.

**Important:** You must use the `-P gevent` flag for the worker to handle asynchronous tasks correctly.

```sh
# Navigate to the backend directory and activate your virtual environment
# e.g., source venv/bin/activate

celery -A celery_worker.celery worker -P gevent --loglevel=info
```
*Keep this terminal open.*

### Terminal 3: Start the Flask Application

The Flask app serves the API that the frontend interacts with.

```sh
# Navigate to the backend directory and activate your virtual environment

python run.py
```
*Keep this terminal open.*

---

## 2. Debugging and Viewing Logs

### Flask Application Logs

-   When you run `python run.py` in the foreground, all application logs (including API requests and errors) will be printed directly to that terminal.
-   To log to a file for background execution, you can run: `python run.py > flask.log 2>&1 &`.

### Celery Worker Logs

-   The Celery worker's logs will be printed to the terminal where it is running. This is the most important place to look for errors related to task execution.
-   The `--loglevel=info` flag provides a good level of detail. For more verbose output, you can use `--loglevel=debug`.

### Redis Logs

-   By default, `redis-server` also logs to its terminal.
-   For a real-time view of all commands being sent to Redis (e.g., to see if tasks are being queued), you can use the `MONITOR` command in a new terminal:
    ```sh
    redis-cli monitor
    ```
    This is very useful for debugging connection and task queuing issues.

---

## 3. Architecture: Where Celery and Redis are Used

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
