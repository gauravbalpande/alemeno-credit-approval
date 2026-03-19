from django.contrib import admin
from django.urls import include, path

from core.views import home

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("", include("customers.urls")),
    path("", include("loans.urls")),
]

