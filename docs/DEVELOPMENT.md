# InvoiceFlow Pro - Development Guide

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure](#project-structure)
3. [Coding Standards](#coding-standards)
4. [Development Workflow](#development-workflow)
5. [Testing](#testing)
6. [Database Development](#database-development)
7. [API Development](#api-development)
8. [Frontend Development](#frontend-development)
9. [Real-time Features](#real-time-features)
10. [Performance Optimization](#performance-optimization)
11. [Debugging](#debugging)
12. [Contributing](#contributing)

## Development Environment Setup

### Prerequisites

- **Python 3.11+** with pip and virtualenv
- **Node.js 18+** with npm
- **PostgreSQL 16+** with TimescaleDB extension
- **Redis 7.0+**
- **Git** for version control
- **Docker & Docker Compose** (recommended)
- **IDE**: VS Code, PyCharm, or similar

### Initial Setup

```bash
# Clone repository
git clone https://github.com/yourusername/invoiceflow-pro.git
cd invoiceflow-pro

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Option 1: Docker setup (recommended for quick start)
docker-compose up -d

# Option 2: Manual setup
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Frontend setup
cd ../frontend
npm install

# Database setup (if not using Docker)
createdb invoiceflow_dev
psql invoiceflow_dev -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

### Development Tools Setup

#### VS Code Extensions (Recommended)
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.flake8",
    "ms-python.mypy-type-checker",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "ms-vscode.vscode-json",
    "ms-vscode-remote.remote-containers"
  ]
}
```

#### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Set up git hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

#### Pre-commit Configuration (.pre-commit-config.yaml)
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 22.12.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --ignore=E203,W503]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.0-alpha.4
    hooks:
      - id: prettier
        files: \.(js|jsx|ts|tsx|json|css|md|yaml|yml)$
```

### Environment Variables

#### Development Environment (.env)
```bash
# Development settings
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production

# Database
DATABASE_URL=postgresql://invoiceflow:password@localhost:5432/invoiceflow_dev
REDIS_URL=redis://localhost:6379/0

# External services (use test keys)
STRIPE_PUBLISHABLE_KEY=pk_test_your_test_key
STRIPE_SECRET_KEY=sk_test_your_test_key
STRIPE_WEBHOOK_SECRET=whsec_test_your_webhook_secret

# Email (use test service)
SMTP_HOST=smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USER=your_mailtrap_user
SMTP_PASSWORD=your_mailtrap_password

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/api/v1/ws
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_test_key

# Feature flags
ENABLE_DEBUG_TOOLBAR=true
ENABLE_ANALYTICS=true
ENABLE_REAL_TIME=true
```

## Project Structure

### Backend Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── core/                   # Core configuration and utilities
│   │   ├── config.py          # Application configuration
│   │   ├── security.py        # Authentication and security
│   │   ├── database.py        # Database connection and session
│   │   ├── deps.py            # FastAPI dependencies
│   │   └── exceptions.py      # Custom exception classes
│   ├── api/                   # API routes and endpoints
│   │   ├── routes.py          # Main router
│   │   └── v1/                # API version 1
│   │       ├── auth.py        # Authentication endpoints
│   │       ├── users.py       # User management
│   │       ├── customers.py   # Customer management
│   │       ├── invoices.py    # Invoice operations
│   │       ├── payments.py    # Payment processing
│   │       ├── analytics.py   # Analytics endpoints
│   │       └── websocket.py   # WebSocket endpoints
│   ├── models/                # Database models
│   │   ├── __init__.py
│   │   ├── base.py           # Base model class
│   │   ├── user.py           # User model
│   │   ├── customer.py       # Customer model
│   │   ├── invoice.py        # Invoice and InvoiceItem models
│   │   ├── payment.py        # Payment model
│   │   └── audit.py          # Audit log model
│   ├── schemas/              # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py          # User schemas
│   │   ├── customer.py      # Customer schemas
│   │   ├── invoice.py       # Invoice schemas
│   │   └── payment.py       # Payment schemas
│   ├── services/            # Business logic services
│   │   ├── __init__.py
│   │   ├── auth_service.py      # Authentication service
│   │   ├── invoice_service.py   # Invoice business logic
│   │   ├── payment_service.py   # Payment processing
│   │   ├── email_service.py     # Email sending
│   │   ├── pdf_service.py       # PDF generation
│   │   ├── analytics_service.py # Analytics calculations
│   │   └── websocket_service.py # WebSocket management
│   ├── utils/               # Utility functions
│   │   ├── __init__.py
│   │   ├── email.py         # Email utilities
│   │   ├── pdf.py           # PDF utilities
│   │   └── validators.py    # Custom validators
│   └── workers/             # Celery workers and tasks
│       ├── __init__.py
│       ├── celery_app.py    # Celery configuration
│       ├── email_tasks.py   # Email sending tasks
│       └── invoice_tasks.py # Invoice processing tasks
├── migrations/              # Alembic database migrations
├── tests/                   # Test files
│   ├── __init__.py
│   ├── conftest.py         # Test configuration
│   ├── test_auth.py        # Authentication tests
│   ├── test_invoices.py    # Invoice tests
│   └── test_analytics.py   # Analytics tests
├── requirements.txt         # Python dependencies
├── requirements-dev.txt     # Development dependencies
└── alembic.ini             # Alembic configuration
```

### Frontend Structure
```
frontend/
├── public/                  # Static assets
├── src/
│   ├── components/         # React components
│   │   ├── layout/        # Layout components
│   │   ├── forms/         # Form components
│   │   ├── analytics/     # Analytics components
│   │   ├── invoices/      # Invoice components
│   │   ├── customers/     # Customer components
│   │   ├── payments/      # Payment components
│   │   └── notifications/ # Notification components
│   ├── pages/             # Next.js pages
│   │   ├── _app.tsx       # App component
│   │   ├── _document.tsx  # Document component
│   │   ├── index.tsx      # Home page
│   │   ├── dashboard.tsx  # Dashboard page
│   │   ├── invoices/      # Invoice pages
│   │   ├── customers/     # Customer pages
│   │   ├── analytics.tsx  # Analytics page
│   │   └── api/           # API routes
│   ├── hooks/             # Custom React hooks
│   │   ├── useAuth.ts     # Authentication hook
│   │   ├── useInvoices.ts # Invoice management hook
│   │   ├── useAnalytics.ts# Analytics hook
│   │   └── useWebSocket.ts# WebSocket hook
│   ├── contexts/          # React contexts
│   │   ├── AuthContext.tsx    # Authentication context
│   │   └── NotificationContext.tsx # Notification context
│   ├── lib/               # Utility libraries
│   │   ├── api.ts         # API client
│   │   ├── auth.ts        # Authentication utilities
│   │   ├── utils.ts       # General utilities
│   │   └── validations.ts # Form validations
│   ├── stores/            # State management
│   │   ├── authStore.ts   # Authentication store
│   │   └── uiStore.ts     # UI state store
│   ├── styles/            # CSS styles
│   │   ├── globals.css    # Global styles
│   │   └── components.css # Component styles
│   └── types/             # TypeScript types
│       ├── index.ts       # Common types
│       ├── api.ts         # API types
│       └── models.ts      # Data model types
├── package.json           # Node.js dependencies
├── tsconfig.json          # TypeScript configuration
├── tailwind.config.js     # Tailwind CSS configuration
├── next.config.js         # Next.js configuration
└── .eslintrc.js          # ESLint configuration
```

## Coding Standards

### Python (Backend)

#### Style Guide
- Follow **PEP 8** for Python code style
- Use **Black** for code formatting (line length: 88)
- Use **isort** for import sorting
- Use **flake8** for linting
- Use **mypy** for type checking

#### Code Organization
```python
# Standard library imports
import asyncio
import json
from datetime import datetime
from typing import List, Optional, Dict, Any

# Third-party imports
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Local imports
from app.core.database import get_db
from app.models.invoice import Invoice
from app.schemas.invoice import InvoiceCreate
from app.services.invoice_service import InvoiceService

# Constants at module level
MAX_INVOICE_ITEMS = 100
DEFAULT_CURRENCY = "USD"

# Class definitions
class InvoiceController:
    """Invoice management controller."""
    
    def __init__(self, service: InvoiceService):
        self.service = service
    
    async def create_invoice(
        self, 
        invoice_data: InvoiceCreate, 
        db: Session = Depends(get_db)
    ) -> Invoice:
        """Create a new invoice."""
        try:
            return await self.service.create_invoice(db, invoice_data)
        except Exception as e:
            logger.error(f"Failed to create invoice: {str(e)}")
            raise HTTPException(status_code=500, detail="Invoice creation failed")
```

#### Type Hints
```python
# Always use type hints
from typing import List, Dict, Optional, Union, Any
from decimal import Decimal

def calculate_invoice_total(
    items: List[Dict[str, Union[str, Decimal, int]]], 
    tax_rate: Optional[Decimal] = None
) -> Decimal:
    """Calculate invoice total with optional tax."""
    subtotal = sum(item["quantity"] * item["unit_price"] for item in items)
    tax_amount = subtotal * (tax_rate or Decimal('0')) / 100
    return subtotal + tax_amount
```

#### Error Handling
```python
# Custom exceptions
class InvoiceFlowException(Exception):
    """Base exception for InvoiceFlow Pro."""
    
    def __init__(self, message: str, error_code: str = "GENERAL_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class InvoiceNotEditableException(InvoiceFlowException):
    """Raised when trying to edit a non-editable invoice."""
    
    def __init__(self, invoice_id: int, status: str):
        message = f"Invoice {invoice_id} with status '{status}' is not editable"
        super().__init__(message, "INVOICE_NOT_EDITABLE")

# Usage
async def update_invoice(invoice_id: int, data: InvoiceUpdate) -> Invoice:
    try:
        invoice = await get_invoice_by_id(invoice_id)
        if invoice.status != "draft":
            raise InvoiceNotEditableException(invoice_id, invoice.status)
        
        return await update_invoice_data(invoice, data)
    
    except InvoiceNotEditableException:
        raise  # Re-raise custom exceptions
    except Exception as e:
        logger.error(f"Unexpected error updating invoice {invoice_id}: {str(e)}")
        raise InvoiceFlowException(f"Failed to update invoice: {str(e)}")
```

#### Database Operations
```python
# Use async/await for database operations
async def get_user_invoices(
    db: AsyncSession, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 20
) -> List[Invoice]:
    """Get paginated list of user's invoices."""
    query = (
        select(Invoice)
        .where(Invoice.user_id == user_id)
        .options(selectinload(Invoice.items), selectinload(Invoice.customer))
        .offset(skip)
        .limit(limit)
        .order_by(Invoice.created_at.desc())
    )
    
    result = await db.execute(query)
    return result.scalars().all()

# Use transactions for multi-table operations
async def create_invoice_with_items(
    db: AsyncSession, 
    invoice_data: InvoiceCreate
) -> Invoice:
    """Create invoice with items in a transaction."""
    async with db.begin():
        # Create invoice
        invoice = Invoice(**invoice_data.dict(exclude={'items'}))
        db.add(invoice)
        await db.flush()  # Get the ID
        
        # Create items
        for item_data in invoice_data.items:
            item = InvoiceItem(invoice_id=invoice.id, **item_data.dict())
            db.add(item)
        
        await db.commit()
        await db.refresh(invoice)
        
        return invoice
```

### TypeScript/React (Frontend)

#### Style Guide
- Use **Prettier** for code formatting
- Use **ESLint** for linting
- Follow **React best practices**
- Use **TypeScript strict mode**

#### Component Structure
```tsx
// components/invoices/InvoiceList.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardBody, Button, Spinner } from '@nextui-org/react';
import { useInvoices } from '@/hooks/useInvoices';
import { Invoice } from '@/types/models';

// Props interface
interface InvoiceListProps {
  customerId?: number;
  status?: string;
  onInvoiceSelect?: (invoice: Invoice) => void;
  className?: string;
}

// Component with proper TypeScript
export default function InvoiceList({
  customerId,
  status,
  onInvoiceSelect,
  className
}: InvoiceListProps) {
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  
  const {
    invoices,
    loading,
    error,
    refreshInvoices
  } = useInvoices({
    customerId,
    status,
    autoRefresh: true
  });

  // Event handlers
  const handleInvoiceClick = useCallback((invoice: Invoice) => {
    setSelectedInvoice(invoice);
    onInvoiceSelect?.(invoice);
  }, [onInvoiceSelect]);

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" label="Loading invoices..." />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <Card className="border-danger-200">
        <CardBody className="text-center py-8">
          <p className="text-danger-600 mb-4">{error}</p>
          <Button color="primary" variant="flat" onPress={refreshInvoices}>
            Try Again
          </Button>
        </CardBody>
      </Card>
    );
  }

  // Main render
  return (
    <div className={`space-y-4 ${className}`}>
      {invoices.length === 0 ? (
        <Card>
          <CardBody className="text-center py-8">
            <p className="text-gray-500">No invoices found</p>
          </CardBody>
        </Card>
      ) : (
        invoices.map((invoice) => (
          <InvoiceCard
            key={invoice.id}
            invoice={invoice}
            isSelected={selectedInvoice?.id === invoice.id}
            onClick={() => handleInvoiceClick(invoice)}
          />
        ))
      )}
    </div>
  );
}

// Sub-component
interface InvoiceCardProps {
  invoice: Invoice;
  isSelected: boolean;
  onClick: () => void;
}

function InvoiceCard({ invoice, isSelected, onClick }: InvoiceCardProps) {
  return (
    <Card
      isPressable
      onPress={onClick}
      className={`cursor-pointer transition-all ${
        isSelected ? 'ring-2 ring-primary-500' : 'hover:shadow-md'
      }`}
    >
      <CardBody>
        {/* Card content */}
      </CardBody>
    </Card>
  );
}
```

#### Custom Hooks
```tsx
// hooks/useInvoices.ts
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Invoice, InvoiceFilters } from '@/types/models';
import { invoiceApi } from '@/lib/api';

interface UseInvoicesOptions {
  customerId?: number;
  status?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface UseInvoicesReturn {
  invoices: Invoice[];
  loading: boolean;
  error: string | null;
  totalCount: number;
  createInvoice: (data: InvoiceCreateData) => Promise<Invoice>;
  updateInvoice: (id: number, data: InvoiceUpdateData) => Promise<Invoice>;
  deleteInvoice: (id: number) => Promise<void>;
  refreshInvoices: () => Promise<void>;
}

export function useInvoices(options: UseInvoicesOptions = {}): UseInvoicesReturn {
  const { token } = useAuth();
  const [state, setState] = useState({
    invoices: [] as Invoice[],
    loading: true,
    error: null as string | null,
    totalCount: 0
  });

  const fetchInvoices = useCallback(async () => {
    if (!token) return;

    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      const filters: InvoiceFilters = {
        customerId: options.customerId,
        status: options.status
      };
      
      const response = await invoiceApi.getInvoices(filters, token);
      
      setState(prev => ({
        ...prev,
        invoices: response.items,
        totalCount: response.total,
        loading: false
      }));
      
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch invoices'
      }));
    }
  }, [token, options.customerId, options.status]);

  // Auto-refresh setup
  useEffect(() => {
    fetchInvoices();

    if (options.autoRefresh && options.refreshInterval) {
      const interval = setInterval(fetchInvoices, options.refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchInvoices, options.autoRefresh, options.refreshInterval]);

  // CRUD operations
  const createInvoice = useCallback(async (data: InvoiceCreateData): Promise<Invoice> => {
    if (!token) throw new Error('No authentication token');

    const invoice = await invoiceApi.createInvoice(data, token);
    setState(prev => ({
      ...prev,
      invoices: [invoice, ...prev.invoices]
    }));
    
    return invoice;
  }, [token]);

  const updateInvoice = useCallback(async (id: number, data: InvoiceUpdateData): Promise<Invoice> => {
    if (!token) throw new Error('No authentication token');

    const updatedInvoice = await invoiceApi.updateInvoice(id, data, token);
    setState(prev => ({
      ...prev,
      invoices: prev.invoices.map(inv => 
        inv.id === id ? updatedInvoice : inv
      )
    }));
    
    return updatedInvoice;
  }, [token]);

  const deleteInvoice = useCallback(async (id: number): Promise<void> => {
    if (!token) throw new Error('No authentication token');

    await invoiceApi.deleteInvoice(id, token);
    setState(prev => ({
      ...prev,
      invoices: prev.invoices.filter(inv => inv.id !== id)
    }));
  }, [token]);

  return {
    ...state,
    createInvoice,
    updateInvoice,
    deleteInvoice,
    refreshInvoices: fetchInvoices
  };
}
```

#### Type Definitions
```tsx
// types/models.ts
export interface User {
  id: number;
  email: string;
  full_name: string;
  company_name?: string;
  role: 'admin' | 'user' | 'accountant' | 'viewer';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Customer {
  id: number;
  name: string;
  email?: string;
  phone?: string;
  company?: string;
  address?: Address;
  tax_id?: string;
  payment_terms: number;
  currency: string;
  is_active: boolean;
  total_invoiced: number;
  total_paid: number;
  outstanding_balance: number;
  created_at: string;
  updated_at: string;
}

export interface Address {
  street: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
}

export interface Invoice {
  id: number;
  invoice_number: string;
  customer_id: number;
  customer?: Customer;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  issue_date: string;
  due_date: string;
  subtotal: number;
  tax_rate: number;
  tax_amount: number;
  total_amount: number;
  currency: string;
  notes?: string;
  items: InvoiceItem[];
  payments: Payment[];
  sent_at?: string;
  paid_at?: string;
  created_at: string;
  updated_at: string;
}

export interface InvoiceItem {
  id: number;
  description: string;
  quantity: number;
  unit_price: number;
  total: number;
}

// API types
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  errors?: Record<string, string[]>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pages: number;
  per_page: number;
  has_next: boolean;
  has_prev: boolean;
}
```

## Development Workflow

### Git Workflow

#### Branch Strategy
```bash
# Main branches
main        # Production-ready code
develop     # Development integration branch
staging     # Staging environment branch

# Feature branches
feature/user-authentication
feature/invoice-pdf-generation
feature/payment-integration

# Bugfix branches  
bugfix/invoice-calculation-error
bugfix/email-template-formatting

# Hotfix branches
hotfix/security-vulnerability
hotfix/critical-payment-bug
```

#### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format: type(scope): description
feat(invoices): add PDF generation with custom templates
fix(payments): resolve Stripe webhook signature validation
docs(api): update authentication documentation
refactor(database): optimize invoice queries for performance
test(analytics): add unit tests for dashboard calculations
chore(deps): update dependencies to latest versions
```

#### Pull Request Template
```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Refactoring

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Performance impact assessed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings or errors
- [ ] Database migrations included (if applicable)

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Related Issues
Fixes #123
Related to #456
```

### Development Tasks

#### Daily Development Routine
```bash
# Start development session
git checkout develop
git pull origin develop
cd backend && source venv/bin/activate
cd ../frontend && npm install  # If package.json changed

# Start services
docker-compose up -d postgres redis rabbitmq  # Infrastructure
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000  # Backend
npm run dev  # Frontend (separate terminal)

# Run tests before committing
pytest  # Backend tests
npm test  # Frontend tests
pre-commit run --all-files  # Linting and formatting
```

#### Code Review Checklist

**Backend Reviews:**
- [ ] Proper error handling with custom exceptions
- [ ] Database queries are optimized and use proper indexing
- [ ] API endpoints have proper authentication and authorization
- [ ] Input validation using Pydantic schemas
- [ ] Async/await used correctly for I/O operations
- [ ] Proper logging for debugging and monitoring
- [ ] Type hints are comprehensive and accurate

**Frontend Reviews:**
- [ ] Components are properly typed with TypeScript
- [ ] State management follows established patterns
- [ ] Error boundaries handle component failures
- [ ] Loading states provide good user feedback
- [ ] Accessibility standards are met (ARIA, keyboard navigation)
- [ ] Performance optimizations (memo, useMemo, useCallback)
- [ ] Mobile responsiveness is maintained

## Testing

### Backend Testing

#### Test Structure
```python
# tests/conftest.py
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db
from app.models.base import Base

# Test database setup
SQLALCHEMY_DATABASE_URL = "postgresql://test:test@localhost/test_invoiceflow"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def db_session():
    """Create a database session for testing."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
async def client(db_session):
    """Create a test client."""
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def authenticated_client(client, db_session):
    """Create an authenticated test client."""
    # Create test user and return client with auth headers
    user = await create_test_user(db_session)
    token = create_access_token(user.id)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
```

#### Unit Tests
```python
# tests/test_invoice_service.py
import pytest
from decimal import Decimal
from app.services.invoice_service import InvoiceService
from app.schemas.invoice import InvoiceCreate, InvoiceItemCreate
from app.models.invoice import Invoice, InvoiceStatus

@pytest.mark.asyncio
class TestInvoiceService:
    
    async def test_create_invoice_success(self, db_session):
        """Test successful invoice creation."""
        service = InvoiceService()
        customer = await create_test_customer(db_session)
        
        invoice_data = InvoiceCreate(
            customer_id=customer.id,
            issue_date="2024-01-15",
            due_date="2024-02-15",
            currency="USD",
            tax_rate=Decimal("8.0"),
            items=[
                InvoiceItemCreate(
                    description="Test Item",
                    quantity=Decimal("2"),
                    unit_price=Decimal("100.00")
                )
            ]
        )
        
        invoice = await service.create_invoice(db_session, 1, invoice_data)
        
        assert invoice.status == InvoiceStatus.DRAFT
        assert invoice.total_amount == Decimal("216.00")  # 200 + 8% tax
        assert len(invoice.items) == 1
        assert invoice.items[0].total == Decimal("200.00")

    async def test_create_invoice_invalid_customer(self, db_session):
        """Test invoice creation with invalid customer."""
        service = InvoiceService()
        
        invoice_data = InvoiceCreate(
            customer_id=999,  # Non-existent customer
            issue_date="2024-01-15",
            due_date="2024-02-15",
            currency="USD",
            items=[InvoiceItemCreate(description="Test", quantity=1, unit_price=100)]
        )
        
        with pytest.raises(CustomerNotFoundException):
            await service.create_invoice(db_session, 1, invoice_data)

    async def test_invoice_total_calculation(self):
        """Test invoice total calculation logic."""
        service = InvoiceService()
        
        items = [
            {"quantity": Decimal("2"), "unit_price": Decimal("100.00")},
            {"quantity": Decimal("1"), "unit_price": Decimal("50.00")},
        ]
        
        subtotal = service.calculate_subtotal(items)
        tax_amount = service.calculate_tax(subtotal, Decimal("10.0"))
        total = subtotal + tax_amount
        
        assert subtotal == Decimal("250.00")
        assert tax_amount == Decimal("25.00")
        assert total == Decimal("275.00")
```

#### API Tests
```python
# tests/test_api_invoices.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestInvoiceAPI:
    
    async def test_create_invoice_success(self, authenticated_client: AsyncClient):
        """Test successful invoice creation via API."""
        customer = await create_test_customer()
        
        invoice_data = {
            "customer_id": customer.id,
            "issue_date": "2024-01-15",
            "due_date": "2024-02-15",
            "currency": "USD",
            "tax_rate": 8.0,
            "items": [
                {
                    "description": "Test Service",
                    "quantity": 2,
                    "unit_price": 100.00
                }
            ]
        }
        
        response = await authenticated_client.post("/api/v1/invoices", json=invoice_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "draft"
        assert data["total_amount"] == 216.00
        assert data["invoice_number"].startswith("INV-")

    async def test_get_invoices_pagination(self, authenticated_client: AsyncClient):
        """Test invoice list pagination."""
        # Create test invoices
        await create_test_invoices(count=25)
        
        response = await authenticated_client.get("/api/v1/invoices?limit=10&skip=0")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 25
        assert data["has_next"] is True
        assert data["has_prev"] is False

    async def test_unauthorized_access(self, client: AsyncClient):
        """Test API access without authentication."""
        response = await client.get("/api/v1/invoices")
        assert response.status_code == 401
```

### Frontend Testing

#### Component Tests
```tsx
// __tests__/components/InvoiceList.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import InvoiceList from '@/components/invoices/InvoiceList';
import { mockInvoices } from '@/test-utils/mocks';

// Mock hooks
jest.mock('@/hooks/useInvoices', () => ({
  useInvoices: jest.fn()
}));

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

describe('InvoiceList', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state', () => {
    (useInvoices as jest.Mock).mockReturnValue({
      invoices: [],
      loading: true,
      error: null,
    });

    renderWithProviders(<InvoiceList />);
    
    expect(screen.getByText('Loading invoices...')).toBeInTheDocument();
  });

  it('renders invoice list', async () => {
    (useInvoices as jest.Mock).mockReturnValue({
      invoices: mockInvoices,
      loading: false,
      error: null,
    });

    renderWithProviders(<InvoiceList />);
    
    await waitFor(() => {
      expect(screen.getByText('INV-000001')).toBeInTheDocument();
      expect(screen.getByText('$1,080.00')).toBeInTheDocument();
    });
  });

  it('handles invoice selection', async () => {
    const onInvoiceSelect = jest.fn();
    
    (useInvoices as jest.Mock).mockReturnValue({
      invoices: mockInvoices,
      loading: false,
      error: null,
    });

    renderWithProviders(<InvoiceList onInvoiceSelect={onInvoiceSelect} />);
    
    fireEvent.click(screen.getByText('INV-000001'));
    
    expect(onInvoiceSelect).toHaveBeenCalledWith(mockInvoices[0]);
  });

  it('renders error state', () => {
    (useInvoices as jest.Mock).mockReturnValue({
      invoices: [],
      loading: false,
      error: 'Failed to load invoices',
    });

    renderWithProviders(<InvoiceList />);
    
    expect(screen.getByText('Failed to load invoices')).toBeInTheDocument();
    expect(screen.getByText('Try Again')).toBeInTheDocument();
  });
});
```

#### Hook Tests
```tsx
// __tests__/hooks/useInvoices.test.ts
import { renderHook, act } from '@testing-library/react';
import { useInvoices } from '@/hooks/useInvoices';
import { invoiceApi } from '@/lib/api';

// Mock API
jest.mock('@/lib/api', () => ({
  invoiceApi: {
    getInvoices: jest.fn(),
    createInvoice: jest.fn(),
    updateInvoice: jest.fn(),
    deleteInvoice: jest.fn(),
  },
}));

// Mock auth context
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ token: 'mock-token' }),
}));

describe('useInvoices', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches invoices on mount', async () => {
    const mockResponse = {
      items: [{ id: 1, invoice_number: 'INV-001' }],
      total: 1,
    };

    (invoiceApi.getInvoices as jest.Mock).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useInvoices());

    expect(result.current.loading).toBe(true);

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.invoices).toEqual(mockResponse.items);
    expect(result.current.totalCount).toBe(1);
  });

  it('handles create invoice', async () => {
    const newInvoice = { id: 2, invoice_number: 'INV-002' };
    (invoiceApi.createInvoice as jest.Mock).mockResolvedValue(newInvoice);

    const { result } = renderHook(() => useInvoices());

    await act(async () => {
      const created = await result.current.createInvoice({
        customer_id: 1,
        items: [{ description: 'Test', quantity: 1, unit_price: 100 }],
      });
      
      expect(created).toEqual(newInvoice);
    });
  });
});
```

### E2E Testing

#### Playwright Configuration
```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],

  webServer: [
    {
      command: 'npm run dev',
      port: 3000,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'cd ../backend && uvicorn app.main:app --port 8000',
      port: 8000,
      reuseExistingServer: !process.env.CI,
    },
  ],
});
```

#### E2E Tests
```typescript
// e2e/invoice-workflow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Invoice Management Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'testpassword123');
    await page.click('[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('should create and send invoice', async ({ page }) => {
    // Navigate to invoices
    await page.click('text=Invoices');
    await page.waitForURL('/invoices');
    
    // Create new invoice
    await page.click('text=New Invoice');
    await page.waitForURL('/invoices/new');
    
    // Fill invoice form
    await page.selectOption('[name="customer_id"]', '1');
    await page.fill('[name="issue_date"]', '2024-01-15');
    await page.fill('[name="due_date"]', '2024-02-15');
    
    // Add invoice item
    await page.fill('[name="items.0.description"]', 'Web Development');
    await page.fill('[name="items.0.quantity"]', '10');
    await page.fill('[name="items.0.unit_price"]', '100');
    
    // Save invoice
    await page.click('text=Create Invoice');
    
    // Verify invoice created
    await expect(page.locator('text=Invoice created successfully')).toBeVisible();
    await expect(page.locator('text=INV-')).toBeVisible();
    
    // Send invoice
    await page.click('text=Send Invoice');
    await page.fill('[name="custom_message"]', 'Please find your invoice attached.');
    await page.click('text=Send');
    
    // Verify invoice sent
    await expect(page.locator('text=Invoice sent successfully')).toBeVisible();
    await expect(page.locator('text=Status: Sent')).toBeVisible();
  });

  test('should process payment', async ({ page }) => {
    // Navigate to sent invoice
    await page.goto('/invoices/1');
    
    // Click payment link
    await page.click('text=Pay Now');
    
    // Fill payment form (Stripe test)
    await page.fill('[name="cardNumber"]', '4242424242424242');
    await page.fill('[name="cardExpiry"]', '12/25');
    await page.fill('[name="cardCvc"]', '123');
    await page.fill('[name="billingName"]', 'John Doe');
    
    // Submit payment
    await page.click('text=Pay $1,080.00');
    
    // Verify payment success
    await expect(page.locator('text=Payment Successful')).toBeVisible();
    await expect(page.locator('text=Status: Paid')).toBeVisible();
  });
});
```

This comprehensive development guide provides all the necessary information for developers to work effectively on InvoiceFlow Pro, maintain code quality, and follow best practices throughout the development lifecycle.