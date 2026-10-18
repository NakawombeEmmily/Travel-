# Travel System - Database Schema (PostgreSQL 16)

## Schemas
- crm - Core business data (clients, trips, visas, feedback, CRM, payments, outbox)
- dmin - Company admin ledger (admin_ledger, admin_invoices, admin_revenue_summary)

## Core Tables

### crm.users
- id (UUID, PK)
- email (VARCHAR(255), unique, not null)
- password_hash (VARCHAR(255), not null, argon2)
- full_name (VARCHAR(255), not null)
- role (ENUM: super_admin, admin, agent, accountant, read_only, not null)
- is_active (BOOLEAN, default true)
- assigned_clients_only (BOOLEAN, default false) - for agents
- last_login_at (TIMESTAMP)
- created_at, updated_at (TIMESTAMPTZ)
- created_by (UUID FK -> users)

### crm.clients (encrypted PII)
- id (UUID, PK)
- full_name (VARCHAR(255), not null)
- date_of_birth (DATE)
- gender (VARCHAR(20))
- email (VARCHAR(255))
- phone (VARCHAR(50))
- address (TEXT)
- passport_number_enc (BYTEA, encrypted AES-256-GCM) - never store plaintext
- passport_number_hash (VARCHAR(64), unique, for lookups) - SHA-256 of plaintext
- passport_issue_date (DATE)
- passport_expiry_date (DATE)
- issuing_country (VARCHAR(100))
- nationality (VARCHAR(100))
- emergency_contact (VARCHAR(255))
- is_deleted (BOOLEAN, default false) - soft delete
- created_at, updated_at (TIMESTAMPTZ)
- created_by (UUID FK)

Indexes: passport_number_hash (unique), email, nationality, is_deleted, created_at

### crm.trips
- id (UUID, PK)
- client_id (UUID FK -> crm.clients, not null)
- destination_country (VARCHAR(100), not null)
- travel_start_date (DATE, not null)
- travel_end_date (DATE)
- purpose (VARCHAR(50): tourism, business, study, medical, other)
- itinerary_notes (TEXT)
- total_cost (DECIMAL(15,2), not null)
- currency (CHAR(3), default 'USD' - UGX, USD, EUR, KES)
- status (VARCHAR(20): inquiry, confirmed, in_progress, completed, cancelled)
- created_at, updated_at
- created_by (UUID FK)

### crm.visas
- id (UUID, PK)
- client_id (UUID FK, not null)
- trip_id (UUID FK)
- destination_country (VARCHAR(100), not null)
- visa_type (VARCHAR(100))
- application_date (DATE)
- submission_date (DATE)
- reference_number (VARCHAR(100))
- status (VARCHAR(30): not_required, not_started, documents_pending, submitted, in_review, approved, rejected, expired)
- approval_date (DATE)
- expiry_date (DATE)
- notes (TEXT)
- created_at, updated_at
- created_by (UUID FK)

### crm.visa_status_history
- id (UUID, PK)
- visa_id (UUID FK, not null)
- old_status (VARCHAR(30))
- new_status (VARCHAR(30), not null)
- changed_by (UUID FK)
- changed_at (TIMESTAMPTZ, default now())
- note (TEXT)

### crm.documents (encrypted)
- id (UUID, PK)
- client_id (UUID FK)
- visa_id (UUID FK)
- file_key (VARCHAR(512), S3/R2/MinIO key) - file stored in object storage
- original_filename (VARCHAR(255))
- file_type (VARCHAR(100))
- file_size (BIGINT)
- is_encrypted (BOOLEAN, default true)
- uploaded_by (UUID FK)
- uploaded_at (TIMESTAMPTZ, default now())
- checksum (VARCHAR(64))

### crm.feedback
- id (UUID, PK)
- client_id (UUID FK, not null)
- trip_id (UUID FK)
- rating (SMALLINT, check 1-5, not null)
- comment (TEXT)
- category (VARCHAR(30): service, price, visa_support, communication)
- sentiment (VARCHAR(20): positive, neutral, negative, mixed) - auto-calculated
- feedback_date (DATE, not null, default now())
- created_at

### crm.interactions
- id (UUID, PK)
- client_id (UUID FK, not null)
- interaction_type (VARCHAR(20): call, email, whatsapp, meeting, other)
- notes (TEXT)
- follow_up_date (DATE)
- contacted_by (UUID FK)
- created_at (TIMESTAMPTZ, default now())

### crm.leads
- id (UUID, PK)
- client_id (UUID FK)
- full_name (VARCHAR(255), not null)
- email (VARCHAR(255))
- phone (VARCHAR(50))
- source (VARCHAR(50))
- status (VARCHAR(20): lead, contacted, quote_sent, negotiation, won, lost)
- assigned_to (UUID FK)
- created_at, updated_at

