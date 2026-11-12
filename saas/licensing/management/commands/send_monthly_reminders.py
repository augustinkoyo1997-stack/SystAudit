"""Rappel mensuel : prévient les propriétaires dont des postes n'ont pas été audités récemment.

À planifier une fois par mois (cron, planificateur de tâches, ou tâche cloud) :
    python manage.py send_monthly_reminders
"""

from collections import defaultdict
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from licensing.alerts import device_label
from licensing.models import LicensedDevice


class Command(BaseCommand):
    help = "Envoie un rappel d'audit pour les postes sans audit récent."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30, help="Ancienneté maximale du dernier audit.")
        parser.add_argument("--dry-run", action="store_true", help="Affiche sans envoyer d'e-mail.")

    def handle(self, *args, **options):
        limit = timezone.now() - timedelta(days=options["days"])
        stale_by_owner = defaultdict(list)

        devices = LicensedDevice.objects.select_related("license__user").filter(
            license__is_active=True,
            license__user__is_active=True,
        )
        for device in devices:
            latest = device.audit_reports.order_by("-created_at").first()
            last_date = latest.created_at if latest else None
            if last_date is None or last_date < limit:
                stale_by_owner[device.license.user].append((device, last_date))

        sent = 0
        for owner, items in stale_by_owner.items():
            if not owner.email:
                continue
            lines = []
            for device, last_date in items:
                when = last_date.strftime("%d/%m/%Y") if last_date else "jamais audité"
                lines.append(f"- {device_label(device)} (dernier audit : {when})")
            body = (
                "Bonjour,\n\nLes postes suivants n'ont pas été audités récemment :\n\n"
                + "\n".join(lines)
                + "\n\nLancez un audit sur chacun d'eux pour garder un suivi à jour.\n"
                "Ce message est automatique.\n"
            )
            if options["dry_run"]:
                self.stdout.write(f"[SIMULATION] {owner.email} : {len(items)} poste(s)")
                continue
            send_mail(
                subject="[SystAudit] Rappel mensuel d'audit",
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[owner.email],
                fail_silently=False,
            )
            sent += 1

        self.stdout.write(f"{sent} rappel(s) envoyé(s).")
