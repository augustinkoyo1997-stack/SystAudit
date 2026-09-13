from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from .models import RemediationRequest

from src.remediation_factory import create_remediation_from_finding
from src.remediation_engine import RemediationEngine
from src.bitlocker_engine import execute_bitlocker_plan_for_engine
from src.bitlocker_plan_factory import create_bitlocker_plans
from src.bitlocker_remediation import analyze_bitlocker_state


@login_required
@require_POST
def approve_remediation_request(request, request_id):
    remediation_request = get_object_or_404(
        RemediationRequest,
        pk=request_id,
    )

    remediation_request.approve()

    return redirect("dashboard")


@login_required
@require_POST
def execute_remediation_request(request, request_id):
    remediation_request = get_object_or_404(
        RemediationRequest,
        pk=request_id,
    )

    # Une remÃ©diation doit obligatoirement Ãªtre approuvÃ©e
    # avant de pouvoir Ãªtre exÃ©cutÃ©e.
    if remediation_request.status != RemediationRequest.APPROVED:
        return redirect("dashboard")

    # Pour le moment, seule l'exÃ©cution DRY-RUN est autorisÃ©e.
    # Toute tentative REAL est bloquÃ©e cÃ´tÃ© serveur.
    if remediation_request.execution_mode != RemediationRequest.DRY_RUN:
        remediation_request.start_execution()

        remediation_request.mark_failed(
            "Real remediation execution is currently disabled."
        )

        return redirect("dashboard")

    try:
        # Reconstruire le finding Ã  partir de la demande Django.
        remediation_code = (
            remediation_request.remediation_id
            .replace("REM-", "")
            .lower()
        )

        if remediation_code.startswith("bitlocker-"):
            category = "bitlocker"
        else:
            category = remediation_code

        finding = {
            "risk": remediation_request.severity,
            "category": category,
            "message": remediation_request.description,
        }

        # CrÃ©er la remÃ©diation contrÃ´lÃ©e.
        remediation = create_remediation_from_finding(
            finding
        )

        # L'approbation Django doit Ãªtre propagÃ©e
        # vers l'objet Remediation.
        remediation.approve()

        # Passage APPROVED -> EXECUTING
        remediation_request.start_execution()

        # ExÃ©cution contrÃ´lÃ©e :
        # execute -> verify -> rollback si nÃ©cessaire.
        #
        # BitLocker utilise un handler spÃ©cialisÃ©.
        if category == "bitlocker":
            diagnostic = analyze_bitlocker_state()
            plans = create_bitlocker_plans(diagnostic)

            if not plans:
                remediation_request.mark_failed(
                    "No safe BitLocker remediation plan is available."
                )
                return redirect("dashboard")

            # Pour cette phase, nous exÃ©cutons uniquement un DRY-RUN.
            target_volume = remediation_request.target_volume

            plan = next(
                (
                    current_plan
                    for current_plan in plans
                    if current_plan.volume == target_volume
                ),
                None,
            )

            if plan is None:
                remediation_request.mark_failed(
                    f"No BitLocker remediation plan found for "
                    f"{target_volume or 'the requested volume'}."
                )
                return redirect("dashboard")

            plan.approve()
            plan.execution_allowed = True

            execution_state = {
                "success": False,
            }

            def bitlocker_handler(current_remediation):
                result = execute_bitlocker_plan_for_engine(
                    current_remediation,
                    plan,
                    dry_run=(
                        remediation_request.execution_mode
                        == RemediationRequest.DRY_RUN
                    ),
                )

                execution_state["success"] = result.success

                return result

            remediation.verify_action = (
                lambda: execution_state["success"]
            )

            engine = RemediationEngine(
                remediation,
                execution_handler=bitlocker_handler,
            )

        else:
            engine = RemediationEngine(remediation)

        result = engine.run()

        # RÃ©cupÃ©rer le message rÃ©el produit par le moteur.
        result_message = getattr(
            result,
            "message",
            "",
        )

        # SuccÃ¨s uniquement si l'exÃ©cution ET
        # la vÃ©rification ont rÃ©ussi.
        if engine.state == RemediationEngine.VERIFIED:
            remediation_request.mark_success(
                result_message
                or "Remediation executed and verified successfully."
            )

        # Si la vÃ©rification Ã©choue et que le rollback
        # rÃ©ussit, on conserve la trace du rollback.
        elif engine.state == RemediationEngine.ROLLED_BACK:
            remediation_request.mark_failed(
                result_message
                or "Remediation verification failed and rollback was performed."
            )
            remediation_request.rollback()

        else:
            remediation_request.mark_failed(
                result_message
                or f"Remediation failed with engine state: {engine.state}"
            )

    except PermissionError as exc:
        if remediation_request.status == RemediationRequest.EXECUTING:
            remediation_request.mark_failed(
                str(exc) or "Administrator privileges are required."
            )

    except Exception as exc:
        if remediation_request.status == RemediationRequest.EXECUTING:
            remediation_request.mark_failed(
                str(exc) or "Unexpected remediation execution error."
            )

    return redirect("dashboard")
