from django.urls import path

from loans.views import (
    CheckEligibilityView,
    CreateLoanView,
    ViewCustomerLoans,
    ViewLoanDetail,
)

urlpatterns = [
    path("check-eligibility", CheckEligibilityView.as_view(), name="check-eligibility"),
    path("create-loan", CreateLoanView.as_view(), name="create-loan"),
    path("view-loan/<int:loan_id>", ViewLoanDetail.as_view(), name="view-loan"),
    path(
        "view-loans/<int:customer_id>",
        ViewCustomerLoans.as_view(),
        name="view-customer-loans",
    ),
]

