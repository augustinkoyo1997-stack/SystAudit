import hashlib
import hmac
import json
import time
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from urllib.parse import urlparse

from accounts.models import License
from accounts.views import _license_for_user
from .models import Payment
from .services import FedaPayError, create_payment_link


@login_required
@require_POST
def start_premium_checkout(request):
    try:
        amount = int(getattr(settings, "FEDAPAY_PREMIUM_PRICE_XOF", 0))
    except (TypeError, ValueError):
        amount = 0
    if amount <= 0:
        messages.error(request, "Le tarif Premium n'est pas encore configuré.")
        return redirect("dashboard")

    license_obj = _license_for_user(request.user)
    if license_obj.user_id != request.user.pk:
        messages.error(request, "Seul le responsable de la licence peut gérer son abonnement.")
        return redirect("dashboard")
    payment = Payment.objects.create(user=request.user, license=license_obj, amount_xof=amount)
    callback_url = request.build_absolute_uri(reverse("fedapay_return"))
    try:
        transaction_id, payment_url = create_payment_link(
            email=request.user.email,
            description=f"SystAudit Premium - {request.user.email}",
            amount_xof=amount,
            callback_url=callback_url,
        )
    except FedaPayError as exc:
        payment.status = Payment.FAILED
        payment.save(update_fields=["status", "updated_at"])
        messages.error(request, str(exc))
        return redirect("dashboard")

    parsed_url = urlparse(payment_url)
    hostname = (parsed_url.hostname or "").lower()
    if parsed_url.scheme != "https" or not (hostname == "fedapay.com" or hostname.endswith(".fedapay.com")):
        payment.status = Payment.FAILED
        payment.save(update_fields=["status", "updated_at"])
        messages.error(request, "FedaPay a retourné un lien de paiement invalide.")
        return redirect("dashboard")

    payment.provider_transaction_id = transaction_id
    payment.save(update_fields=["provider_transaction_id", "updated_at"])
    return redirect(payment_url)


def fedapay_return(request):
    return render(request, "billing/payment_pending.html")


def _verify_fedapay_signature(payload, header, secret):
    if not header or not secret:
        return False
    values = {}
    for item in header.split(","):
        key, separator, value = item.strip().partition("=")
        if separator:
            values.setdefault(key, []).append(value)
    try:
        timestamp = int(values.get("t", [""])[0])
    except (TypeError, ValueError, IndexError):
        return False
    if abs(int(time.time()) - timestamp) > 300:
        return False
    expected = hmac.new(
        secret.encode("utf-8"),
        str(timestamp).encode("ascii") + b"." + payload,
        hashlib.sha256,
    ).hexdigest()
    return any(hmac.compare_digest(expected, signature) for signature in values.get("s", []))


@csrf_exempt
@require_POST
def fedapay_webhook(request):
    secret = getattr(settings, "FEDAPAY_WEBHOOK_SECRET", "")
    if not _verify_fedapay_signature(
        request.body,
        request.headers.get("X-FEDAPAY-SIGNATURE", ""),
        secret,
    ):
        return HttpResponse(status=400)
    try:
        event = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return HttpResponse(status=400)

    event_name = event.get("name")
    event_data = event.get("data") or {}
    provider_transaction = event_data.get("transaction", event_data)
    provider_id = provider_transaction.get("id")
    if event_name not in {"transaction.approved", "transaction.canceled"} or not provider_id:
        return JsonResponse({"received": True})

    with transaction.atomic():
        payment = Payment.objects.select_for_update().filter(
            provider_transaction_id=str(provider_id),
        ).first()
        if payment is None:
            return HttpResponse(status=404)
        try:
            amount = int(provider_transaction.get("amount"))
        except (TypeError, ValueError):
            return HttpResponse(status=400)
        if amount != payment.amount_xof:
            return HttpResponse(status=400)
        if payment.status == Payment.APPROVED:
            return JsonResponse({"received": True})

        if event_name == "transaction.canceled":
            payment.status = Payment.CANCELED
            payment.save(update_fields=["status", "updated_at"])
            return JsonResponse({"received": True})

        if str(provider_transaction.get("status", "")).lower() not in {"approved", "transferred"}:
            return HttpResponse(status=400)
        license_obj = License.objects.select_for_update().get(pk=payment.license_id)
        start = license_obj.expires_at if license_obj.expires_at and license_obj.expires_at > timezone.now() else timezone.now()
        license_obj.plan = License.PLAN_PREMIUM
        license_obj.is_active = True
        license_obj.max_devices = max(
            license_obj.max_devices,
            int(getattr(settings, "FEDAPAY_PREMIUM_MAX_DEVICES", 5)),
        )
        license_obj.expires_at = start + timedelta(days=30)
        license_obj.save(update_fields=["plan", "is_active", "max_devices", "expires_at"])
        payment.status = Payment.APPROVED
        payment.save(update_fields=["status", "updated_at"])

    return JsonResponse({"received": True})
