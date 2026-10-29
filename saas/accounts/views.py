from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from remediation.models import RemediationRequest
from licensing.models import AuditReport

from .forms import RegisterForm
from .models import Workspace, WorkspaceMembership


def _license_for_user(user):
    membership = getattr(user, "workspace_membership", None)
    if membership:
        return membership.workspace.license
    return user.license


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            verification_url = request.build_absolute_uri(
                reverse(
                    "verify_email",
                    kwargs={"uidb64": uid, "token": token},
                )
            )

            send_mail(
                subject="Confirmez votre adresse e-mail SystAudit",
                message=render_to_string(
                    "accounts/email_verification.txt",
                    {
                        "user": user,
                        "verification_url": verification_url,
                    },
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )

            return render(
                request,
                "accounts/verification_sent.html",
            )
    else:
        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form},
    )


def verify_email_view(request, uidb64, token):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is None or not default_token_generator.check_token(user, token):
        return render(
            request,
            "accounts/email_verification_invalid.html",
            status=400,
        )

    if not user.is_active:
        user.is_active = True
        user.save(update_fields=["is_active"])

    return render(request, "accounts/email_verified.html")


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
    license_obj = _license_for_user(request.user)
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
            "can_manage_license": license_obj.user_id == request.user.pk,
            "premium_price_xof": getattr(settings, "FEDAPAY_PREMIUM_PRICE_XOF", 0),
            "latest_audit": latest_audit,
            "audit_history": audit_history,
            "audit_count": audit_history.count(),
            "audit_history_chart": audit_history_chart,
            "remediation_requests": remediation_requests,
            "workspace_membership": getattr(request.user, "workspace_membership", None),
        },
    )


@login_required
def create_remediation_request(request, audit_id, category):
    if request.method != "POST":
        return redirect("dashboard")

    license_obj = _license_for_user(request.user)

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

    if category == "bitlocker":
        volumes = ["C:", "D:", "E:"]

        for volume in volumes:
            RemediationRequest.objects.get_or_create(
                audit_report=audit_report,
                remediation_id=f"REM-BITLOCKER-{volume[0]}",
                defaults={
                    "title": f"Remediate bitlocker {volume}",
                    "description": (
                        f"BitLocker protection is disabled on volume {volume}."
                    ),
                    "severity": finding.get(
                        "risk",
                        "medium",
                    ).upper(),
                    "target_volume": volume,
                },
            )

    else:
        remediation_map = {
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
                "severity": finding.get(
                    "risk",
                    "medium",
                ).upper(),
            },
        )

    return redirect("dashboard")


@login_required
def create_workspace_view(request):
    if request.method != "POST":
        return redirect("dashboard")
    if getattr(request.user, "workspace_membership", None):
        messages.error(request, "Ce compte appartient déjà à un espace d'équipe.")
        return redirect("dashboard")
    license_obj = request.user.license
    if hasattr(license_obj, "workspace"):
        messages.error(request, "Cette licence est déjà associée à un espace d'équipe.")
        return redirect("dashboard")
    name = request.POST.get("name", "").strip()
    if not name or len(name) > 120:
        messages.error(request, "Saisissez un nom d'équipe de 1 à 120 caractères.")
        return redirect("dashboard")
    workspace = Workspace.objects.create(
        name=name,
        owner=request.user,
        license=license_obj,
    )
    WorkspaceMembership.objects.create(
        workspace=workspace,
        user=request.user,
        role=WorkspaceMembership.OWNER,
    )
    messages.success(request, "Votre espace d'équipe est créé.")
    return redirect("dashboard")


@login_required
def add_workspace_member_view(request):
    if request.method != "POST":
        return redirect("dashboard")
    membership = getattr(request.user, "workspace_membership", None)
    if not membership or membership.role not in {WorkspaceMembership.OWNER, WorkspaceMembership.ADMIN}:
        return redirect("dashboard")
    email = request.POST.get("email", "").strip()
    member = User.objects.filter(email__iexact=email, is_active=True).first()
    if not member:
        messages.error(request, "Aucun compte confirmé n'utilise cette adresse e-mail.")
        return redirect("dashboard")
    if member.pk == request.user.pk:
        messages.error(request, "Vous êtes déjà propriétaire de cet espace.")
        return redirect("dashboard")
    if hasattr(member, "workspace_membership"):
        messages.error(request, "Ce compte est déjà membre d'un espace d'équipe.")
        return redirect("dashboard")
    WorkspaceMembership.objects.create(
        workspace=membership.workspace,
        user=member,
        role=WorkspaceMembership.MEMBER,
    )
    messages.success(request, f"{member.email} a rejoint l'espace d'équipe.")
    return redirect("dashboard")


@login_required
def remove_workspace_member_view(request, member_id):
    if request.method != "POST":
        return redirect("dashboard")
    membership = getattr(request.user, "workspace_membership", None)
    if not membership or membership.role not in {WorkspaceMembership.OWNER, WorkspaceMembership.ADMIN}:
        return redirect("dashboard")
    removed = WorkspaceMembership.objects.filter(
        workspace=membership.workspace,
        user_id=member_id,
        role=WorkspaceMembership.MEMBER,
    ).delete()[0]
    if removed:
        messages.success(request, "Le membre a été retiré de l'équipe.")
    return redirect("dashboard")
