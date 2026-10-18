# Travel System — ER Diagram (Phase 1)

```mermaid
erDiagram
    users {
        uuid id PK
        string email UK
        string password_hash
        string full_name
        enum role
        bool is_active
        bool assigned_clients_only
        timestamp last_login_at
        uuid created_by FK
    }
    audit_log {
        uuid id PK
        uuid actor_id FK
        string action
        string entity_type
        uuid entity_id
        string ip_address
        text metadata
        timestamp created_at
    }
    clients {
        uuid id PK
        string full_name
        date date_of_birth
        string gender
        string email
        string phone
        text address
        bytes passport_number_enc
        string passport_number_hash UK
        date passport_issue_date
        date passport_expiry_date
        string issuing_country
        string nationality
        string emergency_contact
        bool consent_given
        bool is_deleted
        uuid created_by FK
        uuid updated_by FK
    }

    users ||--o{ audit_log : "acts"
    users ||--o{ clients : "creates"
```

- Schemas: `crm` (all above), `admin` (ledger/invoices/revenue in Phase 4).
- Passport number is stored encrypted (`passport_number_enc`, AES-256-GCM) with a SHA-256 `passport_number_hash` for unique lookups.
- Soft delete on `clients` via `is_deleted` + `deleted_at`/`deleted_by`.
