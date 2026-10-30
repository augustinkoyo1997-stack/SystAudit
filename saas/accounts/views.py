from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponse
from django.core.mail import send_mail
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from datetime import timedelta
from pathlib import Path
import base64
import re
import tempfile
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from remediation.models import RemediationRequest
from licensing.models import AuditReport, LicensedDevice

from .forms import ManagedComputerForm, RegisterForm, RepairInterventionForm
from .models import ManagedComputer, RepairIntervention, Workspace, WorkspaceInvitation, WorkspaceMembership
from src.deployment.office import generate_office_configuration
from src.deployment.windows_media import (
    DeploymentError,
    build_configured_windows_iso,
    inspect_windows_iso,
)


def _deployment_media_dir():
    return settings.BASE_DIR.parent / "media"


@login_required
def deployment_view(request):
    media_dir = _deployment_media_dir().resolve()
    media_dir.mkdir(parents=True, exist_ok=True)
    result = None

    if request.method == "POST":
        action = request.POST.get("action", "")
        try:
            if action in {"inspect", "build"}:
                iso_name = request.POST.get("iso_name", "").strip()
                if not iso_name or Path(iso_name).name != iso_name or not iso_name.lower().endswith(".iso"):
                    raise DeploymentError("Sélectionne un fichier ISO de la liste.")
                iso_path = (media_dir / iso_name).resolve()
                if iso_path.parent != media_dir or not iso_path.is_file():
                    raise DeploymentError("Cet ISO est introuvable dans le dossier media.")

                if action == "inspect":
                    details, digest = inspect_windows_iso(iso_path)
                    result = {"title": "Analyse de l'ISO terminée", "details": details, "digest": digest}
                else:
                    if request.POST.get("confirm_build") != "CREER ISO":
                        raise DeploymentError("Confirme la création en saisissant exactement CREER ISO.")
                    output_name = request.POST.get("output_name", "").strip()
                    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,119}\.iso", output_name, re.IGNORECASE):
                        raise DeploymentError("Donne au nouvel ISO un nom simple se terminant par .iso.")
                    index_value = request.POST.get("image_index", "").strip()
                    image_index = int(index_value) if index_value else None
                    output_path = (media_dir / output_name).resolve()
                    if output_path.parent != media_dir:
                        raise DeploymentError("Le fichier de sortie doit rester dans media.")
                    output, digest = build_configured_windows_iso(
                        iso_path,
                        output_path,
                        language=request.POST.get("language", "fr-FR").strip(),
                        image_index=image_index,
                    )
                    result = {"title": "Nouvel ISO prêt", "details": str(output), "digest": digest}
            elif action == "office-config":
                product_id = request.POST.get("product_id", "").strip()
                with tempfile.TemporaryDirectory(prefix="sysaudit-office-") as temporary:
                    config_path = generate_office_configuration(
                        Path(temporary) / "office-configuration.xml",
                        product_id=product_id,
                        language=request.POST.get("office_language", "fr-fr").strip(),
                        architecture=request.POST.get("office_architecture", "64"),
                        channel=request.POST.get("office_channel", "Current"),
                    )
                    response = HttpResponse(config_path.read_bytes(), content_type="application/xml; charset=utf-8")
                    response["Content-Disposition"] = 'attachment; filename="systaudit-office-configuration.xml"'
                    return response
            else:
                raise DeploymentError("Action de déploiement inconnue.")
        except (DeploymentError, ValueError, OSError) as exc:
            messages.error(request, str(exc))

    iso_files = []
    for candidate in media_dir.iterdir():
        if candidate.is_file() and candidate.suffix.lower() == ".iso":
            iso_files.append({"name": candidate.name, "size_mb": round(candidate.stat().st_size / (1024 * 1024))})

    return render(
        request,
        "accounts/deployment.html",
        {
            "iso_files": sorted(iso_files, key=lambda item: item["name"].lower()),
            "result": result,
            "can_manage_license": _license_for_user(request.user).user_id == request.user.pk,
        },
    )


def _license_for_user(user):
    membership = getattr(user, "workspace_membership", None)
    if membership:
        return membership.workspace.license
    return user.license


def _email_uses_console():
    return settings.EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend"


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
                {"email_console_mode": _email_uses_console()},
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
        next_url = request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
        return redirect("dashboard")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.POST.get("next") or request.GET.get("next")
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect("dashboard")
    else:
        form = AuthenticationForm()

    return render(
        request,
        "accounts/login.html",
        {"form": form, "next": request.POST.get("next") or request.GET.get("next", "")},
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

    workspace_membership = getattr(request.user, "workspace_membership", None)
    pending_invitations = WorkspaceInvitation.objects.none()
    if workspace_membership and workspace_membership.role in {WorkspaceMembership.OWNER, WorkspaceMembership.ADMIN}:
        pending_invitations = WorkspaceInvitation.objects.filter(
            workspace=workspace_membership.workspace,
            accepted_at__isnull=True,
            expires_at__gt=timezone.now(),
        )

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
            "workspace_membership": workspace_membership,
            "pending_invitations": pending_invitations,
            "managed_computer_count": _managed_computers_for_user(request.user).count(),
            "email_console_mode": _email_uses_console(),
        },
    )


