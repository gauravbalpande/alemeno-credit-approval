from datetime import date, timedelta

from rest_framework import serializers

from core.credit_scoring import LoanRecord, calculate_emi, compute_credit_score
from customers.models import Customer
from loans.models import Loan


class LoanSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())

    class Meta:
        model = Loan
        fields = [
            "loan_id",
            "customer",
            "loan_amount",
            "tenure",
            "interest_rate",
            "monthly_repayment",
            "emis_paid_on_time",
            "start_date",
            "end_date",
        ]
        read_only_fields = ["loan_id", "monthly_repayment"]


class CheckEligibilitySerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.FloatField()
    tenure = serializers.IntegerField()
    interest_rate = serializers.FloatField()

    def validate(self, attrs):
        customer_id = attrs["customer_id"]
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise serializers.ValidationError({"customer_id": "Customer not found"})

        attrs["customer"] = customer
        return attrs

    def evaluate(self):
        customer: Customer = self.validated_data["customer"]
        loan_amount = self.validated_data["loan_amount"]
        tenure = self.validated_data["tenure"]
        interest_rate = self.validated_data["interest_rate"]

        past_loans = list(
            Loan.objects.filter(customer=customer).order_by("start_date")
        )
        loan_records = [
            LoanRecord(
                loan_amount=l.loan_amount,
                tenure=l.tenure,
                interest_rate=l.interest_rate,
                monthly_repayment=l.monthly_repayment,
                emis_paid_on_time=l.emis_paid_on_time,
                start_date=l.start_date,
                end_date=l.end_date,
            )
            for l in past_loans
        ]

        score_result = compute_credit_score(
            customer_loans=loan_records,
            approved_limit=customer.approved_limit,
            monthly_salary=customer.monthly_salary,
            requested_loan_amount=loan_amount,
            requested_tenure=tenure,
            requested_interest_rate=interest_rate,
        )

        approval = False
        corrected_interest_rate = None
        applied_interest_rate = interest_rate

        if not score_result["eligible"]:
            approval = False
        else:
            score = score_result["score"]
            if score > 50:
                approval = True
            elif 30 <= score <= 50:
                if interest_rate >= 12.0:
                    approval = True
                else:
                    approval = True
                    corrected_interest_rate = 12.0
                    applied_interest_rate = corrected_interest_rate
            elif 10 <= score < 30:
                if interest_rate >= 16.0:
                    approval = True
                else:
                    approval = True
                    corrected_interest_rate = 16.0
                    applied_interest_rate = corrected_interest_rate
            else:
                approval = False

        if approval:
            monthly_installment = calculate_emi(loan_amount, applied_interest_rate, tenure)
        else:
            monthly_installment = 0.0

        return {
            "customer_id": customer.customer_id,
            "approval": approval,
            "interest_rate": interest_rate,
            "corrected_interest_rate": corrected_interest_rate,
            "monthly_installment": monthly_installment,
            "credit_score": score_result.get("score", 0),
            "message": score_result.get("reason"),
        }


class CreateLoanSerializer(CheckEligibilitySerializer):
    def create(self, validated_data):
        evaluation = self.evaluate()
        if not evaluation["approval"]:
            raise serializers.ValidationError(
                {"non_field_errors": ["Loan not approved based on eligibility rules."]}
            )

        customer: Customer = validated_data["customer"]
        loan_amount = validated_data["loan_amount"]
        tenure = validated_data["tenure"]

        applied_interest_rate = (
            evaluation["corrected_interest_rate"] or evaluation["interest_rate"]
        )
        monthly_installment = evaluation["monthly_installment"]

        start_date = date.today()
        end_date = start_date + timedelta(days=30 * tenure)

        loan = Loan.objects.create(
            customer=customer,
            loan_amount=loan_amount,
            tenure=tenure,
            interest_rate=applied_interest_rate,
            monthly_repayment=monthly_installment,
            emis_paid_on_time=0,
            start_date=start_date,
            end_date=end_date,
        )

        # Update customer's current debt
        customer.current_debt += loan_amount
        customer.save(update_fields=["current_debt"])

        return loan, evaluation

