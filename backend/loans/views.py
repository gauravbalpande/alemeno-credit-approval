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
            data = LoanSerializer(loan).data
            data.update(
                {
                    "approval": evaluation["approval"],
                    "interest_rate": evaluation["interest_rate"],
                    "corrected_interest_rate": evaluation["corrected_interest_rate"],
                    "monthly_installment": evaluation["monthly_installment"],
                    "credit_score": evaluation["credit_score"],
                }
            )
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ViewLoanDetail(APIView):
    def get(self, request, loan_id: int, *args, **kwargs):
        loan = get_object_or_404(Loan, pk=loan_id)
        loan_data = LoanSerializer(loan).data
        customer_data = CustomerSerializer(loan.customer).data
        return Response(
            {
                "loan": loan_data,
                "customer": customer_data,
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
            loan_data = LoanSerializer(loan).data
            loan_data["repayments_left"] = repayments_left
            serialized_loans.append(loan_data)

        return Response(serialized_loans, status=status.HTTP_200_OK)

