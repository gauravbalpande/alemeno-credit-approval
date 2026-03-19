from rest_framework import serializers

from core.credit_scoring import calculate_approved_limit
from customers.models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "customer_id",
            "first_name",
            "last_name",
            "age",
            "phone_number",
            "monthly_salary",
            "approved_limit",
            "current_debt",
        ]
        read_only_fields = ["customer_id", "approved_limit"]

    def create(self, validated_data):
        monthly_salary = validated_data["monthly_salary"]
        validated_data["approved_limit"] = calculate_approved_limit(monthly_salary)
        return super().create(validated_data)


class RegisterCustomerSerializer(serializers.ModelSerializer):
    
    monthly_income = serializers.FloatField(source="monthly_salary")

    class Meta:
        model = Customer
        fields = [
            "first_name",
            "last_name",
            "age",
            "phone_number",
            "monthly_income",
        ]

    def create(self, validated_data):
        monthly_salary = validated_data["monthly_salary"]
        approved_limit = calculate_approved_limit(monthly_salary)
        customer = Customer.objects.create(
            approved_limit=approved_limit,
            current_debt=0.0,
            **validated_data,
        )
        return customer