### crm.tags
- id (UUID, PK)
- name (VARCHAR(50), unique)
- color (VARCHAR(7)) # hex

### crm.client_tags (junction)
- client_id (UUID FK)
- tag_id (UUID FK)
- PRIMARY KEY (client_id, tag_id)

### crm.follow_up_tasks
- id (UUID, PK)
- client_id (UUID FK, not null)
- title (VARCHAR(255), not null)
- description (TEXT)
- assigned_to (UUID FK)
- due_date (DATE)
- status (VARCHAR(20): pending, in_progress, completed, cancelled)
- priority (VARCHAR(10): low, medium, high)
- created_by (UUID FK)
- created_at, updated_at

### crm.payments
- id (UUID, PK)
- client_id (UUID FK, not null)
- trip_id (UUID FK)
- amount (DECIMAL(15,2), not null)
- currency (CHAR(3), not null, default 'USD')
- exchange_rate (DECIMAL(12,6), not null, default 1.0) - rate at payment time
- method (VARCHAR(20): card, mobile_money, bank_transfer, cash)
- provider (VARCHAR(30): mock, flutterwave, stripe, mtn, airtel)
- provider_transaction_id (VARCHAR(255))
- status (VARCHAR(20): pending, completed, failed, refunded, partial)
- paid_at (TIMESTAMPTZ)
- invoice_number (VARCHAR(50), unique)
- notes (TEXT)
- created_at, updated_at
- created_by (UUID FK)

Indexes: client_id, trip_id, status, invoice_number, provider_transaction_id

### crm.payment_installments
- id (UUID, PK)
- payment_id (UUID FK -> payments)
- amount (DECIMAL(15,2), not null)
- due_date (DATE)
- paid_at (TIMESTAMPTZ)
- status (VARCHAR(20): pending, paid, overdue)

### crm.payment_outbox (transactional outbox)
- id (UUID, PK)
- event_id (UUID, unique, not null) - idempotency key
- aggregate_type (VARCHAR(50): payment)
- aggregate_id (UUID, not null)
- event_type (VARCHAR(50): payment_created, payment_updated, payment_refunded)
- payload (JSONB, not null)
- status (VARCHAR(20): pending, processing, completed, failed, dead_letter)
- attempts (INTEGER, default 0)
- max_attempts (INTEGER, default 10)
- last_attempt_at (TIMESTAMPTZ)
- next_attempt_at (TIMESTAMPTZ)
- error_message (TEXT)
- created_at (TIMESTAMPTZ, default now())
- processed_at (TIMESTAMPTZ)

Indexes: status, next_attempt_at, aggregate_id, event_id

### crm.audit_logs
- id (UUID, PK)
- user_id (UUID FK)
- action (VARCHAR(100), not null) - e.g., client.view, client.update, passport.reveal
- resource_type (VARCHAR(50), not null)
- resource_id (UUID)
- ip_address (INET)
- user_agent (TEXT)
- details (JSONB) - redacted, no full passport/card
- created_at (TIMESTAMPTZ, default now())

Indexes: user_id, resource_type, resource_id, created_at, action

## Admin Schema Tables

### admin.admin_ledger
- id (UUID, PK)
- crm_payment_id (UUID) - reference to crm.payments
- client_id (UUID)
- trip_id (UUID)
- amount (DECIMAL(15,2), not null)
- currency (CHAR(3), not null)
- status (VARCHAR(20))
- provider (VARCHAR(30))
- provider_transaction_id (VARCHAR(255))
- invoice_number (VARCHAR(50))
- synced_at (TIMESTAMPTZ, default now())
- last_reconciled_at (TIMESTAMPTZ)

Unique: crm_payment_id

### admin.admin_invoices
- id (UUID, PK)
- ledger_id (UUID FK -> admin_ledger)
- invoice_number (VARCHAR(50))
- issue_date (DATE, not null, default now())
- due_date (DATE)
- amount (DECIMAL(15,2))
- status (VARCHAR(20))
- pdf_key (VARCHAR(512)) - stored in object storage
- created_at (TIMESTAMPTZ)

### admin.admin_revenue_summary (daily/monthly)
- id (UUID, PK)
- summary_date (DATE, not null)
- period_type (VARCHAR(10): daily, monthly)
- total_amount (DECIMAL(15,2), not null)
- currency (CHAR(3), not null)
- transaction_count (INTEGER, not null)
- completed_count (INTEGER)
- failed_count (INTEGER)
- refunded_count (INTEGER)
- created_at (TIMESTAMPTZ, default now())

Unique: (summary_date, period_type, currency)
