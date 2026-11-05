# InvoiceFlow Pro - API Documentation

## Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Error Handling](#error-handling)
4. [Rate Limiting](#rate-limiting)
5. [Pagination](#pagination)
6. [Authentication Endpoints](#authentication-endpoints)
7. [User Management](#user-management)
8. [Customer Management](#customer-management)
9. [Invoice Management](#invoice-management)
10. [Payment Processing](#payment-processing)
11. [Analytics Endpoints](#analytics-endpoints)
12. [WebSocket API](#websocket-api)
13. [File Upload/Download](#file-uploaddownload)
14. [Webhook Management](#webhook-management)
15. [API Examples](#api-examples)

## API Overview

The InvoiceFlow Pro API is a RESTful API built with FastAPI that provides comprehensive invoice and payment management capabilities.

### Base URL
```
Production: https://api.invoiceflow.com/api/v1
Staging: https://staging-api.invoiceflow.com/api/v1
Development: http://localhost:8000/api/v1
```

### Content Type
All requests should include:
```
Content-Type: application/json
```

### API Versioning
The API uses URL versioning (`/api/v1/`). All endpoints are prefixed with the version number.

### OpenAPI Documentation
Interactive API documentation is available at:
- Swagger UI: `/api/v1/docs`
- ReDoc: `/api/v1/redoc`
- OpenAPI JSON: `/api/v1/openapi.json`

## Authentication

InvoiceFlow Pro uses JWT (JSON Web Token) authentication with access and refresh tokens.

### Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Database
    
    Client->>API: POST /auth/login (credentials)
    API->>Database: Validate credentials
    Database-->>API: User validated
    API-->>Client: Access + Refresh tokens
    
    Client->>API: API request with Authorization header
    API->>API: Validate access token
    API-->>Client: API response
    
    Client->>API: POST /auth/refresh (refresh token)
    API-->>Client: New access token
```

### Token Types

#### Access Token
- **Purpose**: Used for API requests
- **Lifetime**: 30 minutes (configurable)
- **Usage**: Include in Authorization header

#### Refresh Token
- **Purpose**: Used to obtain new access tokens
- **Lifetime**: 7 days (configurable)
- **Usage**: Send to `/auth/refresh` endpoint

### Authorization Header
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Error Handling

### Standard Error Response Format

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional error details",
    "code": "SPECIFIC_ERROR_CODE"
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "path": "/api/v1/invoices"
}
```

### HTTP Status Codes

| Status Code | Description | Use Case |
|-------------|-------------|----------|
| 200 | OK | Successful GET, PUT |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Error Codes

#### Authentication Errors
- `AUTH_REQUIRED`: Authentication required
- `TOKEN_EXPIRED`: Access token expired
- `TOKEN_INVALID`: Invalid token format
- `CREDENTIALS_INVALID`: Invalid login credentials
- `ACCOUNT_INACTIVE`: User account is inactive

#### Validation Errors
- `VALIDATION_ERROR`: Request validation failed
- `REQUIRED_FIELD`: Required field missing
- `INVALID_FORMAT`: Invalid field format
- `VALUE_OUT_OF_RANGE`: Value outside allowed range

#### Business Logic Errors
- `INVOICE_NOT_EDITABLE`: Invoice cannot be modified
- `INSUFFICIENT_PERMISSIONS`: User lacks required permissions
- `RESOURCE_NOT_FOUND`: Requested resource not found
- `DUPLICATE_RESOURCE`: Resource already exists

## Rate Limiting

API endpoints are rate-limited to prevent abuse and ensure fair usage.

### Rate Limits

| Endpoint Category | Limit | Window |
|------------------|-------|---------|
| Authentication | 5 requests | 5 minutes |
| General API | 1000 requests | 1 hour |
| File Upload | 100 requests | 1 hour |
| Payment Processing | 100 requests | 1 hour |

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1609459200
X-RateLimit-Window: 3600
```

### Rate Limit Exceeded Response

```json
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded. Try again later.",
  "details": {
    "limit": 1000,
    "window": 3600,
    "reset_time": "2024-01-15T11:00:00Z"
  }
}
```

## Pagination

List endpoints support pagination with consistent parameters.

### Pagination Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | integer | 0 | Number of records to skip |
| `limit` | integer | 20 | Maximum records per page (max: 100) |
| `sort` | string | "created_at" | Sort field |
| `order` | string | "desc" | Sort order (asc/desc) |

### Pagination Response

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "pages": 8,
  "per_page": 20,
  "has_next": true,
  "has_prev": false,
  "next_page": 2,
  "prev_page": null
}
```

## Authentication Endpoints

### POST /auth/login
Authenticate user with email and password.

#### Request Body
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

#### Success Response (200)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "company_name": "Acme Corp",
    "role": "user",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

#### Error Response (401)
```json
{
  "error": "CREDENTIALS_INVALID",
  "message": "Invalid email or password"
}
```

### POST /auth/refresh
Refresh access token using refresh token.

#### Request Body
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### Success Response (200)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### POST /auth/register
Register new user account.

#### Request Body
```json
{
  "email": "newuser@example.com",
  "password": "securepassword123",
  "full_name": "New User",
  "company_name": "New Company"
}
```

#### Success Response (201)
```json
{
  "user": {
    "id": 2,
    "email": "newuser@example.com",
    "full_name": "New User",
    "company_name": "New Company",
    "role": "user",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### POST /auth/logout
Logout and invalidate refresh token.

#### Request Headers
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

#### Success Response (204)
No content

### POST /auth/forgot-password
Request password reset email.

#### Request Body
```json
{
  "email": "user@example.com"
}
```

#### Success Response (200)
```json
{
  "message": "Password reset email sent"
}
```

### POST /auth/reset-password
Reset password with token from email.

#### Request Body
```json
{
  "token": "password_reset_token",
  "new_password": "newsecurepassword123"
}
```

#### Success Response (200)
```json
{
  "message": "Password reset successful"
}
```

## User Management

### GET /users/me
Get current user profile.

#### Request Headers
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

#### Success Response (200)
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "company_name": "Acme Corp",
  "role": "user",
  "is_active": true,
  "email_verified": true,
  "settings": {
    "timezone": "America/New_York",
    "currency": "USD",
    "date_format": "MM/DD/YYYY"
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### PUT /users/me
Update current user profile.

#### Request Body
```json
{
  "full_name": "John Smith",
  "company_name": "Smith Corp",
  "settings": {
    "timezone": "America/Los_Angeles",
    "currency": "USD",
    "date_format": "DD/MM/YYYY"
  }
}
```

#### Success Response (200)
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Smith",
  "company_name": "Smith Corp",
  "role": "user",
  "is_active": true,
  "settings": {
    "timezone": "America/Los_Angeles",
    "currency": "USD",
    "date_format": "DD/MM/YYYY"
  },
  "updated_at": "2024-01-15T11:00:00Z"
}
```

### POST /users/change-password
Change user password.

#### Request Body
```json
{
  "current_password": "currentpassword123",
  "new_password": "newpassword123"
}
```

#### Success Response (200)
```json
{
  "message": "Password changed successfully"
}
```

## Customer Management

### GET /customers
Get paginated list of customers.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `skip` | integer | No | Records to skip (default: 0) |
| `limit` | integer | No | Records per page (default: 20, max: 100) |
| `search` | string | No | Search in name/email |
| `is_active` | boolean | No | Filter by active status |
| `sort` | string | No | Sort field (name, email, created_at) |
| `order` | string | No | Sort order (asc, desc) |

#### Success Response (200)
```json
{
  "items": [
    {
      "id": 1,
      "name": "John Customer",
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
      "tax_id": "12-3456789",
      "payment_terms": 30,
      "currency": "USD",
      "is_active": true,
      "total_invoiced": 5000.00,
      "total_paid": 4500.00,
      "outstanding_balance": 500.00,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "pages": 3,
  "per_page": 20,
  "has_next": true,
  "has_prev": false
}
```

### POST /customers
Create new customer.

#### Request Body
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
  "tax_id": "98-7654321",
  "payment_terms": 30,
  "currency": "USD",
  "notes": "VIP customer"
}
```

#### Success Response (201)
```json
{
  "id": 2,
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
  "tax_id": "98-7654321",
  "payment_terms": 30,
  "currency": "USD",
  "notes": "VIP customer",
  "is_active": true,
  "total_invoiced": 0.00,
  "total_paid": 0.00,
  "outstanding_balance": 0.00,
  "created_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

### GET /customers/{customer_id}
Get specific customer details.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | integer | Yes | Customer ID |

#### Success Response (200)
```json
{
  "id": 1,
  "name": "John Customer",
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
  "tax_id": "12-3456789",
  "payment_terms": 30,
  "currency": "USD",
  "notes": "Important client",
  "is_active": true,
  "total_invoiced": 5000.00,
  "total_paid": 4500.00,
  "outstanding_balance": 500.00,
  "recent_invoices": [
    {
      "id": 1,
      "invoice_number": "INV-000001",
      "total_amount": 1000.00,
      "status": "paid",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "payment_history": [
    {
      "id": 1,
      "amount": 1000.00,
      "payment_date": "2024-01-20",
      "payment_method": "card"
    }
  ],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### PUT /customers/{customer_id}
Update existing customer.

#### Request Body
```json
{
  "name": "Updated Customer Name",
  "email": "updated@example.com",
  "phone": "+1234567891",
  "company": "Updated Corp",
  "address": {
    "street": "789 Pine St",
    "city": "Chicago",
    "state": "IL",
    "postal_code": "60601",
    "country": "US"
  },
  "payment_terms": 45,
  "notes": "Updated notes"
}
```

#### Success Response (200)
```json
{
  "id": 1,
  "name": "Updated Customer Name",
  "email": "updated@example.com",
  "phone": "+1234567891",
  "company": "Updated Corp",
  "address": {
    "street": "789 Pine St",
    "city": "Chicago",
    "state": "IL",
    "postal_code": "60601",
    "country": "US"
  },
  "tax_id": "12-3456789",
  "payment_terms": 45,
  "currency": "USD",
  "notes": "Updated notes",
  "is_active": true,
  "total_invoiced": 5000.00,
  "total_paid": 4500.00,
  "outstanding_balance": 500.00,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T12:00:00Z"
}
```

### DELETE /customers/{customer_id}
Delete customer (soft delete).

#### Success Response (204)
No content

## Invoice Management

### GET /invoices
Get paginated list of invoices.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `skip` | integer | No | Records to skip |
| `limit` | integer | No | Records per page |
| `status` | string | No | Filter by status |
| `customer_id` | integer | No | Filter by customer |
| `date_from` | date | No | Start date filter (YYYY-MM-DD) |
| `date_to` | date | No | End date filter (YYYY-MM-DD) |
| `search` | string | No | Search in invoice number/customer |
| `sort` | string | No | Sort field |
| `order` | string | No | Sort order |

#### Success Response (200)
```json
{
  "items": [
    {
      "id": 1,
      "invoice_number": "INV-000001",
      "customer_id": 1,
      "customer_name": "John Customer",
      "status": "sent",
      "issue_date": "2024-01-15",
      "due_date": "2024-02-15",
      "subtotal": 1000.00,
      "tax_rate": 8.00,
      "tax_amount": 80.00,
      "total_amount": 1080.00,
      "currency": "USD",
      "notes": "Thank you for your business!",
      "payment_terms": 30,
      "sent_at": "2024-01-15T11:00:00Z",
      "paid_at": null,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T11:00:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "pages": 2,
  "per_page": 20,
  "summary": {
    "total_amount": 25000.00,
    "paid_amount": 18000.00,
    "outstanding_amount": 7000.00,
    "draft_count": 2,
    "sent_count": 15,
    "paid_count": 6,
    "overdue_count": 2
  }
}
```

### POST /invoices
Create new invoice.

#### Request Body
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

#### Success Response (201)
```json
{
  "id": 2,
  "invoice_number": "INV-000002",
  "customer_id": 1,
  "customer_name": "John Customer",
  "status": "draft",
  "issue_date": "2024-01-15",
  "due_date": "2024-02-15",
  "subtotal": 2500.00,
  "tax_rate": 8.00,
  "tax_amount": 200.00,
  "total_amount": 2700.00,
  "currency": "USD",
  "notes": "Thank you for your business!",
  "payment_terms": 30,
  "late_fee": 25.00,
  "items": [
    {
      "id": 1,
      "description": "Consulting Services",
      "quantity": 10.0000,
      "unit_price": 100.00,
      "total": 1000.00
    },
    {
      "id": 2,
      "description": "Development Work",
      "quantity": 20.0000,
      "unit_price": 75.00,
      "total": 1500.00
    }
  ],
  "created_at": "2024-01-15T12:00:00Z",
  "updated_at": "2024-01-15T12:00:00Z"
}
```

### GET /invoices/{invoice_id}
Get specific invoice details.

#### Success Response (200)
```json
{
  "id": 1,
  "invoice_number": "INV-000001",
  "customer": {
    "id": 1,
    "name": "John Customer",
    "email": "customer@example.com",
    "company": "Customer Corp",
    "address": {
      "street": "123 Main St",
      "city": "New York",
      "state": "NY",
      "postal_code": "10001",
      "country": "US"
    }
  },
  "status": "sent",
  "issue_date": "2024-01-15",
  "due_date": "2024-02-15",
  "subtotal": 1000.00,
  "tax_rate": 8.00,
  "tax_amount": 80.00,
  "total_amount": 1080.00,
  "currency": "USD",
  "notes": "Thank you for your business!",
  "payment_terms": 30,
  "late_fee": 25.00,
  "items": [
    {
      "id": 1,
      "description": "Web Development Services",
      "quantity": 40.0000,
      "unit_price": 25.00,
      "total": 1000.00
    }
  ],
  "payments": [],
  "sent_at": "2024-01-15T11:00:00Z",
  "paid_at": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

### PUT /invoices/{invoice_id}
Update invoice (only if status is draft).

#### Request Body
```json
{
  "customer_id": 1,
  "issue_date": "2024-01-16",
  "due_date": "2024-02-16",
  "tax_rate": 10.0,
  "notes": "Updated invoice",
  "items": [
    {
      "description": "Updated Consulting Services",
      "quantity": 15,
      "unit_price": 120.00
    }
  ]
}
```

#### Success Response (200)
Returns updated invoice object similar to GET response.

### DELETE /invoices/{invoice_id}
Delete invoice (only if status is draft).

#### Success Response (204)
No content

### POST /invoices/{invoice_id}/send
Send invoice to customer via email.

#### Request Body (Optional)
```json
{
  "email_template": "default",
  "custom_message": "Please find attached your invoice.",
  "send_copy_to_self": true
}
```

#### Success Response (200)
```json
{
  "id": 1,
  "status": "sent",
  "sent_at": "2024-01-15T12:30:00Z",
  "email_sent": true,
  "email_address": "customer@example.com"
}
```

### POST /invoices/{invoice_id}/mark-paid
Mark invoice as paid (manual payment recording).

#### Request Body
```json
{
  "payment_date": "2024-01-20",
  "payment_method": "bank_transfer",
  "reference": "TXN123456",
  "notes": "Payment received via bank transfer"
}
```

#### Success Response (200)
```json
{
  "id": 1,
  "status": "paid",
  "paid_at": "2024-01-20T10:00:00Z",
  "payment": {
    "id": 1,
    "amount": 1080.00,
    "payment_date": "2024-01-20",
    "payment_method": "bank_transfer",
    "reference": "TXN123456",
    "notes": "Payment received via bank transfer"
  }
}
```

### GET /invoices/{invoice_id}/pdf
Generate and download invoice PDF.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `template` | string | No | PDF template (professional, modern, classic) |
| `download` | boolean | No | Force download (default: true) |

#### Success Response (200)
Returns PDF file with appropriate headers:
```http
Content-Type: application/pdf
Content-Disposition: attachment; filename="INV-000001.pdf"
```

## Payment Processing

### POST /stripe/create-payment-intent
Create Stripe PaymentIntent for invoice payment.

#### Request Body
```json
{
  "invoice_id": 1,
  "save_payment_method": false,
  "return_url": "https://yourdomain.com/payment/return"
}
```

#### Success Response (200)
```json
{
  "client_secret": "pi_1234567890_secret_abc123",
  "payment_intent_id": "pi_1234567890",
  "amount": 1080,
  "currency": "usd",
  "status": "requires_payment_method"
}
```

### POST /stripe/create-checkout-session
Create Stripe Checkout session for hosted payment.

#### Request Body
```json
{
  "invoice_id": 1,
  "success_url": "https://yourdomain.com/payment/success?session_id={CHECKOUT_SESSION_ID}",
  "cancel_url": "https://yourdomain.com/payment/cancel"
}
```

#### Success Response (200)
```json
{
  "session_id": "cs_test_abc123",
  "session_url": "https://checkout.stripe.com/pay/cs_test_abc123",
  "expires_at": 1609459200
}
```

### POST /stripe/webhook
Stripe webhook endpoint for payment events.

#### Headers
```http
Stripe-Signature: t=1609459200,v1=abc123def456...
```

#### Webhook Events Handled
- `payment_intent.succeeded`
- `payment_intent.payment_failed`
- `invoice.payment_succeeded`
- `customer.created`
- `payment_method.attached`

#### Success Response (200)
```json
{
  "received": true
}
```

### GET /payments
Get paginated list of payments.

#### Query Parameters
Similar to invoices endpoint with additional filters:
- `payment_method`: Filter by payment method
- `status`: Filter by payment status
- `amount_min`: Minimum amount filter
- `amount_max`: Maximum amount filter

#### Success Response (200)
```json
{
  "items": [
    {
      "id": 1,
      "invoice_id": 1,
      "invoice_number": "INV-000001",
      "customer_name": "John Customer",
      "amount": 1080.00,
      "currency": "USD",
      "payment_method": "card",
      "status": "completed",
      "payment_date": "2024-01-20",
      "reference": "pi_1234567890",
      "provider_payment_id": "pi_1234567890",
      "notes": "Payment via Stripe",
      "created_at": "2024-01-20T10:00:00Z"
    }
  ],
  "total": 15,
  "summary": {
    "total_amount": 15000.00,
    "completed_amount": 14000.00,
    "pending_amount": 1000.00,
    "failed_amount": 0.00
  }
}
```

### POST /payments/{payment_id}/refund
Process payment refund.

#### Request Body
```json
{
  "amount": 540.00,
  "reason": "requested_by_customer",
  "notes": "Customer requested partial refund"
}
```

#### Success Response (200)
```json
{
  "refund_id": "re_1234567890",
  "amount": 540.00,
  "currency": "USD",
  "status": "succeeded",
  "reason": "requested_by_customer",
  "created_at": "2024-01-21T10:00:00Z"
}
```

## Analytics Endpoints

### GET /analytics/dashboard
Get dashboard analytics overview.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date_range` | integer | No | Number of days to analyze (default: 30) |
| `compare_previous` | boolean | No | Include previous period comparison |

#### Success Response (200)
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
    },
    "top_performing_metrics": [
      {
        "type": "top_customer",
        "label": "Top Customer",
        "value": "Acme Corp",
        "amount": 5000.00,
        "icon": "user"
      }
    ]
  }
}
```

### GET /analytics/revenue
Get detailed revenue analytics.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `period` | string | No | Time period (daily, weekly, monthly) |
| `months` | integer | No | Number of months for analysis (default: 12) |

#### Success Response (200)
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
      },
      {
        "period": "2023-12-01T00:00:00Z", 
        "revenue": 21000.00,
        "invoice_count": 18
      }
    ],
    "revenue_by_customer": [
      {
        "customer_name": "Acme Corp",
        "revenue": 5000.00,
        "percentage": 20.0
      }
    ],
    "revenue_by_currency": [
      {
        "currency": "USD",
        "revenue": 22000.00,
        "percentage": 88.0
      },
      {
        "currency": "EUR",
        "revenue": 3000.00,
        "percentage": 12.0
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

### GET /analytics/customers
Get comprehensive customer analytics.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date_range` | integer | No | Number of days to analyze (default: 180) |

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "time_range": {
      "start_date": "2023-07-01T00:00:00Z",
      "end_date": "2024-01-31T23:59:59Z"
    },
    "acquisition": {
      "new_customers_per_month": [
        {
          "month": "2024-01",
          "count": 3
        }
      ],
      "acquisition_cost": 150.00
    },
    "retention": {
      "retention_rate": 85.5,
      "churn_rate": 14.5
    },
    "lifetime_value": {
      "average_ltv": 5000.00,
      "ltv_distribution": [
        {
          "range": "0-1000",
          "count": 5
        },
        {
          "range": "1000-5000",
          "count": 15
        }
      ]
    },
    "top_customers": [
      {
        "id": 1,
        "name": "Acme Corp",
        "total_revenue": 5000.00,
        "invoice_count": 5,
        "average_payment_time": 15.5
      }
    ],
    "payment_behavior": {
      "average_payment_days": 18.5,
      "payment_methods": {
        "card": 60.0,
        "bank_transfer": 30.0,
        "other": 10.0
      }
    }
  }
}
```

### GET /analytics/performance
Get business performance analytics.

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "collection_efficiency": {
      "efficiency_score": 92.5,
      "collection_rate": 87.3
    },
    "invoice_processing": {
      "avg_processing_time": 2.5,
      "bottlenecks": [
        "Manual approval process",
        "Payment method setup"
      ]
    },
    "cash_flow": {
      "cash_flow_timeline": [
        {
          "period": "2024-01",
          "inflow": 25000.00,
          "outflow": 5000.00,
          "net": 20000.00
        }
      ],
      "projected_cash_flow": [
        {
          "period": "2024-02",
          "projected_inflow": 28000.00,
          "confidence": 0.85
        }
      ]
    },
    "aging_analysis": {
      "aging_buckets": {
        "0-30": 15,
        "31-60": 5,
        "61-90": 2,
        "90+": 1
      }
    },
    "performance_score": {
      "score": 87.5,
      "grade": "A",
      "improvement_areas": [
        "Reduce average payment time",
        "Improve collection rate"
      ]
    }
  }
}
```

### GET /analytics/export
Export analytics data in various formats.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `report_type` | string | Yes | Report type (dashboard, revenue, customers, performance) |
| `format_type` | string | No | Export format (json, csv, pdf) |
| `date_range` | integer | No | Number of days to include |

#### Success Response (200)
For JSON format, returns the data directly. For CSV/PDF, returns file download.

## WebSocket API

### Connection
Connect to WebSocket with authentication token:

```javascript
const ws = new WebSocket('wss://api.yourdomain.com/api/v1/ws/ws?token=your_jwt_token');
```

### Connection Events

#### connection
Welcome message after successful connection:
```json
{
  "type": "connection",
  "message": "Connected to InvoiceFlow Pro",
  "timestamp": "2024-01-15T10:30:00Z",
  "user_id": 1
}
```

#### heartbeat
Periodic connection health check:
```json
{
  "type": "heartbeat",
  "timestamp": "2024-01-15T10:30:00Z",
  "connections": 5
}
```

### Business Events

#### invoice_created
New invoice created:
```json
{
  "type": "invoice_created",
  "title": "New Invoice Created",
  "message": "Invoice INV-000001 has been created",
  "data": {
    "invoice_id": 1,
    "invoice_number": "INV-000001",
    "customer_name": "John Customer",
    "total": 1080.00,
    "currency": "USD"
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "action_url": "/invoices/1"
}
```

#### payment_received
Payment successfully processed:
```json
{
  "type": "payment_received",
  "title": "Payment Received",
  "message": "Payment of USD 1080.00 received for Invoice INV-000001",
  "data": {
    "payment_id": 1,
    "invoice_id": 1,
    "invoice_number": "INV-000001",
    "amount": 1080.00,
    "currency": "USD",
    "payment_method": "card"
  },
  "timestamp": "2024-01-20T15:30:00Z",
  "action_url": "/invoices/1",
  "priority": "info"
}
```

#### invoice_overdue
Invoice became overdue:
```json
{
  "type": "invoice_overdue",
  "title": "Invoice Overdue",
  "message": "Invoice INV-000001 is now overdue",
  "data": {
    "invoice_id": 1,
    "invoice_number": "INV-000001",
    "customer_name": "John Customer",
    "amount_due": 1080.00,
    "currency": "USD",
    "days_overdue": 5
  },
  "timestamp": "2024-02-20T10:00:00Z",
  "action_url": "/invoices/1",
  "priority": "high"
}
```

### Client Messages

#### ping
Send heartbeat ping:
```json
{
  "type": "ping"
}
```

#### subscribe
Subscribe to specific event types:
```json
{
  "type": "subscribe",
  "events": ["invoice_created", "payment_received"]
}
```

#### typing
Send typing indicator:
```json
{
  "type": "typing",
  "is_typing": true
}
```

## File Upload/Download

### POST /files/upload
Upload files (invoices, receipts, documents).

#### Request
```http
Content-Type: multipart/form-data

file: [file data]
category: invoice_attachment
description: Supporting documentation
```

#### Success Response (201)
```json
{
  "id": "file_123456789",
  "filename": "receipt.pdf",
  "size": 1024576,
  "content_type": "application/pdf",
  "category": "invoice_attachment",
  "description": "Supporting documentation",
  "url": "https://files.yourdomain.com/files/file_123456789",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### GET /files/{file_id}
Download file.

#### Success Response (200)
Returns file with appropriate headers:
```http
Content-Type: application/pdf
Content-Disposition: attachment; filename="receipt.pdf"
Content-Length: 1024576
```

### DELETE /files/{file_id}
Delete file.

#### Success Response (204)
No content

## Webhook Management

### POST /webhooks
Create webhook endpoint.

#### Request Body
```json
{
  "url": "https://your-app.com/webhooks/invoiceflow",
  "events": ["invoice.created", "payment.received"],
  "secret": "your_webhook_secret"
}
```

#### Success Response (201)
```json
{
  "id": "wh_123456789",
  "url": "https://your-app.com/webhooks/invoiceflow",
  "events": ["invoice.created", "payment.received"],
  "secret": "your_webhook_secret",
  "active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### GET /webhooks
List webhook endpoints.

### PUT /webhooks/{webhook_id}
Update webhook endpoint.

### DELETE /webhooks/{webhook_id}
Delete webhook endpoint.

## API Examples

### Complete Invoice Creation Workflow

```python
import requests
import json

# Configuration
API_BASE = "https://api.yourdomain.com/api/v1"
headers = {
    "Authorization": "Bearer your_access_token",
    "Content-Type": "application/json"
}

# 1. Create customer
customer_data = {
    "name": "Example Customer",
    "email": "customer@example.com",
    "company": "Example Corp",
    "address": {
        "street": "123 Main St",
        "city": "New York",
        "state": "NY",
        "postal_code": "10001",
        "country": "US"
    },
    "payment_terms": 30
}

customer_response = requests.post(
    f"{API_BASE}/customers",
    headers=headers,
    json=customer_data
)
customer = customer_response.json()
print(f"Created customer: {customer['id']}")

# 2. Create invoice
invoice_data = {
    "customer_id": customer["id"],
    "issue_date": "2024-01-15",
    "due_date": "2024-02-15",
    "currency": "USD",
    "tax_rate": 8.0,
    "notes": "Thank you for your business!",
    "items": [
        {
            "description": "Web Development Services",
            "quantity": 40,
            "unit_price": 25.00
        },
        {
            "description": "Design Services",
            "quantity": 10,
            "unit_price": 50.00
        }
    ]
}

invoice_response = requests.post(
    f"{API_BASE}/invoices",
    headers=headers,
    json=invoice_data
)
invoice = invoice_response.json()
print(f"Created invoice: {invoice['invoice_number']}")

# 3. Send invoice
send_response = requests.post(
    f"{API_BASE}/invoices/{invoice['id']}/send",
    headers=headers,
    json={
        "send_copy_to_self": True,
        "custom_message": "Please find your invoice attached."
    }
)
print(f"Invoice sent: {send_response.json()}")

# 4. Create payment intent
payment_intent_response = requests.post(
    f"{API_BASE}/stripe/create-payment-intent",
    headers=headers,
    json={
        "invoice_id": invoice["id"],
        "save_payment_method": False
    }
)
payment_intent = payment_intent_response.json()
print(f"Payment intent created: {payment_intent['client_secret']}")
```

### Analytics Dashboard Data Fetching

```javascript
async function fetchDashboardData() {
    const token = localStorage.getItem('access_token');
    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
    
    try {
        // Fetch all analytics data in parallel
        const [dashboard, revenue, customers, performance] = await Promise.all([
            fetch('/api/v1/analytics/dashboard?date_range=30', { headers }).then(r => r.json()),
            fetch('/api/v1/analytics/revenue?period=monthly&months=12', { headers }).then(r => r.json()),
            fetch('/api/v1/analytics/customers?date_range=180', { headers }).then(r => r.json()),
            fetch('/api/v1/analytics/performance?date_range=90', { headers }).then(r => r.json())
        ]);
        
        return {
            dashboard: dashboard.data,
            revenue: revenue.data,
            customers: customers.data,
            performance: performance.data
        };
    } catch (error) {
        console.error('Failed to fetch analytics data:', error);
        throw error;
    }
}

// Usage
fetchDashboardData().then(data => {
    console.log('Dashboard KPIs:', data.dashboard.kpis);
    console.log('Revenue trend:', data.revenue.time_series);
    console.log('Customer retention:', data.customers.retention);
    console.log('Performance score:', data.performance.performance_score);
});
```

### WebSocket Integration

```javascript
class InvoiceFlowWebSocket {
    constructor(token) {
        this.token = token;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }
    
    connect() {
        const wsUrl = `wss://api.yourdomain.com/api/v1/ws/ws?token=${this.token}`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            
            // Subscribe to specific events
            this.ws.send(JSON.stringify({
                type: 'subscribe',
                events: ['invoice_created', 'payment_received', 'invoice_overdue']
            }));
        };
        
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.reconnect();
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    handleMessage(message) {
        switch (message.type) {
            case 'invoice_created':
                this.showNotification('New Invoice', message.message, 'success');
                this.updateInvoiceList();
                break;
                
            case 'payment_received':
                this.showNotification('Payment Received', message.message, 'success');
                this.updateDashboard();
                break;
                
            case 'invoice_overdue':
                this.showNotification('Invoice Overdue', message.message, 'warning');
                this.updateOverdueList();
                break;
                
            case 'heartbeat':
                // Handle heartbeat
                break;
                
            default:
                console.log('Unhandled message type:', message.type);
        }
    }
    
    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.pow(2, this.reconnectAttempts) * 1000; // Exponential backoff
            
            setTimeout(() => {
                console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                this.connect();
            }, delay);
        } else {
            console.error('Max reconnection attempts reached');
        }
    }
    
    showNotification(title, message, type) {
        // Implement your notification system
        console.log(`${type.toUpperCase()}: ${title} - ${message}`);
    }
    
    updateInvoiceList() {
        // Refresh invoice list in UI
    }
    
    updateDashboard() {
        // Refresh dashboard data
    }
    
    updateOverdueList() {
        // Refresh overdue invoices
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Usage
const wsClient = new InvoiceFlowWebSocket('your_access_token');
wsClient.connect();
```

This comprehensive API documentation provides all the information needed to integrate with InvoiceFlow Pro's REST API and WebSocket services.