from django.urls import path

from .views import activate_device, validate_license


urlpatterns = [
    path("validate/", validate_license, name="validate-license"),
    path("activate/", activate_device, name="activate-device"),
]