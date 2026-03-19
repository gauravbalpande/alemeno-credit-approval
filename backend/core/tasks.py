import logging
from pathlib import Path

import pandas as pd
from celery import shared_task
from django.db import transaction

from customers.models import Customer
from loans.models import Loan
from core.credit_scoring import calculate_approved_limit, calculate_emi

logger = logging.getLogger(__name__)


def _normalize_column_name(name: object) -> str:
    s = str(name).strip().lower()
    s = s.replace("-", "_").replace(" ", "_")
    s = "".join(ch for ch in s if ch.isalnum() or ch == "_")
    while "__" in s:
        s = s.replace("__", "_")
    return s


_MISSING = object()


def _row_value(row: pd.Series, *candidates: str, default=_MISSING):
    for key in candidates:
        if key in row and pd.notna(row[key]):
            return row[key]
    if default is _MISSING:
        raise KeyError(candidates[0] if candidates else "missing_key")
    return default


def _read_excel_normalized(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    df.columns = [_normalize_column_name(c) for c in df.columns]
    return df


@shared_task
def ingest_customers_from_excel(file_path: str) -> int:
    path = Path(file_path)
    if not path.exists():
        logger.error("Customer Excel file not found: %s", file_path)
        return 0

    df = _read_excel_normalized(path)
    created_count = 0
    with transaction.atomic():
        for _, row in df.iterrows():
            try:
                monthly_salary = float(
                    _row_value(
                        row,
                        "monthly_salary",
                        "monthlyincome",
                        "monthly_income",
                        "salary",
                        "income",
                    )
                )
            except KeyError:
                logger.error(
                    "Customer ingestion failed. Expected salary column like "
                    "`monthly_salary` (or variants). Found columns: %s",
                    list(df.columns),
                )
                raise

            approved_limit = calculate_approved_limit(monthly_salary)
            customer, created = Customer.objects.update_or_create(
                phone_number=_row_value(row, "phone_number", "phone", "mobile", "mobile_number"),
                defaults={
                    "first_name": _row_value(row, "first_name", "firstname", "first"),
                    "last_name": _row_value(row, "last_name", "lastname", "last"),
                    "age": int(_row_value(row, "age")),
                    "monthly_salary": monthly_salary,
                    "approved_limit": approved_limit,
                    "current_debt": float(
                        _row_value(row, "current_debt", "debt", "currentdebt", default=0.0)
                    ),
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

    df = _read_excel_normalized(path)
    created_count = 0
    with transaction.atomic():
        for _, row in df.iterrows():
            try:
                customer_id = _row_value(row, "customer_id", "customer", "customerid", "cust_id")
                customer = Customer.objects.get(pk=customer_id)
            except Customer.DoesNotExist:
                logger.warning(
                    "Skipping loan row; customer %s not found", row.get("customer_id")
                )
                continue
            except KeyError:
                logger.error(
                    "Loan ingestion failed. Expected customer id column like "
                    "`customer_id` (or variants). Found columns: %s",
                    list(df.columns),
                )
                raise

            loan_amount = float(_row_value(row, "loan_amount", "loanamount", "amount"))
            tenure = int(_row_value(row, "tenure", "tenure_months", "months"))
            interest_rate = float(_row_value(row, "interest_rate", "interestrate", "rate"))
            monthly_repayment = calculate_emi(loan_amount, interest_rate, tenure)

            Loan.objects.update_or_create(
                customer=customer,
                loan_amount=loan_amount,
                start_date=_row_value(row, "start_date", "startdate", "start"),
                defaults={
                    "tenure": tenure,
                    "interest_rate": interest_rate,
                    "monthly_repayment": monthly_repayment,
                    "emis_paid_on_time": int(
                        _row_value(
                            row,
                            "emis_paid_on_time",
                            "emispaidontime",
                            "on_time_emis",
                            default=0,
                        )
                    ),
                    "end_date": _row_value(row, "end_date", "enddate", "end"),
                },
            )
            created_count += 1

    logger.info("Ingested %s loans from %s", created_count, file_path)
    return created_count

