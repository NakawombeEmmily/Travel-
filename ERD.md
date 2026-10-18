# Travel System - Entity Relationship Diagram (Text Description)

See DB_SCHEMA.md for full field definitions. Key relationships:
- users 1:N clients (created_by)
- clients 1:N trips
- clients 1:N visas
- clients 1:N payments
- trips 1:N payments, 1:N visas
- visas 1:N visa_status_history, 1:N documents
- payments 1:N payment_installments, 1:N payment_outbox (via aggregate)
- audit_logs linked to users/resources
- admin_ledger linked to crm payments by crm_payment_id

ERD visual to be generated from migrations/schema.
