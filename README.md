## Credit Approval Backend System

This is a production-ready backend for a **Credit Approval System** built with **Django**, **Django REST Framework**, **PostgreSQL**, **Celery**, **Redis**, and **Docker**.

### Tech Stack

- **Backend**: Django 4, Django REST Framework
- **Database**: PostgreSQL
- **Background Jobs**: Celery + Redis
- **Containerization**: Docker, Docker Compose

### Project Structure

- `backend/credit_system/` – Django project configuration, settings, Celery config
- `backend/core/` – Shared utilities, credit scoring logic, ingestion tasks
- `backend/customers/` – Customer model, serializers, and `/register` API
- `backend/loans/` – Loan model, business logic, and loan-related APIs

### Setup with Docker

1. Copy `.env` and adjust secrets if needed:
   - Database credentials
   - `SECRET_KEY`
   - `ALLOWED_HOSTS`

2. Build and start services:

```bash
docker-compose build
docker-compose up
```

3. Run migrations inside the `web` container (first time only):

```bash
docker-compose run --rm web python manage.py migrate
```

4. (Optional) Create a superuser:

```bash
docker-compose run --rm web python manage.py createsuperuser
```

### Celery Workers

Celery workers are started as a separate service via Docker Compose:

- Service: `celery`
- Broker / backend: Redis (configured via `REDIS_URL` in `.env`)

### Data Ingestion

Background tasks exist for Excel ingestion:

- `core.tasks.ingest_customers_from_excel(file_path)`
- `core.tasks.ingest_loans_from_excel(file_path)`

You can trigger these via Django shell or a custom management command, for example:

```bash
docker-compose run --rm web python manage.py shell
```

```python
from core.tasks import ingest_customers_from_excel, ingest_loans_from_excel
ingest_customers_from_excel.delay("/app/backend/customer_data.xlsx")
ingest_loans_from_excel.delay("/app/backend/loan_data.xlsx")
```

### API Endpoints

Base prefix: `/api/`

- `POST /api/register` – Register a customer and auto-calculate `approved_limit`
- `POST /api/check-eligibility` – Check credit score, loan rules, and return:
  - `approval`
  - `interest_rate`
  - `corrected_interest_rate`
  - `monthly_installment`
- `POST /api/create-loan` – Use eligibility logic, create loan if approved
- `GET /api/view-loan/{loan_id}` – Return loan + customer details
- `GET /api/view-loans/{customer_id}` – Return all loans with `repayments_left`

### Running Tests

Inside the `web` container:

```bash
docker-compose run --rm web python manage.py test
```

### Notes

- Business rules are implemented in `core/credit_scoring.py` and `loans/serializers.py`.
- Logging is configured in `credit_system/settings.py` to log to stdout (suitable for Docker).
- The system is stateless aside from the PostgreSQL and Redis containers, making it production-ready with proper externalized configuration.

