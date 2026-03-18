from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable


@dataclass
class LoanRecord:
    loan_amount: float
    tenure: int
    interest_rate: float
    monthly_repayment: float
    emis_paid_on_time: int
    start_date: date
    end_date: date


def calculate_approved_limit(monthly_salary: float) -> float:
    raw_limit = 36 * monthly_salary
    # Round to nearest lakh (100000)
    lakhs = round(raw_limit / 100000)
    return lakhs * 100000


def calculate_emi(principal: float, annual_interest_rate: float, tenure_months: int) -> float:
    if tenure_months <= 0:
        raise ValueError("Tenure must be positive")
    monthly_rate = annual_interest_rate / (12 * 100)
    if monthly_rate == 0:
        return principal / tenure_months
    factor = (1 + monthly_rate) ** tenure_months
    emi = principal * monthly_rate * factor / (factor - 1)
    return round(emi, 2)


def compute_credit_score(
    *,
    customer_loans: Iterable[LoanRecord],
    approved_limit: float,
    monthly_salary: float,
    requested_loan_amount: float,
    requested_tenure: int,
    requested_interest_rate: float,
    today: date | None = None,
) -> dict:
    today = today or date.today()

    total_current_loans = sum(l.loan_amount for l in customer_loans)
    total_active_loan_amount = sum(
        l.loan_amount for l in customer_loans if l.start_date <= today <= l.end_date
    )
    total_emis = sum(l.monthly_repayment for l in customer_loans)

    if total_current_loans > approved_limit:
        return {
            "score": 0,
            "eligible": False,
            "reason": "total_current_loans_exceed_limit",
        }

    if total_emis > 0.5 * monthly_salary:
        return {
            "score": 0,
            "eligible": False,
            "reason": "existing_emi_burden_too_high",
        }

    score = 100

    # Past loans paid on time
    total_emis_possible = sum(l.tenure for l in customer_loans) or 1
    total_emis_on_time = sum(l.emis_paid_on_time for l in customer_loans)
    on_time_ratio = total_emis_on_time / total_emis_possible
    if on_time_ratio < 0.5:
        score -= 30
    elif on_time_ratio < 0.8:
        score -= 15

    # Number of loans taken
    num_loans = len(list(customer_loans))
    if num_loans > 5:
        score -= 20
    elif num_loans > 2:
        score -= 10

    # Loan activity in current year
    current_year_loans = [
        l for l in customer_loans if l.start_date.year == today.year
    ]
    if len(current_year_loans) > 3:
        score -= 10

    # Loan approved volume vs limit
    if total_active_loan_amount + requested_loan_amount > approved_limit:
        score -= 30

    score = max(score, 0)

    requested_emi = calculate_emi(
        requested_loan_amount, requested_interest_rate, requested_tenure
    )

    if requested_emi + total_emis > 0.5 * monthly_salary:
        return {
            "score": score,
            "eligible": False,
            "reason": "emi_would_exceed_50_percent_salary",
        }

    return {
        "score": score,
        "eligible": True,
        "reason": "ok",
    }

