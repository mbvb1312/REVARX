# Backend Notes

The backend stores abandoned e-commerce customers, generated recovery emails, campaign records, and replies.

## Main Files

- `backend/database.py`: SQLAlchemy models and SQLite setup.
- `backend/models.py`: Pydantic request models.
- `backend/csv_parser.py`: CSV/TXT abandoned customer import.
- `backend/scheduler.py`: scans pending messages and sends them.
- `main.py`: FastAPI routes and live recovery flow.

## Customer Fields

Leads now represent abandoned e-commerce customers:

- `name`
- `email`
- `age`
- `gender`
- `state`
- `product_viewed`
- `product_category`
- `notes`
- `ab_preference`
- `status`

## Status Values

- `new`
- `pending`
- `hot`
- `warm`
- `cold`
- `no_response`
- `email_failed`
- `unsubscribed`

## Uploads

`POST /upload-leads` accepts CSV and TXT files. Recommended CSV columns:

```text
name,email,age,gender,state,product_viewed,product_category,notes
```

TXT lines can be comma, pipe, or semicolon separated.

## Date Handling

Use `utc_now()` from `backend.database` for UTC timestamps.
