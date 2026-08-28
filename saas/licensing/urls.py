from django.urls import path

from .views import activate_device, submit_audit_report, validate_license


urlpatterns = [
    path("validate/", validate_license, name="validate-license"),
    path("activate/", activate_device, name="activate-device"),
    path("audit/report/", submit_audit_report, name="submit-audit-report"),
]