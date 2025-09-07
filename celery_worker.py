from fabraforma_server import create_app
from celery import Celery
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Get Redis URL from environment, default to localhost
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Create a Flask app instance to access its context
flask_app = create_app()

# Create the Celery instance
celery_app = Celery(
    flask_app.import_name,
    backend=REDIS_URL,
    broker=REDIS_URL
)

# Update Celery config from Flask config
celery_app.conf.update(flask_app.config)

# Subclass Task to make sure tasks run in the Flask app context
# This is crucial for tasks to access things like app.config, db_session, etc.
class ContextTask(celery_app.Task):
    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)

celery_app.Task = ContextTask

# Optional: Autodiscover tasks from a 'tasks.py' file in the blueprints
# For now, we will import them manually where needed.
# celery_app.autodiscover_tasks(lambda: [bp.name for bp in flask_app.blueprints.values()])
