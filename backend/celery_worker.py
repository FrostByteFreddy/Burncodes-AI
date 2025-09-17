import gevent.monkey
gevent.monkey.patch_all()

from app import create_app, celery

app = create_app()
app.app_context().push()
