from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from core.tasks import ingest_customers_from_excel, ingest_loans_from_excel


class Command(BaseCommand):
    help = "Enqueue Celery tasks to ingest customer_data.xlsx and loan_data.xlsx"

    def add_arguments(self, parser):
        parser.add_argument(
            "--customers",
            default=str(Path(settings.BASE_DIR) / "data" / "customer_data.xlsx"),
            help="Path to customer_data.xlsx",
        )
        parser.add_argument(
            "--loans",
            default=str(Path(settings.BASE_DIR) / "data" / "loan_data.xlsx"),
            help="Path to loan_data.xlsx",
        )

    def handle(self, *args, **options):
        customers_path = options["customers"]
        loans_path = options["loans"]

        res1 = ingest_customers_from_excel.delay(customers_path)
        res2 = ingest_loans_from_excel.delay(loans_path)

        self.stdout.write(
            self.style.SUCCESS(
                "Ingestion tasks enqueued.\n"
                f"- customers task id: {res1.id}\n"
                f"- loans task id: {res2.id}\n"
                "Make sure the `celery` service is running."
            )
        )

