"""
api/app/chat/tasks.py — task dispatch stub for the API.
The API only calls chat_task.delay() to queue work.
The actual task runs in worker_chat which has langchain/chromadb installed.
"""
from app import celery


class _TaskProxy:
    def __init__(self, task_name, queue='chat'):
        self._name = task_name
        self._queue = queue

    def delay(self, *args, **kwargs):
        return celery.send_task(self._name, args=args, kwargs=kwargs, queue=self._queue)


chat_task = _TaskProxy('app.chat.tasks.chat_task', queue='chat')
