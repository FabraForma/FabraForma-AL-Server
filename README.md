# FabraForma Server

This is the server-side application for the FabraForma Additive Ledger client. It is a Flask-based application that provides a REST API for managing 3D printing data, processing print log images via OCR, and generating quotations.

## Features

- **User & Company Management:** Multi-tenant system with JWT-based authentication.
- **Data Management:** CRUD APIs for managing printers and filament inventory.
- **Automated Logging:** An image processing pipeline that uses EasyOCR to read print summary images, which are then verified by a user and logged.
- **Reporting:** Generates detailed individual Excel logs for each print and maintains a master monthly log.
- **File Management:** Allows admin users to browse, upload, and download files from a shared server directory.
- **Quotation Generation:** Creates PDF quotations based on print data and configurable margins.

## Project Setup

### Prerequisites

- Python 3.9+
- A virtual environment tool (e.g., `venv`)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-folder>
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\\Scripts\\activate`
    ```

3.  **Install the required dependencies:**
    The project's dependencies are listed in `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Environment Variables:**
    The server requires a `SECRET_KEY` for signing JWTs. For production, you should also configure a proper database URI.

    Create a file named `.env` in the root of the project and add the following:
    ```
    SECRET_KEY='a-very-strong-and-secret-key-that-you-generate'
    # For future database migrations (e.g., to PostgreSQL)
    # DATABASE_URI='postgresql://user:password@host:port/dbname'
    ```
    *Note: The `SECRET_KEY` should be a long, random string.*

5.  **Initialize the Database:**
    This project uses Alembic to manage database migrations. To create the initial database tables from the models, run the following command:
    ```bash
    alembic upgrade head
    ```
    This will create the `server_data.sqlite` file (if it doesn't exist) and set up all the necessary tables.

## Running the Server

The application now consists of three main components that need to be run: the Redis message broker, the Celery worker for background tasks, and the Flask web server itself.

### 1. Run Redis

A Redis server must be running for Celery to use as a message broker. The easiest way to run Redis locally is with Docker:
```bash
docker run -d -p 6379:6379 redis
```

### 2. Run the Celery Worker

Open a new terminal, navigate to the project directory, and activate the virtual environment. Then, start the Celery worker:
```bash
celery -A celery_worker.celery_app worker --loglevel=info
```
The worker will connect to Redis and wait for tasks to be dispatched from the Flask application.

### 3. Run the Flask Web Server

Finally, open a third terminal, activate the virtual environment, and run the Flask application using the `run.py` script:

```bash
python run.py
```

The server will start using Waitress and be accessible at `http://0.0.0.0:5000`. The `run.py` script handles the creation of the app and serving it.
