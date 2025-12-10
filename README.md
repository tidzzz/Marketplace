# API Abilan Tidiane - IMT Second-Hand Marketplace

This project is a second-hand marketplace web application developed with Flask. It provides a REST API for managing users, categories, listings, and transactions, as well as a basic user interface rendered with Jinja2 templates.

## Tech Stack

- **Language**: Python 3.8+
- **Web Framework**: Flask
- **ORM**: SQLAlchemy
- **Database**: SQLite
- **API Spec**: OpenAPI 3.1 (`full_openapi.yaml`)

## Project Structure

```text
app.py                    # Flask application entry point
full_openapi.yaml         # OpenAPI specification
requirements.txt          # Python dependencies
start.sh                  # Quick start script
tests/                    # Tests folder
  test_scenario.py        # Reproducible test scenarios
database/
  database.py             # DB initialization
  models.py               # Data models
  database.db             # SQLite file (generated)
src/
  templates/              # Jinja2 templates
instance/
  uploads/                # Uploaded files storage
```

## Installation and Startup

### Option 1: Quick Start (macOS/Linux)

A `start.sh` script is provided to automate virtual environment creation, dependency installation, and application launch.

```bash
chmod +x start.sh
./start.sh
```

### Option 2: Manual Installation

1. **Create a virtual environment**:

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # macOS/Linux
    # or
    venv\Scripts\activate     # Windows
    ```

2. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

3. **Run the application**:

    ```bash
    python app.py
    ```

The application will be accessible at: `http://127.0.0.1:5000`.

## API Usage

The API follows the specification defined in `full_openapi.yaml`.

### Authentication

Authentication for tests and the API is done via the `X-User-Email` HTTP header.

- **Admin**: `admin@imt.test` (for privileged operations like creating categories)
- **Standard User**: Any email registered via `POST /api/users`.

### Examples (cURL)

**Create a category (Admin only)**:

```bash
curl -X POST http://127.0.0.1:5000/api/categories \
  -H 'Content-Type: application/json' \
  -H 'X-User-Email: admin@imt.test' \
  -d '{"name":"Computing"}'
```

**List categories**:

```bash
curl -X GET http://127.0.0.1:5000/api/categories
```

## Reproducible Tests

Automated test scenarios are available in the `tests/` folder. These tests use an in-memory database to avoid affecting your local data.

To run the tests:

```bash
# Ensure you are in the virtual environment
source venv/bin/activate

# Run tests
python -m unittest discover tests
```

The `tests/test_scenario.py` file contains a complete scenario verifying:

1. Initial state (empty).
2. Category creation by an admin.
3. Data persistence and retrieval.
4. Security (creation refusal for non-admins).


