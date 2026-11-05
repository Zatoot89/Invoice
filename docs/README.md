# InvoiceFlow Pro - Complete Documentation

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Getting Started](#getting-started)
4. [API Documentation](#api-documentation)
5. [Frontend Components](#frontend-components)
6. [Database Schema](#database-schema)
7. [Authentication & Security](#authentication--security)
8. [Features Documentation](#features-documentation)
9. [Deployment Guide](#deployment-guide)
10. [Development Guide](#development-guide)
11. [Testing](#testing)
12. [Contributing](#contributing)
13. [Troubleshooting](#troubleshooting)

## Project Overview

InvoiceFlow Pro is a comprehensive SaaS invoice generation and management platform designed for businesses of all sizes. It provides end-to-end invoice lifecycle management with advanced analytics, real-time notifications, payment processing, and automated workflows.

### Key Features

- **Professional Invoice Generation**: Multiple templates with PDF export
- **Customer Management**: Complete customer relationship management
- **Payment Processing**: Stripe integration with multiple payment methods
- **Real-time Notifications**: WebSocket-powered live updates
- **Advanced Analytics**: TimescaleDB-powered business intelligence
- **Email Automation**: Automated invoice delivery and reminders
- **Multi-currency Support**: Global business operations
- **Role-based Access Control**: Enterprise-grade security
- **API-first Architecture**: RESTful APIs for all operations
- **Responsive Design**: Mobile-optimized user interface

### Technology Stack

#### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 16 with TimescaleDB
- **Cache**: Redis 7.0+
- **Message Queue**: RabbitMQ with Celery
- **File Storage**: MinIO (S3-compatible)
- **Authentication**: JWT with OAuth 2.0 support
- **Validation**: Pydantic models
- **Logging**: Structlog with JSON formatting
- **Testing**: pytest with async support

#### Frontend
- **Framework**: Next.js 14 with TypeScript
- **UI Library**: NextUI components
- **Styling**: Tailwind CSS
- **State Management**: Zustand + SWR
- **Charts**: Recharts + Chart.js
- **Forms**: React Hook Form with Zod validation
- **Payments**: Stripe Elements
- **Real-time**: WebSocket hooks
- **Testing**: Jest + React Testing Library

#### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Nginx
- **SSL**: Let's Encrypt
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **CI/CD**: GitHub Actions

### Business Value

- **Increased Efficiency**: Automated invoice generation and delivery
- **Improved Cash Flow**: Faster payment processing and collection
- **Better Insights**: Advanced analytics and reporting
- **Enhanced Customer Experience**: Professional invoices and payment portals
- **Reduced Errors**: Automated calculations and validations
- **Scalability**: Cloud-native architecture for growth
- **Compliance**: SOX, PCI DSS, and GDPR compliance ready

## Architecture

### System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[Next.js App] --> B[NextUI Components]
        A --> C[Analytics Dashboard]
        A --> D[Invoice Management]
        A --> E[Customer Portal]
    end
    
    subgraph "API Gateway"
        F[FastAPI Server]
        G[Authentication Middleware]
        H[Rate Limiting]
        I[CORS Handler]
    end
    
    subgraph "Business Logic"
        J[Invoice Service]
        K[Payment Service]
        L[Analytics Service]
        M[Notification Service]
        N[PDF Service]
        O[Email Service]
    end
    
    subgraph "Data Layer"
        P[PostgreSQL + TimescaleDB]
        Q[Redis Cache]
        R[MinIO Object Storage]
    end
    
    subgraph "External Services"
        S[Stripe API]
        T[Email Provider]
        U[WebSocket Server]
    end
    
    subgraph "Background Jobs"
        V[Celery Workers]
        W[RabbitMQ]
        X[Scheduled Tasks]
    end
    
    A --> F
    F --> G
    G --> H
    H --> I
    I --> J
    I --> K
    I --> L
    I --> M
    J --> P
    K --> P
    L --> P
    M --> Q
    N --> R
    O --> T
    V --> W
    V --> X
    K --> S
    M --> U
```

### Database Architecture

#### Core Tables
- **users**: User accounts and authentication
- **customers**: Customer information and billing details
- **invoices**: Invoice headers with metadata
- **invoice_items**: Line items for each invoice
- **payments**: Payment records and transactions
- **audit_logs**: System audit trail (TimescaleDB hypertable)

#### Time-series Data (TimescaleDB)
- **analytics_events**: Business events for analytics
- **performance_metrics**: System performance data
- **user_activities**: User interaction tracking

### API Architecture

#### RESTful Endpoints
```
/api/v1/
├── auth/                 # Authentication endpoints
├── users/                # User management
├── customers/            # Customer operations
├── invoices/             # Invoice CRUD operations
├── payments/             # Payment processing
├── analytics/            # Business intelligence
├── pdf/                  # PDF generation
├── notifications/        # Real-time notifications
└── ws/                   # WebSocket connections
```

#### Authentication Flow
1. **Login**: Email/password or OAuth provider
2. **Token Generation**: JWT access and refresh tokens
3. **Token Validation**: Middleware validates on each request
4. **Role Authorization**: RBAC for endpoint access
5. **Session Management**: Redis-based session storage

### Real-time Architecture

#### WebSocket Flow
1. **Connection**: Authenticated WebSocket connection
2. **Subscription**: Subscribe to relevant event types
3. **Event Broadcasting**: Server broadcasts to subscribed clients
4. **Notification Delivery**: Real-time UI updates
5. **Connection Management**: Heartbeat and reconnection logic

## Getting Started

### Prerequisites

- Node.js 18+ and npm 8+
- Python 3.11+ and pip
- PostgreSQL 16+
- Redis 7.0+
- Docker and Docker Compose (recommended)

### Quick Start with Docker

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/invoiceflow-pro.git
   cd invoiceflow-pro
   ```

2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start Services**
   ```bash
   docker-compose up -d
   ```

4. **Initialize Database**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

5. **Access Application**
   - Frontend: http://localhost:3000
   - API Documentation: http://localhost:8000/api/v1/docs
   - Admin Panel: http://localhost:3000/admin

### Development Setup

#### Backend Setup

1. **Create Virtual Environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Database Setup**
   ```bash
   # Start PostgreSQL and Redis
   docker-compose up -d postgres redis
   
   # Run migrations
   alembic upgrade head
   
   # Seed initial data (optional)
   python scripts/seed_data.py
   ```

4. **Start Development Server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Frontend Setup

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Environment Configuration**
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your settings
   ```

3. **Start Development Server**
   ```bash
   npm run dev
   ```

### Environment Variables

#### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/invoiceflow_pro
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Stripe
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# File Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioaccess
MINIO_SECRET_KEY=miniosecret

# External APIs
FRONTEND_URL=http://localhost:3000
API_V1_STR=/api/v1
```

#### Frontend (.env.local)
```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Stripe
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...

# Authentication
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-nextauth-secret

# Feature Flags
NEXT_PUBLIC_ANALYTICS_ENABLED=true
NEXT_PUBLIC_REAL_TIME_ENABLED=true
```

## API Documentation

### Authentication Endpoints

#### POST /api/v1/auth/login
Login with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "user",
    "is_active": true
  }
}
```

#### POST /api/v1/auth/refresh
Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### POST /api/v1/auth/register
Register new user account.

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "password": "securepassword123",
  "full_name": "New User",
  "company_name": "Acme Corp"
}
```

### Customer Management

#### GET /api/v1/customers
Get paginated list of customers.

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Number of records to return (default: 20)
- `search` (string): Search term for name/email
- `sort` (string): Sort field (name, email, created_at)
- `order` (string): Sort order (asc, desc)

**Response:**
```json
{
  "customers": [
    {
      "id": 1,
      "name": "Customer Name",
      "email": "customer@example.com",
      "phone": "+1234567890",
      "company": "Customer Corp",
      "address": {
        "street": "123 Main St",
        "city": "New York",
        "state": "NY",
        "postal_code": "10001",
        "country": "US"
      },
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 50,
  "has_next": true,
  "has_prev": false
}
```

#### POST /api/v1/customers
Create new customer.

**Request Body:**
```json
{
  "name": "New Customer",
  "email": "new@example.com",
  "phone": "+1234567890",
  "company": "New Corp",
  "address": {
    "street": "456 Oak St",
    "city": "Los Angeles",
    "state": "CA",
    "postal_code": "90001",
    "country": "US"
  },
  "tax_id": "12-3456789",
  "payment_terms": 30,
  "currency": "USD",
  "notes": "VIP customer"
}
```

#### PUT /api/v1/customers/{customer_id}
Update existing customer.

#### DELETE /api/v1/customers/{customer_id}
Delete customer (soft delete).

### Invoice Management

#### GET /api/v1/invoices
Get paginated list of invoices.

**Query Parameters:**
- `skip`, `limit`: Pagination
- `status`: Filter by status (draft, sent, paid, overdue, cancelled)
- `customer_id`: Filter by customer
- `date_from`, `date_to`: Date range filter
- `search`: Search in invoice number or customer name

**Response:**
```json
{
  "invoices": [
    {
      "id": 1,
      "invoice_number": "INV-001",
      "customer_id": 1,
      "customer_name": "Customer Name",
      "status": "sent",
      "issue_date": "2024-01-15",
      "due_date": "2024-02-15",
      "subtotal": 1000.00,
      "tax_amount": 80.00,
      "total_amount": 1080.00,
      "currency": "USD",
      "items": [
        {
          "id": 1,
          "description": "Web Development Services",
          "quantity": 40,
          "unit_price": 25.00,
          "total": 1000.00
        }
      ],
      "created_at": "2024-01-15T10:30:00Z",
      "sent_at": "2024-01-15T11:00:00Z",
      "paid_at": null
    }
  ],
  "total": 25,
  "summary": {
    "total_amount": 25000.00,
    "paid_amount": 18000.00,
    "outstanding_amount": 7000.00
  }
}
```

#### POST /api/v1/invoices
Create new invoice.

**Request Body:**
```json
{
  "customer_id": 1,
  "issue_date": "2024-01-15",
  "due_date": "2024-02-15",
  "currency": "USD",
  "tax_rate": 8.0,
  "notes": "Thank you for your business!",
  "items": [
    {
      "description": "Consulting Services",
      "quantity": 10,
      "unit_price": 100.00
    },
    {
      "description": "Development Work",
      "quantity": 20,
      "unit_price": 75.00
    }
  ],
  "payment_terms": 30,
  "late_fee": 25.00
}
```

#### PUT /api/v1/invoices/{invoice_id}
Update invoice (only if status is draft).

#### POST /api/v1/invoices/{invoice_id}/send
Send invoice to customer via email.

#### POST /api/v1/invoices/{invoice_id}/mark-paid
Mark invoice as paid (manual payment recording).

**Request Body:**
```json
{
  "payment_date": "2024-01-20",
  "payment_method": "bank_transfer",
  "reference": "TXN123456",
  "notes": "Payment received via bank transfer"
}
```

#### GET /api/v1/invoices/{invoice_id}/pdf
Generate and download invoice PDF.

### Payment Processing

#### POST /api/v1/stripe/create-payment-intent
Create Stripe PaymentIntent for invoice.

**Request Body:**
```json
{
  "invoice_id": 1,
  "save_payment_method": false
}
```

**Response:**
```json
{
  "client_secret": "pi_1234567890_secret_abc123",
  "payment_intent_id": "pi_1234567890"
}
```

#### POST /api/v1/stripe/create-checkout-session
Create Stripe Checkout session.

**Request Body:**
```json
{
  "invoice_id": 1,
  "success_url": "https://yourdomain.com/payment/success",
  "cancel_url": "https://yourdomain.com/payment/cancel"
}
```

#### POST /api/v1/stripe/webhook
Stripe webhook handler for payment events.

**Headers:**
- `stripe-signature`: Stripe webhook signature

### Analytics Endpoints

#### GET /api/v1/analytics/dashboard
Get dashboard analytics overview.

**Query Parameters:**
- `date_range` (int): Number of days to analyze (default: 30)

**Response:**
```json
{
  "success": true,
  "data": {
    "period": {
      "start_date": "2024-01-01T00:00:00Z",
      "end_date": "2024-01-31T23:59:59Z",
      "days": 30
    },
    "kpis": {
      "total_revenue": 25000.00,
      "outstanding_amount": 5000.00,
      "average_invoice_value": 1250.00,
      "total_invoices": 20,
      "paid_invoices": 16,
      "overdue_invoices": 2,
      "payment_rate": 85.5,
      "average_payment_time": 18.5,
      "active_customers": 12,
      "new_customers": 3
    },
    "trends": {
      "revenue": {
        "value": 25000.00,
        "change": 15.3,
        "direction": "up"
      },
      "invoices": {
        "value": 20,
        "change": 8.2,
        "direction": "up"
      }
    },
    "status_breakdown": {
      "paid": 16,
      "sent": 2,
      "overdue": 2,
      "draft": 0
    }
  }
}
```

#### GET /api/v1/analytics/revenue
Get detailed revenue analytics.

**Query Parameters:**
- `period`: Time period (daily, weekly, monthly)
- `months`: Number of months for analysis (default: 12)

**Response:**
```json
{
  "success": true,
  "data": {
    "period": "monthly",
    "time_range": {
      "start_date": "2023-02-01T00:00:00Z",
      "end_date": "2024-01-31T23:59:59Z"
    },
    "time_series": [
      {
        "period": "2024-01-01T00:00:00Z",
        "revenue": 25000.00,
        "invoice_count": 20
      }
    ],
    "forecast": {
      "forecast_revenue": 28000.00,
      "confidence": 0.85
    },
    "growth_metrics": {
      "growth_rate": 15.3,
      "momentum": "accelerating"
    }
  }
}
```

### WebSocket Events

#### Connection
Connect to WebSocket with authentication token:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/ws?token=your_jwt_token');
```

#### Event Types
- `connection`: Welcome message after connection
- `heartbeat`: Periodic connection health check
- `invoice_created`: New invoice created
- `invoice_sent`: Invoice sent to customer  
- `payment_received`: Payment processed successfully
- `invoice_overdue`: Invoice became overdue
- `customer_created`: New customer added
- `system_update`: System notifications
- `user_activity`: User activity notifications

#### Example Event Message
```json
{
  "type": "payment_received",
  "title": "Payment Received",
  "message": "Payment of USD 1080.00 received for Invoice INV-001",
  "data": {
    "payment_id": 123,
    "invoice_id": 1,
    "invoice_number": "INV-001",
    "amount": 1080.00,
    "currency": "USD",
    "payment_method": "card"
  },
  "timestamp": "2024-01-20T15:30:00Z",
  "action_url": "/invoices/1",
  "priority": "info"
}
```

## Frontend Components

### Component Architecture

The frontend follows a modular component architecture with the following structure:

```
src/
├── components/           # Reusable UI components
│   ├── layout/          # Layout components
│   ├── forms/           # Form components
│   ├── analytics/       # Analytics components
│   ├── invoices/        # Invoice-specific components
│   ├── customers/       # Customer management components
│   ├── payments/        # Payment components
│   └── notifications/   # Notification components
├── pages/               # Next.js pages
├── hooks/               # Custom React hooks
├── contexts/            # React contexts
├── lib/                 # Utility functions
├── types/               # TypeScript type definitions
└── styles/              # Global styles
```

### Key Components

#### Layout Components

**Layout (`components/layout/Layout.tsx`)**
Main application layout with navigation and authentication.

```tsx
interface LayoutProps {
  children: React.ReactNode;
  title?: string;
  description?: string;
}

export default function Layout({ children, title, description }: LayoutProps)
```

**Navigation (`components/layout/Navigation.tsx`)**
Responsive navigation with role-based menu items.

**Sidebar (`components/layout/Sidebar.tsx`)**
Collapsible sidebar with navigation links.

#### Analytics Components

**AnalyticsDashboard (`components/analytics/AnalyticsDashboard.tsx`)**
Main analytics dashboard with multiple tabs and visualizations.

```tsx
interface AnalyticsDashboardProps {
  className?: string;
}

export default function AnalyticsDashboard({ className }: AnalyticsDashboardProps)
```

**RevenueChart (`components/analytics/RevenueChart.tsx`)**
Revenue visualization with multiple chart types.

```tsx
interface RevenueChartProps {
  data: any[];
  period: 'daily' | 'weekly' | 'monthly';
  chartType?: 'line' | 'area' | 'bar';
  showForecast?: boolean;
  className?: string;
}

export default function RevenueChart(props: RevenueChartProps)
```

**PerformanceMetrics (`components/analytics/PerformanceMetrics.tsx`)**
Performance metrics with KPIs, aging analysis, and efficiency scores.

**AdvancedMetrics (`components/analytics/AdvancedMetrics.tsx`)**
Advanced analytics with radar charts, trend analysis, and forecasting.

#### Invoice Components

**InvoiceList (`components/invoices/InvoiceList.tsx`)**
Paginated invoice list with filtering and sorting.

```tsx
interface InvoiceListProps {
  filters?: InvoiceFilters;
  onInvoiceSelect?: (invoice: Invoice) => void;
}

export default function InvoiceList(props: InvoiceListProps)
```

**InvoiceForm (`components/invoices/InvoiceForm.tsx`)**
Invoice creation and editing form with validation.

```tsx
interface InvoiceFormProps {
  invoice?: Invoice;
  onSubmit: (data: InvoiceFormData) => void;
  onCancel: () => void;
}

export default function InvoiceForm(props: InvoiceFormProps)
```

**InvoicePreview (`components/invoices/InvoicePreview.tsx`)**
Invoice preview with PDF generation and email sending.

#### Customer Components

**CustomerList (`components/customers/CustomerList.tsx`)**
Customer management with search and filtering.

**CustomerForm (`components/customers/CustomerForm.tsx`)**
Customer creation and editing form.

#### Payment Components

**StripePayment (`components/payments/StripePayment.tsx`)**
Stripe payment form with Elements integration.

```tsx
interface StripePaymentProps {
  invoice: {
    id: number;
    invoice_number: string;
    total: number;
    currency: string;
    customer_name: string;
  };
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (paymentResult: any) => void;
}

export default function StripePayment(props: StripePaymentProps)
```

### Custom Hooks

#### useAnalytics
Comprehensive analytics data management hook.

```tsx
interface AnalyticsOptions {
  dateRange?: number;
  period?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export function useAnalytics(options: AnalyticsOptions = {}) {
  return {
    dashboardData,
    revenueData,
    customerData,
    performanceData,
    loading,
    error,
    refreshData,
    exportData,
    getRealTimeMetrics,
    createAlert,
  };
}
```

#### useWebSocket
WebSocket connection management with auto-reconnection.

```tsx
export interface WebSocketHookOptions {
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  enableNotifications?: boolean;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

export default function useWebSocket(options: WebSocketHookOptions = {})
```

#### useInvoices
Invoice management with CRUD operations.

```tsx
export function useInvoices(options: InvoiceHookOptions = {}) {
  return {
    invoices,
    loading,
    error,
    createInvoice,
    updateInvoice,
    deleteInvoice,
    sendInvoice,
    markAsPaid,
    generatePDF,
    refreshInvoices,
  };
}
```

### State Management

#### Zustand Stores

**AuthStore (`stores/authStore.ts`)**
Authentication state management.

```tsx
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({ ... }));
```

**UIStore (`stores/uiStore.ts`)**
UI state management (modals, sidebars, themes).

```tsx
interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  modals: Record<string, boolean>;
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
  openModal: (modalId: string) => void;
  closeModal: (modalId: string) => void;
}

export const useUIStore = create<UIState>((set) => ({ ... }));
```

### Form Validation

Forms use React Hook Form with Zod validation schemas:

```tsx
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

const invoiceSchema = z.object({
  customer_id: z.number().min(1, 'Customer is required'),
  issue_date: z.string().min(1, 'Issue date is required'),
  due_date: z.string().min(1, 'Due date is required'),
  currency: z.string().min(3).max(3),
  items: z.array(z.object({
    description: z.string().min(1, 'Description is required'),
    quantity: z.number().min(0.01, 'Quantity must be greater than 0'),
    unit_price: z.number().min(0.01, 'Unit price must be greater than 0'),
  })).min(1, 'At least one item is required'),
});

type InvoiceFormData = z.infer<typeof invoiceSchema>;

export default function InvoiceForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<InvoiceFormData>({
    resolver: zodResolver(invoiceSchema),
  });

  // Form implementation...
}
```

## Database Schema

### Entity Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ CUSTOMERS : creates
    USERS ||--o{ INVOICES : creates
    CUSTOMERS ||--o{ INVOICES : "billed to"
    INVOICES ||--o{ INVOICE_ITEMS : contains
    INVOICES ||--o{ PAYMENTS : "paid by"
    USERS ||--o{ AUDIT_LOGS : performs
    
    USERS {
        int id PK
        string email UK
        string password_hash
        string full_name
        string company_name
        string role
        boolean is_active
        datetime created_at
        datetime updated_at
        json settings
    }
    
    CUSTOMERS {
        int id PK
        int user_id FK
        string name
        string email
        string phone
        string company
        json address
        string tax_id
        int payment_terms
        string currency
        text notes
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    INVOICES {
        int id PK
        int user_id FK
        int customer_id FK
        string invoice_number UK
        enum status
        date issue_date
        date due_date
        decimal subtotal
        decimal tax_rate
        decimal tax_amount
        decimal total_amount
        string currency
        text notes
        int payment_terms
        decimal late_fee
        datetime sent_at
        datetime paid_at
        datetime created_at
        datetime updated_at
        json metadata
    }
    
    INVOICE_ITEMS {
        int id PK
        int invoice_id FK
        string description
        decimal quantity
        decimal unit_price
        decimal total
        json metadata
        int sort_order
    }
    
    PAYMENTS {
        int id PK
        int invoice_id FK
        decimal amount
        string currency
        string payment_method
        string status
        string provider_payment_id
        string provider_customer_id
        date payment_date
        text reference
        text notes
        datetime created_at
        json metadata
    }
    
    AUDIT_LOGS {
        bigint id PK
        int user_id FK
        string action
        string resource_type
        int resource_id
        json old_values
        json new_values
        string ip_address
        string user_agent
        timestamp timestamp
    }
```

### Table Definitions

#### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    company_name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT true,
    email_verified BOOLEAN NOT NULL DEFAULT false,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);
```

#### Customers Table
```sql
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    company VARCHAR(255),
    address JSONB DEFAULT '{}',
    tax_id VARCHAR(100),
    payment_terms INTEGER DEFAULT 30,
    currency VARCHAR(3) DEFAULT 'USD',
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_customers_user_id ON customers(user_id);
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_active ON customers(is_active);
CREATE INDEX idx_customers_name ON customers(name);
```

#### Invoices Table
```sql
CREATE TYPE invoice_status AS ENUM ('draft', 'sent', 'paid', 'overdue', 'cancelled');

CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    invoice_number VARCHAR(100) NOT NULL,
    status invoice_status NOT NULL DEFAULT 'draft',
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    tax_rate DECIMAL(5,4) DEFAULT 0.0000,
    tax_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    total_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    notes TEXT,
    payment_terms INTEGER DEFAULT 30,
    late_fee DECIMAL(10,2) DEFAULT 0.00,
    sent_at TIMESTAMP WITH TIME ZONE,
    paid_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE UNIQUE INDEX idx_invoices_user_number ON invoices(user_id, invoice_number);
CREATE INDEX idx_invoices_customer_id ON invoices(customer_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_dates ON invoices(issue_date, due_date);
CREATE INDEX idx_invoices_total ON invoices(total_amount);
```

#### Invoice Items Table
```sql
CREATE TABLE invoice_items (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    quantity DECIMAL(10,4) NOT NULL DEFAULT 1.0000,
    unit_price DECIMAL(12,2) NOT NULL,
    total DECIMAL(12,2) NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_invoice_items_invoice_id ON invoice_items(invoice_id);
CREATE INDEX idx_invoice_items_sort_order ON invoice_items(invoice_id, sort_order);
```

#### Payments Table
```sql
CREATE TYPE payment_status AS ENUM ('pending', 'completed', 'failed', 'refunded');
CREATE TYPE payment_method AS ENUM ('card', 'bank_transfer', 'check', 'cash', 'other');

CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE RESTRICT,
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    payment_method payment_method NOT NULL,
    status payment_status NOT NULL DEFAULT 'pending',
    provider_payment_id VARCHAR(255),
    provider_customer_id VARCHAR(255),
    payment_date DATE NOT NULL,
    reference VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_payments_invoice_id ON payments(invoice_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_payment_date ON payments(payment_date);
CREATE INDEX idx_payments_provider_id ON payments(provider_payment_id);
```

### TimescaleDB Hypertables

#### Audit Logs (Time-series)
```sql
CREATE TABLE audit_logs (
    id BIGSERIAL,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable('audit_logs', 'timestamp');

-- Create indexes
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id, timestamp DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action, timestamp DESC);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id, timestamp DESC);
```

#### Analytics Events (Time-series)
```sql
CREATE TABLE analytics_events (
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    user_id INTEGER REFERENCES users(id),
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}',
    session_id VARCHAR(255),
    ip_address INET
);

-- Convert to hypertable
SELECT create_hypertable('analytics_events', 'timestamp');

-- Create indexes
CREATE INDEX idx_analytics_events_user_id ON analytics_events(user_id, timestamp DESC);
CREATE INDEX idx_analytics_events_type ON analytics_events(event_type, timestamp DESC);
CREATE INDEX idx_analytics_events_session ON analytics_events(session_id, timestamp DESC);
```

### Database Functions and Triggers

#### Update Timestamp Trigger
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_invoices_updated_at BEFORE UPDATE ON invoices 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

#### Invoice Number Generation
```sql
CREATE OR REPLACE FUNCTION generate_invoice_number(user_id_param INTEGER)
RETURNS VARCHAR(100) AS $$
DECLARE
    next_number INTEGER;
    formatted_number VARCHAR(100);
BEGIN
    -- Get next number for this user
    SELECT COALESCE(MAX(CAST(SUBSTRING(invoice_number FROM 'INV-(\d+)') AS INTEGER)), 0) + 1
    INTO next_number
    FROM invoices
    WHERE user_id = user_id_param
    AND invoice_number ~ '^INV-\d+$';
    
    -- Format with padding
    formatted_number := 'INV-' || LPAD(next_number::TEXT, 6, '0');
    
    RETURN formatted_number;
END;
$$ LANGUAGE plpgsql;
```

#### Invoice Total Calculation
```sql
CREATE OR REPLACE FUNCTION calculate_invoice_totals()
RETURNS TRIGGER AS $$
DECLARE
    invoice_subtotal DECIMAL(12,2);
    invoice_tax DECIMAL(12,2);
    invoice_total DECIMAL(12,2);
BEGIN
    -- Calculate subtotal from items
    SELECT COALESCE(SUM(total), 0.00)
    INTO invoice_subtotal
    FROM invoice_items
    WHERE invoice_id = NEW.invoice_id;
    
    -- Get tax rate from invoice
    SELECT tax_rate INTO invoice_tax
    FROM invoices
    WHERE id = NEW.invoice_id;
    
    -- Calculate total
    invoice_total := invoice_subtotal + (invoice_subtotal * invoice_tax / 100);
    
    -- Update invoice totals
    UPDATE invoices
    SET subtotal = invoice_subtotal,
        tax_amount = (invoice_subtotal * invoice_tax / 100),
        total_amount = invoice_total,
        updated_at = NOW()
    WHERE id = NEW.invoice_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_totals_after_item_change
    AFTER INSERT OR UPDATE OR DELETE ON invoice_items
    FOR EACH ROW EXECUTE FUNCTION calculate_invoice_totals();
```

### Data Migration Strategy

#### Alembic Migration Files
```python
# migrations/versions/001_initial_schema.py
"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create enum types
    op.execute("CREATE TYPE invoice_status AS ENUM ('draft', 'sent', 'paid', 'overdue', 'cancelled')")
    op.execute("CREATE TYPE payment_status AS ENUM ('pending', 'completed', 'failed', 'refunded')")
    op.execute("CREATE TYPE payment_method AS ENUM ('card', 'bank_transfer', 'check', 'cash', 'other')")
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False, default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('email_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('settings', postgresql.JSONB(), nullable=True, default='{}'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Continue with other tables...
    # (Additional table definitions...)

def downgrade():
    op.drop_table('payments')
    op.drop_table('invoice_items')
    op.drop_table('invoices')
    op.drop_table('customers')
    op.drop_table('users')
    op.execute("DROP TYPE IF EXISTS payment_method")
    op.execute("DROP TYPE IF EXISTS payment_status")
    op.execute("DROP TYPE IF EXISTS invoice_status")
```

## Authentication & Security

### Authentication Architecture

InvoiceFlow Pro implements a comprehensive authentication and authorization system using JWT tokens with the following components:

#### JWT Token Structure
```python
# Access Token (Short-lived: 30 minutes)
{
    "sub": "user_id",
    "email": "user@example.com", 
    "role": "user",
    "company_id": 1,
    "permissions": ["read:invoices", "write:invoices"],
    "iat": 1704067200,
    "exp": 1704069000,
    "type": "access"
}

# Refresh Token (Long-lived: 7 days)
{
    "sub": "user_id",
    "iat": 1704067200,
    "exp": 1704672000,
    "type": "refresh"
}
```

#### Token Management
```python
# app/core/security.py
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        "iat": datetime.utcnow()
    }
    
    if additional_claims:
        to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None
```

### Role-Based Access Control (RBAC)

#### Role Definitions
```python
class UserRole(str, Enum):
    ADMIN = "admin"          # Full system access
    MANAGER = "manager"      # Company-wide access
    USER = "user"           # Personal account access
    ACCOUNTANT = "accountant" # Financial data access
    VIEWER = "viewer"       # Read-only access

class Permission(str, Enum):
    # Invoice permissions
    READ_INVOICES = "read:invoices"
    WRITE_INVOICES = "write:invoices"
    DELETE_INVOICES = "delete:invoices"
    SEND_INVOICES = "send:invoices"
    
    # Customer permissions
    READ_CUSTOMERS = "read:customers"
    WRITE_CUSTOMERS = "write:customers"
    DELETE_CUSTOMERS = "delete:customers"
    
    # Payment permissions
    READ_PAYMENTS = "read:payments"
    PROCESS_PAYMENTS = "process:payments"
    REFUND_PAYMENTS = "refund:payments"
    
    # Analytics permissions
    READ_ANALYTICS = "read:analytics"
    EXPORT_ANALYTICS = "export:analytics"
    
    # System permissions
    MANAGE_USERS = "manage:users"
    SYSTEM_CONFIG = "system:config"

# Role-Permission mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [permission for permission in Permission],
    UserRole.MANAGER: [
        Permission.READ_INVOICES,
        Permission.WRITE_INVOICES,
        Permission.SEND_INVOICES,
        Permission.READ_CUSTOMERS,
        Permission.WRITE_CUSTOMERS,
        Permission.READ_PAYMENTS,
        Permission.PROCESS_PAYMENTS,
        Permission.READ_ANALYTICS,
        Permission.EXPORT_ANALYTICS,
    ],
    UserRole.USER: [
        Permission.READ_INVOICES,
        Permission.WRITE_INVOICES,
        Permission.SEND_INVOICES,
        Permission.READ_CUSTOMERS,
        Permission.WRITE_CUSTOMERS,
        Permission.READ_PAYMENTS,
        Permission.PROCESS_PAYMENTS,
        Permission.READ_ANALYTICS,
    ],
    UserRole.ACCOUNTANT: [
        Permission.READ_INVOICES,
        Permission.READ_CUSTOMERS,
        Permission.READ_PAYMENTS,
        Permission.PROCESS_PAYMENTS,
        Permission.READ_ANALYTICS,
        Permission.EXPORT_ANALYTICS,
    ],
    UserRole.VIEWER: [
        Permission.READ_INVOICES,
        Permission.READ_CUSTOMERS,
        Permission.READ_PAYMENTS,
        Permission.READ_ANALYTICS,
    ],
}
```

#### Permission Decorators
```python
from functools import wraps
from fastapi import HTTPException, status

def require_permission(permission: Permission):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current user from dependency injection
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_permissions = ROLE_PERMISSIONS.get(current_user.role, [])
            
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission {permission} required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage in API endpoints
@router.delete("/invoices/{invoice_id}")
@require_permission(Permission.DELETE_INVOICES)
async def delete_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user)
):
    # Delete invoice logic
    pass
```

### Security Middleware

#### Authentication Middleware
```python
# app/core/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import verify_token
from app.core.database import get_db
from app.models.user import User

security = HTTPBearer()

async def get_current_user(
    token: str = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token.credentials)
    
    if payload is None:
        raise credentials_exception
    
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user

async def get_current_active_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
```

#### Rate Limiting
```python
# app/middleware/rate_limiting.py
import time
from typing import Dict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import redis

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_client: redis.Redis):
        super().__init__(app)
        self.redis = redis_client
        self.limits = {
            "/api/v1/auth/login": {"requests": 5, "window": 300},  # 5 per 5 minutes
            "/api/v1/invoices": {"requests": 100, "window": 3600},  # 100 per hour
            "default": {"requests": 1000, "window": 3600},  # 1000 per hour default
        }
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        path = request.url.path
        method = request.method
        
        # Skip rate limiting for certain paths
        if path.startswith("/health") or path.startswith("/docs"):
            return await call_next(request)
        
        # Get rate limit for this endpoint
        limit_config = self.limits.get(path, self.limits["default"])
        
        # Create Redis key
        key = f"rate_limit:{client_ip}:{path}:{method}"
        
        try:
            # Get current request count
            current = self.redis.get(key)
            
            if current is None:
                # First request in window
                self.redis.setex(key, limit_config["window"], 1)
            else:
                current_count = int(current)
                
                if current_count >= limit_config["requests"]:
                    raise HTTPException(
                        status_code=429,
                        detail="Rate limit exceeded",
                        headers={
                            "X-RateLimit-Limit": str(limit_config["requests"]),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(time.time() + limit_config["window"])
                        }
                    )
                
                # Increment counter
                self.redis.incr(key)
            
            response = await call_next(request)
            
            # Add rate limit headers
            remaining = max(0, limit_config["requests"] - (int(current) if current else 1))
            response.headers["X-RateLimit-Limit"] = str(limit_config["requests"])
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            
            return response
            
        except redis.RedisError:
            # If Redis is down, allow request through
            return await call_next(request)
```

### Input Validation and Sanitization

#### Pydantic Models with Validation
```python
# app/schemas/invoice.py
from pydantic import BaseModel, validator, Field
from typing import List, Optional
from decimal import Decimal
from datetime import date
import re

class InvoiceItemCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=1000)
    quantity: Decimal = Field(..., gt=0, le=999999.9999)
    unit_price: Decimal = Field(..., ge=0, le=999999.99)
    
    @validator('description')
    def validate_description(cls, v):
        # Remove potentially harmful characters
        v = re.sub(r'[<>\"\'&]', '', v)
        return v.strip()
    
    @validator('quantity', 'unit_price')
    def validate_decimal_places(cls, v):
        # Ensure proper decimal precision
        if v is not None:
            return round(Decimal(str(v)), 4)
        return v

class InvoiceCreate(BaseModel):
    customer_id: int = Field(..., gt=0)
    issue_date: date
    due_date: date
    currency: str = Field(..., min_length=3, max_length=3, regex=r'^[A-Z]{3}$')
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    notes: Optional[str] = Field(None, max_length=2000)
    items: List[InvoiceItemCreate] = Field(..., min_items=1, max_items=100)
    
    @validator('due_date')
    def validate_due_date(cls, v, values):
        if 'issue_date' in values and v < values['issue_date']:
            raise ValueError('Due date must be after issue date')
        return v
    
    @validator('currency')
    def validate_currency(cls, v):
        allowed_currencies = ['USD', 'EUR', 'GBP', 'CAD', 'AUD']
        if v.upper() not in allowed_currencies:
            raise ValueError(f'Currency must be one of: {allowed_currencies}')
        return v.upper()
    
    @validator('notes')
    def sanitize_notes(cls, v):
        if v:
            # Basic HTML sanitization
            v = re.sub(r'<[^>]+>', '', v)
            return v.strip()
        return v

class InvoiceUpdate(BaseModel):
    customer_id: Optional[int] = Field(None, gt=0)
    issue_date: Optional[date]
    due_date: Optional[date]
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    notes: Optional[str] = Field(None, max_length=2000)
    items: Optional[List[InvoiceItemCreate]] = Field(None, max_items=100)
    
    # Apply same validators as InvoiceCreate
    _validate_due_date = validator('due_date', allow_reuse=True)(InvoiceCreate.validate_due_date)
    _validate_currency = validator('currency', allow_reuse=True)(InvoiceCreate.validate_currency)
    _sanitize_notes = validator('notes', allow_reuse=True)(InvoiceCreate.sanitize_notes)
```

### CORS Configuration
```python
# app/core/config.py
from typing import List, Union
from pydantic import AnyHttpUrl, BaseSettings, validator

class Settings(BaseSettings):
    # CORS settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With"
    ],
    expose_headers=["X-Total-Count", "X-Process-Time"]
)
```

### Security Headers Middleware
```python
# app/middleware/security.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS (only in production with HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # CSP (Content Security Policy)
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://js.stripe.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.stripe.com; "
            "frame-src https://js.stripe.com; "
            "object-src 'none'; "
            "base-uri 'self'"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        
        return response
```

### Password Policy
```python
# app/core/security.py
import re
from typing import List

class PasswordValidator:
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, List[str]]:
        errors = []
        
        if len(password) < PasswordValidator.MIN_LENGTH:
            errors.append(f"Password must be at least {PasswordValidator.MIN_LENGTH} characters long")
        
        if len(password) > PasswordValidator.MAX_LENGTH:
            errors.append(f"Password must not exceed {PasswordValidator.MAX_LENGTH} characters")
        
        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("Password must contain at least one special character")
        
        # Check for common weak passwords
        common_passwords = ['password', '123456', 'qwerty', 'admin']
        if password.lower() in common_passwords:
            errors.append("Password is too common")
        
        return len(errors) == 0, errors

