from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django.shortcuts import get_object_or_404
from remediation.models import RemediationRequest
from licensing.models import AuditReport
from .forms import RegisterForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form},
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("dashboard")
    else:
        form = AuthenticationForm()

    return render(
        request,
        "accounts/login.html",
        {"form": form},
    )


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard_view(request):
    license_obj = request.user.license
    license_key = str(license_obj.key)

    devices = license_obj.devices.all()

    audit_history = (
        AuditReport.objects
        .filter(device__license=license_obj)
        .select_related("device")
        .order_by("-created_at")
    )

    latest_audit = audit_history.first()

    audit_history_chart = list(reversed(audit_history[:10]))

    remediation_requests = []

    if latest_audit:
        remediation_requests = (
            RemediationRequest.objects
            .filter(audit_report=latest_audit)
            .order_by("-created_at")
        )

    return render(
        request,
        "accounts/dashboard.html",
        {
            "user": request.user,
            "license": license_obj,
            "devices": devices,
            "devices_used": devices.count(),
            "license_key": license_key,
            "license_key_masked": f"{license_key[:8]}-****-****-****-****",
            "latest_audit": latest_audit,
            "audit_history": audit_history,
            "audit_count": audit_history.count(),
            "audit_history_chart": audit_history_chart,
            "remediation_requests": remediation_requests,
        },
    )

@login_required
def create_remediation_request(request, audit_id, category):
    if request.method != "POST":
        return redirect("dashboard")

    license_obj = request.user.license

    audit_report = get_object_or_404(
        AuditReport,
        pk=audit_id,
        device__license=license_obj,
    )

    finding = next(
        (
            item
            for item in audit_report.findings
            if item.get("category") == category
        ),
        None,
    )

    if not finding:
        return redirect("dashboard")

    remediation_map = {
        "bitlocker": "REM-BITLOCKER",
        "firewall": "REM-FIREWALL",
    }

    remediation_id = remediation_map.get(category)

    if not remediation_id:
        return redirect("dashboard")

    RemediationRequest.objects.get_or_create(
        audit_report=audit_report,
        remediation_id=remediation_id,
        defaults={
            "title": f"Remediate {category}",
            "description": finding.get("message", ""),
            "severity": finding.get("risk", "medium").upper(),
        },
    )

    return redirect("dashboard")