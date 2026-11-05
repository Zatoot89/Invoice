#!/usr/bin/env python3
"""
InvoiceFlow Pro Test Environment Setup
Sets up a complete test environment with sample data
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def run_command(command, description, cwd=None):
    """Run a shell command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False

def check_service(url, name, max_retries=10):
    """Check if a service is running"""
    print(f"🔍 Checking {name} at {url}...")
    
    for i in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name} is running")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if i < max_retries - 1:
            print(f"⏳ Waiting for {name}... ({i+1}/{max_retries})")
            time.sleep(3)
    
    print(f"❌ {name} is not responding")
    return False

def setup_test_environment():
    """Set up the complete test environment"""
    print("🚀 Setting up InvoiceFlow Pro Test Environment")
    print("=" * 60)
    
    project_root = Path(__file__).parent.parent
    backend_path = project_root / "backend"
    frontend_path = project_root / "frontend"
    
    # 1. Check Python and Node.js
    print("\n📋 Checking Prerequisites...")
    
    if not run_command("python --version", "Check Python version"):
        print("❌ Python is required. Please install Python 3.11+")
        return False
    
    if not run_command("node --version", "Check Node.js version"):
        print("❌ Node.js is required. Please install Node.js 18+")
        return False
    
    # 2. Check databases
    print("\n🗄️  Checking Database Services...")
    
    if not run_command("pg_isready -q", "Check PostgreSQL"):
        print("❌ PostgreSQL is not running. Please start PostgreSQL service")
        return False
    
    if not run_command("redis-cli ping", "Check Redis"):
        print("❌ Redis is not running. Please start Redis service")
        return False
    
    # 3. Set up backend
    print("\n🐍 Setting up Backend Environment...")
    
    # Create virtual environment if it doesn't exist
    venv_path = backend_path / "venv"
    if not venv_path.exists():
        if not run_command("python -m venv venv", "Create virtual environment", backend_path):
            return False
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
        python_cmd = "venv\\Scripts\\python"
    else:  # Unix/Linux/Mac
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"
    
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Install backend dependencies", backend_path):
        return False
    
    if not run_command(f"{pip_cmd} install pytest pytest-asyncio httpx faker", "Install test dependencies", backend_path):
        return False
    
    # 4. Create test database
    print("\n🗄️  Setting up Test Database...")
    
    # Check if test database exists, create if not
    db_exists = run_command(
        "psql -lqt | cut -d \\| -f 1 | grep -qw invoiceflow_test",
        "Check if test database exists"
    )
    
    if not db_exists:
        if not run_command("createdb invoiceflow_test", "Create test database"):
            return False
    
    # Run database migrations
    if not run_command(f"{python_cmd} -m alembic upgrade head", "Run database migrations", backend_path):
        return False
    
    # 5. Set up frontend
    print("\n⚛️  Setting up Frontend Environment...")
    
    if not run_command("npm install", "Install frontend dependencies", frontend_path):
        return False
    
    # 6. Create environment files
    print("\n🔧 Creating Environment Files...")
    
    # Backend .env file
    backend_env = backend_path / ".env"
    if not backend_env.exists():
        env_content = """
DATABASE_URL=postgresql://localhost/invoiceflow_dev
TEST_DATABASE_URL=postgresql://localhost/invoiceflow_test
SECRET_KEY=dev_secret_key_change_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email Configuration (for testing, use MailHog)
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=noreply@invoiceflow.com

# Stripe Test Keys (replace with your test keys)
STRIPE_PUBLIC_KEY=pk_test_your_stripe_public_key
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# File Storage
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# Admin Settings
ADMIN_EMAIL=admin@invoiceflow.com
""".strip()
        
        with open(backend_env, 'w') as f:
            f.write(env_content)
        print("✅ Backend .env file created")
    
    # Frontend .env file
    frontend_env = frontend_path / ".env.local"
    if not frontend_env.exists():
        env_content = """
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/api/v1/ws
NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_test_your_stripe_public_key
""".strip()
        
        with open(frontend_env, 'w') as f:
            f.write(env_content)
        print("✅ Frontend .env file created")
    
    # 7. Generate test data
    print("\n📊 Generating Test Data...")
    
    test_data_script = project_root / "scripts" / "generate_test_data.py"
    if test_data_script.exists():
        if not run_command(f"{python_cmd} scripts/generate_test_data.py", "Generate test data", project_root):
            print("⚠️  Test data generation failed, but continuing...")
    
    print("\n✅ Test Environment Setup Complete!")
    print("\n📝 Next Steps:")
    print("1. Start the backend server:")
    print(f"   cd {backend_path}")
    print(f"   {python_cmd} -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    print("\n2. Start the frontend server:")
    print(f"   cd {frontend_path}")
    print("   npm run dev")
    print("\n3. Start Celery worker (for background tasks):")
    print(f"   cd {backend_path}")
    print(f"   {python_cmd} -m celery -A app.tasks.recurring_tasks worker --loglevel=info")
    print("\n4. Optional: Start MailHog for email testing:")
    print("   docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog")
    print("\n5. Run API tests:")
    print(f"   cd {project_root}")
    print(f"   {python_cmd} scripts/test_api.py")
    print("\n🌐 Access Points:")
    print("   - Frontend: http://localhost:3000")
    print("   - Backend API: http://localhost:8000")
    print("   - API Docs: http://localhost:8000/docs")
    print("   - MailHog (if running): http://localhost:8025")

def start_development_servers():
    """Start all development servers"""
    print("\n🚀 Starting Development Servers...")
    
    project_root = Path(__file__).parent.parent
    backend_path = project_root / "backend"
    frontend_path = project_root / "frontend"
    
    # Start backend server in background
    print("🐍 Starting backend server...")
    backend_process = subprocess.Popen(
        ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=backend_path
    )
    
    time.sleep(3)  # Give backend time to start
    
    # Check if backend is running
    if check_service("http://localhost:8000/docs", "Backend API"):
        print("🎉 Backend server is ready!")
    else:
        print("❌ Backend server failed to start")
        backend_process.terminate()
        return
    
    # Start frontend server
    print("⚛️  Starting frontend server...")
    try:
        subprocess.run(["npm", "run", "dev"], cwd=frontend_path, check=True)
    except KeyboardInterrupt:
        print("\n⚡ Shutting down servers...")
        backend_process.terminate()
        print("✅ Servers stopped")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='InvoiceFlow Pro Test Environment Setup')
    parser.add_argument('--setup-only', action='store_true', help='Only setup environment, do not start servers')
    parser.add_argument('--start-servers', action='store_true', help='Start development servers after setup')
    
    args = parser.parse_args()
    
    # Setup environment
    if setup_test_environment():
        if args.start_servers and not args.setup_only:
            start_development_servers()
    else:
        print("❌ Environment setup failed")
        sys.exit(1)