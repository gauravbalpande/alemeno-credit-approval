from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from customers.models import Customer
from loans.models import Loan
from core.credit_scoring import calculate_approved_limit


class CreditSystemAPITests(APITestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name="John",
            last_name="Doe",
            age=30,
            phone_number="1234567890",
            monthly_salary=50000,
            approved_limit=calculate_approved_limit(50000),
            current_debt=0.0,
        )

    def test_register_customer(self):
        url = reverse("register-customer")
        data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "age": 28,
            "phone_number": "9999999999",
            "monthly_salary": 60000,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("approved_limit", response.data)

    def test_check_eligibility(self):
        url = reverse("check-eligibility")
        data = {
            "customer_id": self.customer.customer_id,
            "loan_amount": 200000,
            "tenure": 12,
            "interest_rate": 14.0,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("approval", response.data)

    def test_create_loan_and_view(self):
        create_url = reverse("create-loan")
        payload = {
            "customer_id": self.customer.customer_id,
            "loan_amount": 100000,
            "tenure": 12,
            "interest_rate": 14.0,
        }
        response = self.client.post(create_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        loan_id = response.data["loan_id"]

        view_url = reverse("view-loan", kwargs={"loan_id": loan_id})
        view_response = self.client.get(view_url, format="json")
        self.assertEqual(view_response.status_code, status.HTTP_200_OK)
        self.assertIn("loan", view_response.data)
        self.assertIn("customer", view_response.data)

    def test_view_loans_for_customer(self):
        Loan.objects.create(
            customer=self.customer,
            loan_amount=50000,
            tenure=10,
            interest_rate=12.0,
            monthly_repayment=6000,
            emis_paid_on_time=2,
            start_date=date.today(),
            end_date=date.today(),
        )
        url = reverse("view-customer-loans", kwargs={"customer_id": self.customer.customer_id})
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(isinstance(response.data, list))

