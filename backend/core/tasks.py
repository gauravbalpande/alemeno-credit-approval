import logging
from pathlib import Path

import pandas as pd
from celery import shared_task
from django.db import transaction

from customers.models import Customer
from loans.models import Loan
from core.credit_scoring import calculate_approved_limit, calculate_emi

logger = logging.getLogger(__name__)


@shared_task
def ingest_customers_from_excel(file_path: str) -> int:
    path = Path(file_path)
    if not path.exists():
        logger.error("Customer Excel file not found: %s", file_path)
        return 0

    df = pd.read_excel(path)
    created_count = 0
    with transaction.atomic():
        for _, row in df.iterrows():
            monthly_salary = float(row["monthly_salary"])
            approved_limit = calculate_approved_limit(monthly_salary)
            customer, created = Customer.objects.update_or_create(
                phone_number=row["phone_number"],
                defaults={
                    "first_name": row["first_name"],
                    "last_name": row["last_name"],
                    "age": int(row["age"]),
                    "monthly_salary": monthly_salary,
                    "approved_limit": approved_limit,
                    "current_debt": float(row.get("current_debt", 0.0)),
                },
            )
            if created:
                created_count += 1

    logger.info("Ingested %s customers from %s", created_count, file_path)
    return created_count


@shared_task
def ingest_loans_from_excel(file_path: str) -> int:
    path = Path(file_path)
    if not path.exists():
        logger.error("Loan Excel file not found: %s", file_path)
        return 0

    df = pd.read_excel(path)
    created_count = 0
    with transaction.atomic():
        for _, row in df.iterrows():
            try:
                customer = Customer.objects.get(pk=row["customer_id"])
            except Customer.DoesNotExist:
                logger.warning(
                    "Skipping loan row; customer %s not found", row["customer_id"]
                )
                continue

            loan_amount = float(row["loan_amount"])
            tenure = int(row["tenure"])
            interest_rate = float(row["interest_rate"])
            monthly_repayment = calculate_emi(loan_amount, interest_rate, tenure)

            Loan.objects.update_or_create(
                customer=customer,
                loan_amount=loan_amount,
                start_date=row["start_date"],
                defaults={
                    "tenure": tenure,
                    "interest_rate": interest_rate,
                    "monthly_repayment": monthly_repayment,
                    "emis_paid_on_time": int(row.get("emis_paid_on_time", 0)),
                    "end_date": row["end_date"],
                },
            )
            created_count += 1

    logger.info("Ingested %s loans from %s", created_count, file_path)
    return created_count

