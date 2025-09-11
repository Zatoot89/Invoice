# SaaS Invoice Generator

This is a SaaS invoice generation application built with Flask. It is designed for small to medium businesses that need professional invoicing capabilities.

## Features

This application currently includes the following core features:

*   **Multi-Tenant Architecture**: Users are grouped by organizations, ensuring data is isolated between different companies.
*   **User Authentication**: Secure user registration, login, and logout functionality.
*   **Client Management**: Users can add and manage a list of their clients.
*   **Invoice Management**:
    *   Create new invoices with multiple line items.
    *   View a list of all invoices.
    *   View detailed information for a single invoice.

## Getting Started

Follow these instructions to get the application running on your local machine for development and testing purposes.

### Prerequisites

*   Python 3.8+
*   pip

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the project root by copying the example file:
    ```bash
    cp .env.example .env
    ```
    Now, open the `.env` file and set the following variables. For local development, you can use a simple secret key and a SQLite database.

    ```
    SECRET_KEY=a-super-secret-key-that-you-should-change
    # For SQLite (development)
    DATABASE_URL=sqlite:///app.db

    # For PostgreSQL (production)
    # DATABASE_URL=postgresql://user:password@localhost/invoicer
    ```

5.  **Run database migrations:**
    You need to set the `FLASK_APP` environment variable first.
    ```bash
    export FLASK_APP=run.py
    flask db upgrade
    ```
    This will create the database file (if using SQLite) and all the necessary tables.

6.  **Run the application:**
    ```bash
    flask run
    ```
    The application will be available at `http://127.0.0.1:5000`.

## Running in GitHub Codespaces

Follow these steps to run the application inside a GitHub Codespace.

1. **Create the Codespace**
   * On the repository page, click **Code** → **Codespaces** → **Create codespace on main**.

2. **Set up a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Copy and edit environment variables**
   ```bash
   cp .env.example .env
   ```
   Open `.env` in the editor and update the values as needed.

5. **Run database migrations**
   ```bash
   export FLASK_APP=run.py
   flask db upgrade
   ```

6. **Launch the development server**
   ```bash
   flask run --host=0.0.0.0 --port=5000
   ```
   The default forwarded port (5000) must be opened in the Codespaces interface to access the application.