def _managed_computers_for_user(user):
    membership = getattr(user, "workspace_membership", None)
    if membership:
        return ManagedComputer.objects.filter(workspace=membership.workspace)
    return ManagedComputer.objects.filter(created_by=user, workspace__isnull=True)


@login_required
def equipment_view(request):
    computers = _managed_computers_for_user(request.user).prefetch_related("interventions")
    if request.method == "POST":
        form = ManagedComputerForm(request.POST)
        if form.is_valid():
            computer = form.save(commit=False)
            computer.created_by = request.user
            membership = getattr(request.user, "workspace_membership", None)
            computer.workspace = membership.workspace if membership else None
            computer.save()
            messages.success(request, f"Le poste {computer.asset_tag} a été ajouté. Vous pouvez maintenant suivre sa préparation et ses interventions.")
            return redirect("equipment_detail", asset_tag=computer.asset_tag)
    else:
        form = ManagedComputerForm()

    active_computers = computers.exclude(status=ManagedComputer.STATUS_RETIRED)
    return render(request, "accounts/equipment.html", {
        "computers": computers,
        "form": form,
        "computer_count": active_computers.count(),
        "repair_spend_xof": sum(item.repair_total_xof for item in computers),
        "replacement_review_count": sum(
            1 for item in computers if item.historical_spend_exceeds_purchase or item.repair_count_last_year >= 3
        ),
    })


@login_required
def equipment_detail_view(request, asset_tag):
    computer = get_object_or_404(
        _managed_computers_for_user(request.user).prefetch_related("interventions"),
        asset_tag=asset_tag,
    )
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "repair":
            form = RepairInterventionForm(request.POST)
            if form.is_valid():
                intervention = form.save(commit=False)
                intervention.computer = computer
                intervention.created_by = request.user
                intervention.save()
                computer.status = ManagedComputer.STATUS_REPAIR
                computer.save(update_fields=["status", "updated_at"])
                messages.success(request, "L’intervention a été ajoutée à l’historique du poste.")
                return redirect("equipment_detail", asset_tag=computer.asset_tag)
        elif action == "preparation":
            fields = ("os_installed", "drivers_installed", "updates_installed", "apps_installed", "security_checked")
            for field in fields:
                setattr(computer, field, request.POST.get(field) == "on")
            checklist_complete = all(getattr(computer, field) for field in fields)
            computer.status = ManagedComputer.STATUS_READY if checklist_complete else ManagedComputer.STATUS_PREPARING
            computer.save(update_fields=[*fields, "status", "updated_at"])
            messages.success(request, "La checklist de préparation a été enregistrée." if not checklist_complete else "Préparation validée : le poste est prêt à être remis.")
            return redirect("equipment_detail", asset_tag=computer.asset_tag)
        elif action == "status":
            allowed = {choice[0] for choice in ManagedComputer.STATUS_CHOICES}
            status = request.POST.get("status")
            if status in allowed:
                computer.status = status
                computer.save(update_fields=["status", "updated_at"])
                messages.success(request, "L’état du poste a été actualisé.")
                return redirect("equipment_detail", asset_tag=computer.asset_tag)
            messages.error(request, "Choisis un état valide pour le poste.")
        elif action == "assessment":
            try:
                replacement_cost = int(request.POST.get("replacement_cost_xof", "0"))
                repair_estimate = int(request.POST.get("next_repair_estimate_xof", "0"))
                if replacement_cost < 0 or repair_estimate < 0:
                    raise ValueError
            except (TypeError, ValueError):
                messages.error(request, "Les montants doivent être des nombres positifs en F CFA.")
            else:
                computer.replacement_cost_xof = replacement_cost
                computer.next_repair_estimate_xof = repair_estimate
                computer.save(update_fields=["replacement_cost_xof", "next_repair_estimate_xof", "updated_at"])
                messages.success(request, "Les coûts de comparaison ont été mis à jour.")
                return redirect("equipment_detail", asset_tag=computer.asset_tag)
        elif action == "associate_device":
            device_id = request.POST.get("licensed_device_id", "").strip()
            if not device_id:
                computer.licensed_device = None
                computer.save(update_fields=["licensed_device", "updated_at"])
                messages.success(request, "L’appareil SystAudit a été dissocié de cette fiche.")
                return redirect("equipment_detail", asset_tag=computer.asset_tag)
            licensed_device = get_object_or_404(
                _license_for_user(request.user).devices,
                pk=device_id,
            )
            if ManagedComputer.objects.filter(licensed_device=licensed_device).exclude(pk=computer.pk).exists():
                messages.error(request, "Cet appareil SystAudit est déjà lié à une autre fiche du parc.")
            else:
                computer.licensed_device = licensed_device
                computer.save(update_fields=["licensed_device", "updated_at"])
                messages.success(request, "L’appareil est associé. Ses nouveaux audits apparaîtront dans cette fiche.")
                return redirect("equipment_detail", asset_tag=computer.asset_tag)
        else:
            messages.error(request, "Action inconnue.")
    else:
        form = RepairInterventionForm()

    interventions = computer.interventions.select_related("created_by")
    audit_reports = (
        AuditReport.objects.filter(device=computer.licensed_device)
        if computer.licensed_device_id else AuditReport.objects.none()
    )
    license_obj = _license_for_user(request.user)
    available_devices = license_obj.devices.filter(
        Q(managed_computer__isnull=True) | Q(pk=computer.licensed_device_id)
    ).order_by("device_id")
    try:
        import qrcode
        import qrcode.image.svg

        qr_image = qrcode.make(
            request.build_absolute_uri(reverse("equipment_detail", kwargs={"asset_tag": computer.asset_tag})),
            image_factory=qrcode.image.svg.SvgPathImage,
        )
        qr_code_data = base64.b64encode(qr_image.to_string(encoding="unicode").encode("utf-8")).decode("ascii")
    except ImportError:
        qr_code_data = ""
    return render(request, "accounts/equipment_detail.html", {
        "computer": computer,
        "status_choices": ManagedComputer.STATUS_CHOICES,
        "qr_code_data": qr_code_data,
        "interventions": interventions,
        "audit_reports": audit_reports,
        "available_devices": available_devices,
        "audit_command": (
            f"$env:SYSAUDIT_API_URL = '{request.build_absolute_uri('/').rstrip('/')}'\n"
            ".\\.venv\\Scripts\\python.exe -m src.audit --upload"
        ),
        "repair_form": form if request.method == "POST" and request.POST.get("action") == "repair" else RepairInterventionForm(),
        "preparation_steps": [
            (computer.os_installed, "os_installed", "Système installé"),
            (computer.drivers_installed, "drivers_installed", "Pilotes installés"),
            (computer.updates_installed, "updates_installed", "Mises à jour terminées"),
            (computer.apps_installed, "apps_installed", "Logiciels professionnels installés"),
            (computer.security_checked, "security_checked", "Contrôles de sécurité effectués"),
        ],
    })


