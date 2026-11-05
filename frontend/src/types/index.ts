// Common types for InvoiceFlow Pro

export interface BaseEntity {
  id: number;
  created_at: string;
  updated_at: string;
}

// User types
export interface User extends BaseEntity {
  email: string;
  first_name: string;
  last_name: string;
  company_name?: string;
  phone?: string;
  is_active: boolean;
  is_verified: boolean;
  role: UserRole;
  auth_provider: AuthProvider;
  last_login?: string;
  timezone: string;
  language: string;
  currency: string;
}

export type UserRole = 'admin' | 'user' | 'manager' | 'viewer';
export type AuthProvider = 'local' | 'google' | 'github' | 'microsoft';

// Customer types
export interface Customer extends BaseEntity {
  name: string;
  email: string;
  phone?: string;
  company?: string;
  address_line_1?: string;
  address_line_2?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  country?: string;
  tax_number?: string;
  notes?: string;
  total_invoices: number;
  total_amount: number;
  amount_paid: number;
  amount_outstanding: number;
  is_active: boolean;
  preferred_currency: string;
  payment_terms: number;
  tags?: string;
}

// Invoice types
export interface Invoice extends BaseEntity {
  invoice_number: string;
  customer_id: number;
  customer_name: string;
  reference_number?: string;
  type: InvoiceType;
  status: InvoiceStatus;
  issue_date: string;
  due_date: string;
  sent_date?: string;
  viewed_date?: string;
  paid_date?: string;
  currency: string;
  subtotal: number;
  discount_percentage: number;
  discount_amount: number;
  tax_rate: number;
  tax_amount: number;
  total: number;
  amount_paid: number;
  amount_due: number;
  is_recurring: boolean;
  recurrence_interval?: RecurrenceInterval;
  recurrence_count?: number;
  next_recurrence_date?: string;
  parent_invoice_id?: number;
  notes?: string;
  terms_and_conditions?: string;
  footer_text?: string;
  pdf_url?: string;
  attachments?: string;
  email_sent_count: number;
  last_email_sent?: string;
  items: InvoiceItem[];
}

export interface InvoiceItem extends BaseEntity {
  invoice_id: number;
  description: string;
  quantity: number;
  unit_price: number;
  tax_rate: number;
  tax_amount: number;
  subtotal: number;
  total: number;
  unit?: string;
  sku?: string;
  category?: string;
  sort_order: number;
}

export type InvoiceStatus = 
  | 'draft'
  | 'sent' 
  | 'viewed'
  | 'paid'
  | 'partially_paid'
  | 'overdue'
  | 'cancelled'
  | 'refunded';

export type InvoiceType = 'standard' | 'recurring' | 'credit_note' | 'proforma';
export type RecurrenceInterval = 'weekly' | 'monthly' | 'quarterly' | 'yearly';

// Payment types
export interface Payment extends BaseEntity {
  invoice_id: number;
  invoice_number: string;
  customer_name: string;
  amount: number;
  currency: string;
  payment_method: PaymentMethod;
  status: PaymentStatus;
  payment_date: string;
  processed_date?: string;
  reference_number?: string;
  transaction_id?: string;
  confirmation_number?: string;
  gateway_provider?: string;
  gateway_transaction_id?: string;
  gateway_fee: number;
  gateway_response?: string;
  is_refunded: boolean;
  refund_amount: number;
  refund_reason?: RefundReason;
  refund_date?: string;
  refund_transaction_id?: string;
  bank_name?: string;
  check_number?: string;
  routing_number?: string;
  account_number_last_4?: string;
  notes?: string;
  receipt_url?: string;
  is_reconciled: boolean;
  reconciled_date?: string;
  bank_statement_date?: string;
}

export type PaymentMethod = 
  | 'cash'
  | 'check'
  | 'credit_card'
  | 'debit_card'
  | 'bank_transfer'
  | 'paypal'
  | 'stripe'
  | 'square'
  | 'wire_transfer'
  | 'cryptocurrency'
  | 'other';

export type PaymentStatus = 
  | 'pending'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'refunded'
  | 'partially_refunded';

export type RefundReason = 
  | 'customer_request'
  | 'billing_error'
  | 'duplicate_payment'
  | 'fraudulent'
  | 'cancelled_service'
  | 'other';

// Analytics types
export interface DashboardSummary {
  total_revenue: number;
  total_invoices: number;
  paid_invoices: number;
  pending_invoices: number;
  overdue_invoices: number;
  total_customers: number;
  average_invoice_value: number;
  collection_rate: number;
  revenue_growth: number;
  invoice_growth: number;
}

export interface RevenueMetric {
  period: string;
  revenue: number;
  invoices_count: number;
  average_invoice: number;
}

export interface CustomerMetric {
  customer_id: number;
  customer_name: string;
  total_revenue: number;
  invoice_count: number;
  average_invoice: number;
  last_invoice_date: string;
}

// API Response types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface ListResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_prev: boolean;
}

// Form types
export interface InvoiceFormData {
  customer_id: number;
  invoice_number?: string;
  currency: string;
  issue_date: Date;
  due_date: Date;
  items: InvoiceItemFormData[];
  notes?: string;
  discount_percentage?: number;
  tax_rate?: number;
  terms_and_conditions?: string;
  footer_text?: string;
}

export interface InvoiceItemFormData {
  description: string;
  quantity: number;
  unit_price: number;
  tax_rate?: number;
  unit?: string;
  sku?: string;
  category?: string;
}

export interface CustomerFormData {
  name: string;
  email: string;
  phone?: string;
  company?: string;
  address_line_1?: string;
  address_line_2?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  country?: string;
  tax_number?: string;
  notes?: string;
  preferred_currency?: string;
  payment_terms?: number;
}

export interface PaymentFormData {
  invoice_id: number;
  amount: number;
  payment_method: PaymentMethod;
  payment_date: Date;
  reference_number?: string;
  notes?: string;
}

// UI types
export interface TableColumn<T> {
  key: keyof T;
  label: string;
  sortable?: boolean;
  render?: (value: any, item: T) => React.ReactNode;
}

export interface FilterOption {
  label: string;
  value: string | number;
}

export interface SearchFilters {
  search?: string;
  status?: string;
  customer_id?: number;
  date_from?: string;
  date_to?: string;
  currency?: string;
  payment_method?: string;
}

// Theme types
export type ThemeMode = 'light' | 'dark' | 'system';

// Notification types
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  actions?: NotificationAction[];
}

export interface NotificationAction {
  label: string;
  action: () => void;
  variant?: 'primary' | 'secondary';
}