from fabraforma_server import create_app
from waitress import serve
import logging

# Set up a basic logger for the runner script
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Create the Flask app instance using the application factory
app = create_app()

if __name__ == "__main__":
    log.info("--- Starting Production Server with Waitress ---")
    # Use waitress to serve the application
    serve(app, host='0.0.0.0', port=5000)
