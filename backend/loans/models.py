from django.db import models

from customers.models import Customer


class Loan(models.Model):
    loan_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, related_name="loans", on_delete=models.CASCADE)
    loan_amount = models.FloatField()
    tenure = models.IntegerField(help_text="Tenure in months")
    interest_rate = models.FloatField(help_text="Annual interest rate in percent")
    monthly_repayment = models.FloatField()
    emis_paid_on_time = models.IntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ["loan_id"]

    def __str__(self) -> str:
        return f"Loan {self.loan_id} for customer {self.customer_id}"

