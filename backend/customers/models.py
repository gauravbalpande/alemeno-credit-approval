from django.db import models


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.IntegerField()
    phone_number = models.CharField(max_length=20, unique=True)
    monthly_salary = models.FloatField()
    approved_limit = models.FloatField()
    current_debt = models.FloatField(default=0.0)

    class Meta:
        ordering = ["customer_id"]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.customer_id})"