def _report_findings(report):
    recommendation_items = report.recommendations if isinstance(report.recommendations, list) else []
    findings = report.findings if isinstance(report.findings, list) else []
    result = []
    for index, item in enumerate(findings):
        if isinstance(item, dict):
            finding = item
        else:
            finding = {"title": "Constat", "message": str(item), "risk": "low"}
        category = finding.get("category")
        recommendation = None
        for candidate in recommendation_items:
            if isinstance(candidate, dict) and candidate.get("category") == category:
                recommendation = candidate.get("recommendation") or candidate.get("message")
                break
        if recommendation is None and index < len(recommendation_items):
            candidate = recommendation_items[index]
            recommendation = (
                candidate.get("recommendation") or candidate.get("message")
                if isinstance(candidate, dict) else str(candidate)
            )
        result.append({
            "title": finding.get("title") or finding.get("category") or "Constat",
            "message": finding.get("message") or finding.get("description") or finding.get("reason") or str(finding),
            "severity": str(finding.get("risk") or finding.get("severity") or "low").upper(),
            "recommendation": recommendation or "Examiner ce constat et valider la correction avec le responsable informatique.",
        })
    return result


@login_required
def equipment_audit_report_view(request, asset_tag, report_id):
    computer = get_object_or_404(
        _managed_computers_for_user(request.user).select_related("licensed_device"),
        asset_tag=asset_tag,
    )
    if not computer.licensed_device_id:
        return redirect("equipment_detail", asset_tag=computer.asset_tag)
    report = get_object_or_404(
        AuditReport,
        pk=report_id,
        device=computer.licensed_device,
    )
    return render(request, "accounts/equipment_audit_report.html", {
        "computer": computer,
        "report": report,
        "findings": _report_findings(report),
        "organization_name": computer.workspace.name if computer.workspace_id else request.user.get_full_name() or request.user.username,
    })


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
    email = request.POST.get("email", "").strip().casefold()
    try:
        validate_email(email)
    except ValidationError:
        messages.error(request, "Saisissez une adresse e-mail valide pour envoyer l'invitation.")
        return redirect("dashboard")

    if request.user.email and request.user.email.casefold() == email:
        messages.error(request, "Vous êtes déjà propriétaire de cet espace.")
        return redirect("dashboard")

    member = User.objects.filter(email__iexact=email).first()
    if member and not member.is_active:
        messages.error(request, "Cette adresse est associée à un compte qui n'a pas encore confirmé son inscription.")
        return redirect("dashboard")
    if member and hasattr(member, "workspace_membership") and member.workspace_membership.workspace_id == membership.workspace_id:
        messages.error(request, "Cette personne fait déjà partie de votre équipe.")
        return redirect("dashboard")
    if member and hasattr(member, "workspace_membership"):
        messages.error(request, "Ce compte est déjà membre d'un espace d'équipe.")
        return redirect("dashboard")

    now = timezone.now()
    invitation = WorkspaceInvitation.objects.filter(
        workspace=membership.workspace,
        email__iexact=email,
        accepted_at__isnull=True,
        expires_at__gt=now,
    ).first()
    if invitation is None:
        invitation = WorkspaceInvitation.objects.create(
            workspace=membership.workspace,
            email=email,
            invited_by=request.user,
            expires_at=now + timedelta(days=7),
        )
    else:
        invitation.invited_by = request.user
        invitation.expires_at = now + timedelta(days=7)
        invitation.save(update_fields=["invited_by", "expires_at"])

    invitation_url = request.build_absolute_uri(
        reverse("accept_workspace_invitation", kwargs={"token": invitation.token})
    )
    try:
        send_mail(
            subject=f"Invitation à rejoindre {membership.workspace.name} sur SystAudit",
            message=(
                f"Bonjour,\n\n{request.user.get_full_name() or request.user.username} "
                f"vous invite à rejoindre l'espace d'équipe « {membership.workspace.name} » sur SystAudit.\n\n"
                f"Connectez-vous avec cette adresse e-mail pour accepter l'invitation :\n{invitation_url}\n\n"
                "Cette invitation expire dans 7 jours. Si vous ne la reconnaissez pas, ignorez ce message."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception:
        messages.error(request, "L'invitation a été créée, mais l'envoi du courriel a échoué. Vérifiez la configuration e-mail et réessayez.")
        return redirect("dashboard")

    if _email_uses_console():
        messages.success(request, f"Invitation créée pour {email}. En mode local, le courriel et son lien sont affichés dans la fenêtre PowerShell du serveur.")
    else:
        messages.success(request, f"Invitation envoyée à {email}. Cette personne rejoindra l'équipe après avoir confirmé l'invitation par e-mail.")
    return redirect("dashboard")


def accept_workspace_invitation_view(request, token):
    invitation = get_object_or_404(
        WorkspaceInvitation.objects.select_related("workspace", "invited_by"),
        token=token,
    )
    state = "ready"
    if invitation.accepted_at:
        state = "accepted"
    elif invitation.expires_at <= timezone.now():
        state = "expired"
    elif request.user.is_authenticated:
        if not request.user.email or request.user.email.casefold() != invitation.email.casefold():
            state = "wrong_account"
        elif hasattr(request.user, "workspace_membership"):
            state = "already_member"
    else:
        state = "sign_in"

    if request.method == "POST":
        if not request.user.is_authenticated:
            login_url = f"{reverse('login')}?next={reverse('accept_workspace_invitation', kwargs={'token': token})}"
            return redirect(login_url)
        if state != "ready":
            return render(request, "accounts/workspace_invitation.html", {"invitation": invitation, "state": state})
        try:
            with transaction.atomic():
                locked_invitation = WorkspaceInvitation.objects.select_for_update().get(pk=invitation.pk)
                if locked_invitation.accepted_at or locked_invitation.expires_at <= timezone.now():
                    state = "expired" if locked_invitation.expires_at <= timezone.now() else "accepted"
                elif locked_invitation.email.casefold() != request.user.email.casefold():
                    state = "wrong_account"
                elif WorkspaceMembership.objects.filter(user=request.user).exists():
                    state = "already_member"
                else:
                    WorkspaceMembership.objects.create(
                        workspace=locked_invitation.workspace,
                        user=request.user,
                        role=WorkspaceMembership.MEMBER,
                    )
                    locked_invitation.accepted_at = timezone.now()
                    locked_invitation.save(update_fields=["accepted_at"])
                    messages.success(request, f"Vous avez rejoint l'équipe {locked_invitation.workspace.name}.")
                    return redirect("dashboard")
        except IntegrityError:
            state = "already_member"

    return render(request, "accounts/workspace_invitation.html", {"invitation": invitation, "state": state})


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
