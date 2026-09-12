from django.urls import path

from .views import (
    approve_remediation_request,
    execute_remediation_request,
)


urlpatterns = [
    path(
        "approve/<int:request_id>/",
        approve_remediation_request,
        name="approve_remediation_request",
    ),
    path(
        "execute/<int:request_id>/",
        execute_remediation_request,
        name="execute_remediation_request",
    ),
]