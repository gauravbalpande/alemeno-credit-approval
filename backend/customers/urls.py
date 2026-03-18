from django.urls import path

from customers.views import RegisterCustomerView

urlpatterns = [
    path("register", RegisterCustomerView.as_view(), name="register-customer"),
]

