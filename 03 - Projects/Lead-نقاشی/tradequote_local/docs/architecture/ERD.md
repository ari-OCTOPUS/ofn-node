# ERD — schema v1

```mermaid
erDiagram
    COMPANY_SETTINGS ||--o{ DOCUMENTS : "supplier snapshot at issue"
    CUSTOMERS ||--o{ DOCUMENTS : "customerId"
    DOCUMENTS ||--o{ LINE_ITEMS : "documentId (cascade)"
    DOCUMENTS ||--o| DOCUMENT_SNAPSHOTS : "frozen at issue"
    DOCUMENTS ||--o{ PAYMENTS : "invoiceId"
    DOCUMENTS ||--o{ SHARE_EVENTS : "documentId"
    DOCUMENTS |o--o| DOCUMENTS : "quote ↔ invoice link"
    NUMBER_SEQUENCES ||--o{ DOCUMENTS : "allocates docNumber"

    COMPANY_SETTINGS {
        int id PK "always 1"
        text legalName
        text tradingName "nullable"
        text abn "nullable, 11 digits normalized"
        bool gstRegistered
        text address
        text phone
        text email
        text bankAccountName
        text bsb
        text accountNumber
        text paymentInstructions
        int defaultPaymentTermsDays
        int defaultQuoteValidityDays
        text gstMode "inclusive|exclusive"
        text quotePrefix
        text invoicePrefix
        text documentFooter "nullable"
        bool onboardingComplete
        int createdAt "epoch ms"
        int updatedAt
    }
    NUMBER_SEQUENCES {
        text id PK "quote|invoice"
        int nextNumber
    }
    CUSTOMERS {
        text id PK "uuid"
        bool isBusiness
        text name
        text contactName "nullable"
        text email "nullable"
        text mobile "nullable"
        text abn "nullable"
        text billingAddress "nullable"
        text siteAddress "nullable"
        text notes "nullable"
        text preferredContact "telegram|email|phone|other, nullable"
        int archivedAt "nullable"
        int createdAt
        int updatedAt
    }
    DOCUMENTS {
        text id PK "uuid"
        text docType "quote|invoice"
        text docNumber UK
        text customerId FK
        text customerNameCache
        text status "see DOCUMENT_LIFECYCLE"
        int issueDate
        int expiryDate "quotes, nullable"
        int dueDate "invoices, nullable"
        text gstMode "inclusive|exclusive|none"
        text siteAddress "nullable"
        text workType "nullable"
        text scopeOfWork "nullable"
        text terms "nullable"
        text customerNotes "nullable"
        text internalNotes "nullable"
        int subtotalExGstCents
        int gstCents
        int totalCents
        text sourceQuoteId "nullable FK"
        text convertedInvoiceId "nullable FK"
        int sentAt "nullable, manual confirm"
        int voidedAt "nullable"
        int createdAt
        int updatedAt
    }
    LINE_ITEMS {
        text id PK
        text documentId FK
        int position
        text description
        int quantityMilli "1000 = 1.0"
        text unitLabel "nullable"
        int unitPriceCents
        bool gstApplicable
        int lineTotalCents
    }
    DOCUMENT_SNAPSHOTS {
        text documentId PK_FK
        text snapshotJson "full DocumentRenderData"
        int createdAt
    }
    PAYMENTS {
        text id PK
        text invoiceId FK
        int paidAt
        int amountCents "> 0"
        text method "bankTransfer|cash|card|cheque|other"
        text reference "nullable"
        text notes "nullable"
        int deletedAt "nullable soft delete"
        int createdAt
    }
    SHARE_EVENTS {
        text id PK
        text documentId FK
        text channel "telegram|email|system|savePdf"
        text outcome "prepared|shareSheetOpened|manuallyConfirmedSent|failedToOpen|cancelledOrUnknown"
        int createdAt
    }
    AUDIT_EVENTS {
        text id PK
        text entityType
        text entityId
        text action
        text detailsJson "nullable"
        int createdAt
    }
    MESSAGE_TEMPLATES {
        text id PK "quote|invoice|reminder"
        text subject "nullable, email"
        text body
    }
    APP_META {
        text key PK
        text value
    }
```

Indexes: `documents(docType, status)`, `documents(customerId)`,
`documents(dueDate)`, `lineItems(documentId)`, `payments(invoiceId)`,
`customers(name)`. Foreign keys ON (`PRAGMA foreign_keys = ON` at open).
All timestamps are epoch **milliseconds UTC**; display formatting is
Australian (`dd/MM/yyyy`) via `core/dates.dart`.