# Usage in user registration
@router.post("/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    is_valid, errors = PasswordValidator.validate_password(user_data.password)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password validation failed", "errors": errors}
        )
    
    # Continue with registration...
```

### SQL Injection Prevention
All database queries use SQLAlchemy's parameterized queries or raw SQL with parameters:

```python
# Safe parameterized query
def get_invoices_by_user(db: Session, user_id: int, status: Optional[str] = None):
    query = db.query(Invoice).filter(Invoice.user_id == user_id)
    
    if status:
        query = query.filter(Invoice.status == status)
    
    return query.all()

# Safe raw SQL with parameters
def get_revenue_analytics(db: Session, user_id: int, start_date: date, end_date: date):
    query = text("""
        SELECT DATE(paid_at) as payment_date, SUM(total_amount) as revenue
        FROM invoices 
        WHERE user_id = :user_id 
        AND status = 'paid'
        AND paid_at BETWEEN :start_date AND :end_date
        GROUP BY DATE(paid_at)
        ORDER BY payment_date
    """)
    
    result = db.execute(query, {
        "user_id": user_id,
        "start_date": start_date,
        "end_date": end_date
    })
    
    return result.fetchall()
```

### Audit Logging
```python
# app/services/audit_service.py
from app.models.audit import AuditLog
from app.core.database import get_db
from fastapi import Request
import json

