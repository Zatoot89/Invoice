-- InvoiceFlow Pro Database Initialization Script

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS invoiceflow_pro;
CREATE DATABASE IF NOT EXISTS invoiceflow_pro_test;

-- Connect to the main database
\c invoiceflow_pro;

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Enable other useful PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For full-text search
CREATE EXTENSION IF NOT EXISTS "unaccent";  -- For accent-insensitive search

-- Create indexes for better performance
-- These will be created by Alembic, but we can add them here for reference

-- Function to generate invoice numbers
CREATE OR REPLACE FUNCTION generate_invoice_number(prefix text DEFAULT 'INV', length integer DEFAULT 8)
RETURNS text AS $$
DECLARE
    max_number integer;
    next_number integer;
    formatted_number text;
BEGIN
    -- Get the maximum existing invoice number
    SELECT COALESCE(
        MAX(CAST(SUBSTRING(invoice_number FROM LENGTH(prefix) + 2) AS INTEGER)), 0
    ) INTO max_number
    FROM invoices 
    WHERE invoice_number ~ ('^' || prefix || '-[0-9]+$');
    
    -- Generate next number
    next_number := max_number + 1;
    
    -- Format with leading zeros
    formatted_number := prefix || '-' || LPAD(next_number::text, length, '0');
    
    RETURN formatted_number;
END;
$$ LANGUAGE plpgsql;

-- Function to update invoice totals
CREATE OR REPLACE FUNCTION calculate_invoice_totals()
RETURNS TRIGGER AS $$
BEGIN
    -- Update invoice totals when items change
    UPDATE invoices SET
        subtotal = (
            SELECT COALESCE(SUM(subtotal), 0)
            FROM invoice_items
            WHERE invoice_id = CASE 
                WHEN TG_OP = 'DELETE' THEN OLD.invoice_id
                ELSE NEW.invoice_id
            END
        ),
        tax_amount = (
            SELECT COALESCE(SUM(tax_amount), 0)
            FROM invoice_items
            WHERE invoice_id = CASE 
                WHEN TG_OP = 'DELETE' THEN OLD.invoice_id
                ELSE NEW.invoice_id
            END
        )
    WHERE id = CASE 
        WHEN TG_OP = 'DELETE' THEN OLD.invoice_id
        ELSE NEW.invoice_id
    END;
    
    -- Update total and amount_due
    UPDATE invoices SET
        total = subtotal + tax_amount - discount_amount,
        amount_due = subtotal + tax_amount - discount_amount - amount_paid
    WHERE id = CASE 
        WHEN TG_OP = 'DELETE' THEN OLD.invoice_id
        ELSE NEW.invoice_id
    END;
    
    RETURN CASE 
        WHEN TG_OP = 'DELETE' THEN OLD
        ELSE NEW
    END;
END;
$$ LANGUAGE plpgsql;

-- Function to update customer totals
CREATE OR REPLACE FUNCTION update_customer_totals()
RETURNS TRIGGER AS $$
DECLARE
    customer_id_to_update integer;
BEGIN
    -- Determine which customer to update
    customer_id_to_update := CASE 
        WHEN TG_OP = 'DELETE' THEN OLD.customer_id
        ELSE NEW.customer_id
    END;
    
    -- Update customer totals
    UPDATE customers SET
        total_invoices = (
            SELECT COUNT(*)
            FROM invoices
            WHERE customer_id = customer_id_to_update
            AND status != 'draft'
        ),
        total_amount = (
            SELECT COALESCE(SUM(total), 0)
            FROM invoices
            WHERE customer_id = customer_id_to_update
            AND status != 'draft'
        ),
        amount_paid = (
            SELECT COALESCE(SUM(amount_paid), 0)
            FROM invoices
            WHERE customer_id = customer_id_to_update
            AND status != 'draft'
        ),
        amount_outstanding = (
            SELECT COALESCE(SUM(amount_due), 0)
            FROM invoices
            WHERE customer_id = customer_id_to_update
            AND status IN ('sent', 'viewed', 'partially_paid', 'overdue')
        )
    WHERE id = customer_id_to_update;
    
    RETURN CASE 
        WHEN TG_OP = 'DELETE' THEN OLD
        ELSE NEW
    END;
END;
$$ LANGUAGE plpgsql;

-- Function to create analytics events
CREATE OR REPLACE FUNCTION create_analytics_event(
    user_id integer,
    event_type text,
    event_category text,
    event_action text,
    entity_type text DEFAULT NULL,
    entity_id integer DEFAULT NULL,
    amount numeric DEFAULT NULL,
    currency text DEFAULT NULL,
    event_data text DEFAULT NULL
)
RETURNS void AS $$
BEGIN
    INSERT INTO analytics_events (
        user_id, event_type, event_category, event_action,
        entity_type, entity_id, amount, currency, event_data,
        timestamp
    ) VALUES (
        user_id, event_type, event_category, event_action,
        entity_type, entity_id, amount, currency, event_data,
        NOW()
    );
END;
$$ LANGUAGE plpgsql;

-- Create some sample data (for development)
-- This should be removed in production

-- Sample users (passwords are hashed with bcrypt)
INSERT INTO users (email, hashed_password, first_name, last_name, company_name, is_active, is_verified, role) VALUES
('admin@invoiceflow.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewAa7bYwVdN6LQ2W', 'Admin', 'User', 'InvoiceFlow Pro', true, true, 'admin'),
('demo@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewAa7bYwVdN6LQ2W', 'Demo', 'User', 'Demo Company', true, true, 'user')
ON CONFLICT (email) DO NOTHING;

-- Sample customers
INSERT INTO customers (user_id, name, email, phone, company, address_line_1, city, state, postal_code, country, is_active) VALUES
(1, 'John Doe', 'john@example.com', '+1-555-123-4567', 'Acme Corporation', '123 Business St', 'New York', 'NY', '10001', 'USA', true),
(1, 'Jane Smith', 'jane@techcorp.com', '+1-555-987-6543', 'Tech Corporation', '456 Innovation Ave', 'San Francisco', 'CA', '94105', 'USA', true),
(2, 'Bob Wilson', 'bob@startup.co', '+1-555-456-7890', 'Startup Inc', '789 Venture Blvd', 'Austin', 'TX', '73301', 'USA', true)
ON CONFLICT DO NOTHING;