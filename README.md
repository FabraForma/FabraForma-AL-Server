# FabraForma Server (Original)

This is the server-side application for the FabraForma Additive Ledger client. It is a Flask-based application that provides a REST API for managing 3D printing data, processing print log images via OCR, and generating quotations.

This version of the documentation is for the original, single-file server implementation.

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
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the required dependencies:**
    The project's dependencies are listed in `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```
    *Note: The `easyocr` package and its dependencies (`torch`) are quite large and may take some time to download and install.*

## Management Commands

This application includes a command-line interface for management tasks, such as creating a super admin user.

### Creating a Super Admin

To create the initial super admin user, run the following commands from your terminal in the project's root directory:

```bash
# For Linux/macOS
export FLASK_APP=manage.py

# For Windows (Command Prompt)
# set FLASK_APP=manage.py

flask createsuperuser
```
You will be prompted to enter a username, email, and password for the new super admin account.

## Running the Server

Once the setup is complete, you can run the server. The application uses `waitress` as its production-ready WSGI server.

```bash
waitress-serve --host 0.0.0.0 --port 5000 server:app
```

The server will start and be accessible at `http://0.0.0.0:5000`. The first time you run the server, it will create and initialize a `server_data.sqlite` database file with default data. Any errors during startup or operation will be logged to the `logs/server.log` file.