class AuditService:
    @staticmethod
    async def log_action(
        db: Session,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(audit_log)
        await db.commit()
        
        return audit_log

# Usage in API endpoints
@router.put("/invoices/{invoice_id}")
async def update_invoice(
    invoice_id: int,
    invoice_data: InvoiceUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get existing invoice
    existing_invoice = db.query(Invoice).filter_by(id=invoice_id, user_id=current_user.id).first()
    
    if not existing_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Store old values for audit
    old_values = {
        "customer_id": existing_invoice.customer_id,
        "total_amount": float(existing_invoice.total_amount),
        "status": existing_invoice.status
    }
    
    # Update invoice
    for field, value in invoice_data.dict(exclude_unset=True).items():
        setattr(existing_invoice, field, value)
    
    db.commit()
    
    # Store new values for audit
    new_values = {
        "customer_id": existing_invoice.customer_id,
        "total_amount": float(existing_invoice.total_amount),
        "status": existing_invoice.status
    }
    
    # Log the action
    await AuditService.log_action(
        db=db,
        user_id=current_user.id,
        action="update",
        resource_type="invoice",
        resource_id=invoice_id,
        old_values=old_values,
        new_values=new_values,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return existing_invoice
```

This comprehensive security implementation ensures that InvoiceFlow Pro meets enterprise security standards with proper authentication, authorization, input validation, and audit logging.