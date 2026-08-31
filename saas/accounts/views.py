from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render

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

    latest_audit = (
        AuditReport.objects
        .filter(device__license=license_obj)
        .select_related("device")
        .first()
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
        },
    )