from django.http import JsonResponse


def home(request):
    return JsonResponse(
        {
            "service": "credit-system",
            "endpoints": {
                "register": "/register",
                "check_eligibility": "/check-eligibility",
                "create_loan": "/create-loan",
                "view_loan": "/view-loan/<loan_id>",
                "view_customer_loans": "/view-loans/<customer_id>",
            },
        }
    )

