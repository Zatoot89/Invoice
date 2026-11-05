# InvoiceFlow Pro - Testing Guide

This guide provides comprehensive instructions for testing all components of the InvoiceFlow Pro system, including manual testing procedures, automated test setup, and API testing.

## Table of Contents

1. [Quick Start Testing](#quick-start-testing)
2. [Backend API Testing](#backend-api-testing)
3. [Frontend Testing](#frontend-testing)
4. [Database Testing](#database-testing)
5. [Integration Testing](#integration-testing)
6. [Performance Testing](#performance-testing)
7. [Security Testing](#security-testing)
8. [Automated Testing Setup](#automated-testing-setup)

## Quick Start Testing

### Prerequisites

1. **Environment Setup**
```bash
# Backend dependencies
cd backend
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx

# Frontend dependencies  
cd ../frontend
npm install
npm install --save-dev @testing-library/react @testing-library/jest-dom jest-environment-jsdom
```

2. **Test Database Setup**
```bash
# Create test database
createdb invoiceflow_test

# Run migrations
cd backend
alembic upgrade head
```

3. **Environment Variables**
Create `.env.test` file:
```env
DATABASE_URL=postgresql://username:password@localhost/invoiceflow_test
SECRET_KEY=test_secret_key_change_in_production
STRIPE_SECRET_KEY=sk_test_your_stripe_test_key
STRIPE_WEBHOOK_SECRET=whsec_test_webhook_secret
REDIS_URL=redis://localhost:6379/1
EMAIL_FROM=test@invoiceflow.com
SMTP_HOST=localhost
SMTP_PORT=587
```

## Backend API Testing

### 1. Start the Development Server

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. API Documentation & Interactive Testing

Visit `http://localhost:8000/docs` for Swagger UI where you can:
- View all API endpoints
- Test endpoints interactively
- See request/response schemas
- Generate API tokens

### 3. Manual API Testing with curl

#### Authentication Testing
```bash
# Register a new user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "full_name": "Test User"
  }'

# Login to get access token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpassword123"

# Save the access_token from the response
export TOKEN="your_access_token_here"
```

#### Customer Management Testing
```bash
# Create a customer
curl -X POST "http://localhost:8000/api/v1/customers/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Customer",
    "email": "customer@example.com",
    "phone": "+1-555-0123",
    "company": "Test Company",
    "address_line_1": "123 Test St",
    "city": "Test City",
    "state": "TS",
    "postal_code": "12345",
    "country": "USA"
  }'

# Get all customers
curl -X GET "http://localhost:8000/api/v1/customers/" \
  -H "Authorization: Bearer $TOKEN"

# Get customer by ID (replace 1 with actual ID)
curl -X GET "http://localhost:8000/api/v1/customers/1" \
  -H "Authorization: Bearer $TOKEN"
```

#### Invoice Testing
```bash
# Create an invoice
curl -X POST "http://localhost:8000/api/v1/invoices/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "invoice_number": "INV-0001",
    "issue_date": "2024-01-15T00:00:00",
    "due_date": "2024-02-15T00:00:00",
    "currency": "USD",
    "items": [
      {
        "description": "Web Development Services",
        "quantity": 10,
        "unit_price": 150.00,
        "subtotal": 1500.00,
        "total": 1500.00
      }
    ],
    "subtotal": 1500.00,
    "tax_rate": 8.5,
    "tax_amount": 127.50,
    "total": 1627.50,
    "notes": "Payment due within 30 days"
  }'

# Get all invoices
curl -X GET "http://localhost:8000/api/v1/invoices/" \
  -H "Authorization: Bearer $TOKEN"

# Update invoice status
curl -X PUT "http://localhost:8000/api/v1/invoices/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "sent"
  }'
```

#### Bulk Operations Testing
```bash
# Export customers to CSV
curl -X GET "http://localhost:8000/api/v1/bulk/export/customers" \
  -H "Authorization: Bearer $TOKEN" \
  -o customers_export.csv

# Download customer import template
curl -X GET "http://localhost:8000/api/v1/bulk/template/customers" \
  -H "Authorization: Bearer $TOKEN" \
  -o customer_template.csv

# Import customers (prepare a test CSV file first)
curl -X POST "http://localhost:8000/api/v1/bulk/import/customers" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_customers.csv" \
  -F "update_existing=false"

# Bulk update invoices
curl -X PUT "http://localhost:8000/api/v1/bulk/invoices/update" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_ids": [1, 2],
    "updates": {
      "status": "sent",
      "notes": "Updated via bulk operation"
    }
  }'
```

#### Recurring Invoices Testing
```bash
# Create recurring invoice
curl -X POST "http://localhost:8000/api/v1/recurring/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "invoice_number": "REC-0001",
    "issue_date": "2024-01-15T00:00:00",
    "due_date": "2024-02-15T00:00:00",
    "recurrence_interval": "monthly",
    "recurrence_count": 12,
    "items": [
      {
        "description": "Monthly Subscription",
        "quantity": 1,
        "unit_price": 99.99,
        "subtotal": 99.99,
        "total": 99.99
      }
    ],
    "subtotal": 99.99,
    "total": 99.99
  }'

# Get all recurring invoices
curl -X GET "http://localhost:8000/api/v1/recurring/" \
  -H "Authorization: Bearer $TOKEN"

# Manually process recurring invoices (admin only)
curl -X POST "http://localhost:8000/api/v1/recurring/process?max_invoices=10" \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Testing with Postman

Import the provided Postman collection:

```bash
# Export Postman collection
curl -o InvoiceFlowPro.postman_collection.json \
  "http://localhost:8000/api/v1/docs/postman"
```

## Frontend Testing

### 1. Start the Frontend Development Server

```bash
cd frontend
npm run dev
```

Visit `http://localhost:3000` to access the application.

### 2. Manual Frontend Testing Checklist

#### Authentication Flow
- [ ] Register new user account
- [ ] Login with valid credentials
- [ ] Login with invalid credentials (should fail)
- [ ] Logout functionality
- [ ] Token refresh on page reload

#### Dashboard Testing
- [ ] Dashboard loads with correct stats
- [ ] Charts render properly
- [ ] Recent invoices display
- [ ] Real-time updates via WebSocket

#### Customer Management
- [ ] Create new customer
- [ ] Edit existing customer
- [ ] Delete customer
- [ ] Search and filter customers
- [ ] Pagination works

#### Invoice Management
- [ ] Create new invoice with line items
- [ ] Edit invoice details
- [ ] Change invoice status
- [ ] Generate PDF preview
- [ ] Send invoice via email
- [ ] Delete invoice

#### Bulk Operations
- [ ] Select multiple items
- [ ] Export to CSV
- [ ] Import CSV with validation
- [ ] Bulk update operations
- [ ] Progress indicators work

#### Recurring Invoices
- [ ] Create recurring invoice template
- [ ] View generated invoices
- [ ] Edit recurrence settings
- [ ] Cancel recurring invoice

### 3. Browser Testing

Test in multiple browsers:
- Chrome (latest)
- Firefox (latest)
- Safari (if on Mac)
- Edge (latest)

#### Responsive Design Testing
- Mobile view (320px - 768px)
- Tablet view (768px - 1024px)
- Desktop view (1024px+)

## Database Testing

### 1. Database Schema Validation

```bash
cd backend
python -c "
from app.core.database import engine
from app.models import *
from sqlalchemy import inspect

# Check if all tables exist
inspector = inspect(engine)
tables = inspector.get_table_names()
print('Available tables:', tables)

# Check table structures
for table in ['users', 'customers', 'invoices', 'invoice_items', 'payments']:
    if table in tables:
        columns = inspector.get_columns(table)
        print(f'{table} columns:', [col['name'] for col in columns])
"
```

### 2. Data Integrity Testing

```python
# Run this script to test data relationships
import pytest
from app.models.user import User
from app.models.customer import Customer  
from app.models.invoice import Invoice, InvoiceItem

def test_data_relationships(db_session):
    # Create test user
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    db_session.flush()
    
    # Create test customer
    customer = Customer(user_id=user.id, name="Test Customer", email="customer@test.com")
    db_session.add(customer)
    db_session.flush()
    
    # Create test invoice
    invoice = Invoice(user_id=user.id, customer_id=customer.id, 
                     invoice_number="TEST-001", total=100.00)
    db_session.add(invoice)
    db_session.flush()
    
    # Test relationships
    assert invoice.customer.name == "Test Customer"
    assert invoice.user.email == "test@example.com"
    assert len(user.invoices) == 1
    assert len(customer.invoices) == 1
```

## Integration Testing

### 1. WebSocket Testing

```javascript
// Test WebSocket connections
const ws = new WebSocket('ws://localhost:8000/api/v1/ws');

ws.onopen = function(event) {
    console.log('WebSocket connected');
    
    // Send authentication
    ws.send(JSON.stringify({
        type: 'auth',
        token: 'your_access_token'
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

// Test notifications
setTimeout(() => {
    // Trigger an action that should send notification
    fetch('/api/v1/invoices/', {
        method: 'POST',
        headers: {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(invoiceData)
    });
}, 1000);
```

### 2. Email Testing

Set up a test email server (MailHog recommended):

```bash
# Install MailHog for email testing
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog

# Update .env file
SMTP_HOST=localhost
SMTP_PORT=1025
```

Visit `http://localhost:8025` to view sent emails.

### 3. Payment Integration Testing

Use Stripe test environment:

```bash
# Test card numbers
4242424242424242  # Visa (success)
4000000000000002  # Declined card
4000000000009995  # Insufficient funds
```

## Performance Testing

### 1. API Load Testing with Artillery

```bash
npm install -g artillery

# Create artillery config
cat > load-test.yml << EOF
config:
  target: 'http://localhost:8000'
  phases:
    - duration: 60
      arrivalRate: 10
scenarios:
  - name: "API Load Test"
    requests:
      - get:
          url: "/api/v1/invoices/"
          headers:
            Authorization: "Bearer {{token}}"
EOF

# Run load test
artillery run load-test.yml
```

### 2. Database Performance Testing

```sql
-- Test query performance
EXPLAIN ANALYZE SELECT * FROM invoices WHERE user_id = 1 AND status = 'sent';

-- Test with large dataset
INSERT INTO invoices (user_id, customer_id, invoice_number, total, created_at)
SELECT 1, 1, 'TEST-' || generate_series, 100.00, NOW()
FROM generate_series(1, 10000);

-- Check index usage
SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch 
FROM pg_stat_user_indexes;
```

## Security Testing

### 1. Authentication & Authorization

```bash
# Test without token (should fail)
curl -X GET "http://localhost:8000/api/v1/invoices/"

# Test with invalid token (should fail)
curl -X GET "http://localhost:8000/api/v1/invoices/" \
  -H "Authorization: Bearer invalid_token"

# Test accessing other user's data (should fail)
curl -X GET "http://localhost:8000/api/v1/invoices/999" \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Input Validation

```bash
# Test SQL injection
curl -X GET "http://localhost:8000/api/v1/invoices/?search='; DROP TABLE invoices; --" \
  -H "Authorization: Bearer $TOKEN"

# Test XSS
curl -X POST "http://localhost:8000/api/v1/customers/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "<script>alert('xss')</script>",
    "email": "test@example.com"
  }'

# Test large payload
curl -X POST "http://localhost:8000/api/v1/customers/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "'$(python -c "print('A' * 10000)")'", "email": "test@example.com"}'
```

## Automated Testing Setup

### 1. Backend Unit Tests

Create `backend/tests/test_invoices.py`:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User

client = TestClient(app)

def test_create_invoice():
    # Mock authentication
    def mock_get_current_user():
        return User(id=1, email="test@example.com")
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    invoice_data = {
        "customer_id": 1,
        "invoice_number": "TEST-001",
        "issue_date": "2024-01-01T00:00:00",
        "due_date": "2024-02-01T00:00:00",
        "items": [{
            "description": "Test Item",
            "quantity": 1,
            "unit_price": 100.00,
            "subtotal": 100.00,
            "total": 100.00
        }],
        "subtotal": 100.00,
        "total": 100.00
    }
    
    response = client.post("/api/v1/invoices/", json=invoice_data)
    assert response.status_code == 201
    assert response.json()["invoice"]["invoice_number"] == "TEST-001"
```

Run backend tests:
```bash
cd backend
pytest tests/ -v
```

### 2. Frontend Unit Tests

Create `frontend/src/__tests__/components/BulkActions.test.tsx`:

```tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import BulkActions from '../components/bulk/BulkActions';

test('renders bulk actions component', () => {
  render(
    <BulkActions 
      selectedItems={[1, 2, 3]}
      itemType="invoices"
      onActionComplete={() => {}}
    />
  );
  
  expect(screen.getByText('Actions (3)')).toBeInTheDocument();
  expect(screen.getByText('Export')).toBeInTheDocument();
});
```

Run frontend tests:
```bash
cd frontend
npm test
```

## Test Data Generation

### 1. Create Test Data Script

Create `scripts/generate_test_data.py`:

```python
import asyncio
from faker import Faker
from app.core.database import SessionLocal
from app.models.user import User
from app.models.customer import Customer
from app.models.invoice import Invoice, InvoiceItem

fake = Faker()

async def generate_test_data():
    db = SessionLocal()
    
    try:
        # Create test user
        user = User(
            email="testuser@invoiceflow.com",
            hashed_password="$2b$12$test_hash",
            full_name="Test User",
            is_active=True
        )
        db.add(user)
        db.flush()
        
        # Create test customers
        customers = []
        for i in range(50):
            customer = Customer(
                user_id=user.id,
                name=fake.name(),
                email=fake.email(),
                phone=fake.phone_number(),
                company=fake.company(),
                address_line_1=fake.street_address(),
                city=fake.city(),
                state=fake.state_abbr(),
                postal_code=fake.postcode(),
                country="USA"
            )
            customers.append(customer)
            db.add(customer)
        
        db.flush()
        
        # Create test invoices
        for i in range(200):
            customer = fake.choice(customers)
            invoice = Invoice(
                user_id=user.id,
                customer_id=customer.id,
                invoice_number=f"INV-{str(i+1).zfill(4)}",
                issue_date=fake.date_between(start_date='-1y', end_date='today'),
                due_date=fake.date_between(start_date='today', end_date='+90d'),
                subtotal=fake.pydecimal(left_digits=4, right_digits=2, positive=True),
                total=fake.pydecimal(left_digits=4, right_digits=2, positive=True),
                status=fake.choice(['draft', 'sent', 'paid', 'overdue'])
            )
            db.add(invoice)
            db.flush()
            
            # Add invoice items
            for j in range(fake.random_int(min=1, max=5)):
                item = InvoiceItem(
                    invoice_id=invoice.id,
                    description=fake.text(max_nb_chars=100),
                    quantity=fake.pydecimal(left_digits=2, right_digits=2, positive=True),
                    unit_price=fake.pydecimal(left_digits=3, right_digits=2, positive=True),
                    subtotal=fake.pydecimal(left_digits=4, right_digits=2, positive=True),
                    total=fake.pydecimal(left_digits=4, right_digits=2, positive=True)
                )
                db.add(item)
        
        db.commit()
        print("Test data generated successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error generating test data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(generate_test_data())
```

Run the script:
```bash
cd backend
python scripts/generate_test_data.py
```

## Continuous Integration Testing

Create `.github/workflows/test.yml`:

```yaml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: invoiceflow_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
          
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-asyncio httpx
        
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/invoiceflow_test
        REDIS_URL: redis://localhost:6379/1
      run: |
        cd backend
        pytest tests/ -v

  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
        
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
        
    - name: Run tests
      run: |
        cd frontend
        npm test -- --coverage --watchAll=false
```

This comprehensive testing guide covers all aspects of the InvoiceFlow Pro system. Start with the Quick Start section and gradually work through each testing area based on your specific needs and development phase.