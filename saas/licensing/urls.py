from django.urls import path

from .views import validate_license


urlpatterns = [
    path("validate/", validate_license, name="validate-license"),
]
