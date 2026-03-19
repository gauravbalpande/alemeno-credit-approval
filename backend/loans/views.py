from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from customers.serializers import CustomerSerializer
from loans.models import Loan
from loans.serializers import (
    CheckEligibilitySerializer,
    CreateLoanSerializer,
    LoanSerializer,
)


class CheckEligibilityView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = CheckEligibilitySerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.evaluate()
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateLoanView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = CreateLoanSerializer(data=request.data)
        if serializer.is_valid():
            try:
                loan, evaluation = serializer.save()
            except Exception as exc:
                return Response(
                    {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {
                    "loan_id": loan.loan_id,
                    "customer_id": loan.customer_id,
                    "loan_approved": True,
                    "message": "Loan approved",
                    "monthly_installment": evaluation["monthly_installment"],
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ViewLoanDetail(APIView):
    def get(self, request, loan_id: int, *args, **kwargs):
        loan = get_object_or_404(Loan, pk=loan_id)
        return Response(
            {
                "loan_id": loan.loan_id,
                "customer": {
                    "customer_id": loan.customer.customer_id,
                    "first_name": loan.customer.first_name,
                    "last_name": loan.customer.last_name,
                    "phone_number": loan.customer.phone_number,
                    "age": loan.customer.age,
                },
                "loan_amount": loan.loan_amount,
                "interest_rate": loan.interest_rate,
                "monthly_installment": loan.monthly_repayment,
                "tenure": loan.tenure,
            }
        )


class ViewCustomerLoans(APIView):
    def get(self, request, customer_id: int, *args, **kwargs):
        loans = Loan.objects.filter(customer_id=customer_id)
        serialized_loans = []
        for loan in loans:
            repayments_left = max(
                loan.tenure - loan.emis_paid_on_time,
                0,
            )
            serialized_loans.append(
                {
                    "loan_id": loan.loan_id,
                    "loan_amount": loan.loan_amount,
                    "interest_rate": loan.interest_rate,
                    "monthly_installment": loan.monthly_repayment,
                    "repayments_left": repayments_left,
                }
            )

        return Response(serialized_loans, status=status.HTTP_200_OK)

