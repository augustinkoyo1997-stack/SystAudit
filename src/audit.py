from src.security_analysis import analyze_security
from src.security_analysis import calculate_security_score
from src.security_recommendations import generate_recommendations
from src.security_report import generate_security_report
from src.report_export import export_report_to_json
from src.license_guard import check_license
from src.license_client import submit_audit_report

def run_security_audit():
    """Run a complete security audit and return the final report."""

    findings = analyze_security()

    score = calculate_security_score(findings)

    recommendations = generate_recommendations(findings)

    report = generate_security_report(
        findings,
        recommendations,
        score,
    )

    return report


def run_and_export_security_audit(output_file="sysaudit_report.json"):
    """Run a security audit and export the report to JSON."""

    report = run_security_audit()

    export_report_to_json(report, output_file)

    return report


def print_security_report(report):
    """Print a security report in a human-readable format."""

    print("=" * 40)
    print("        SYSAUDIT REPORT")
    print("=" * 40)

    print(f"\nSecurity Score : {report['score']}/100")

    summary = report["summary"]

    print("\nFindings")
    print("--------")
    print(f"HIGH   : {summary['high']}")
    print(f"MEDIUM : {summary['medium']}")
    print(f"LOW    : {summary['low']}")

    print("\nRecommendations")
    print("---------------")

    if not report["recommendations"]:
        print("No recommendations.")
    else:
        for recommendation in report["recommendations"]:
            print(
                f"[{recommendation['risk'].upper()}] "
                f"{recommendation['reason']}"
            )
            print(
                f"       → {recommendation['recommendation']}"
            )

    print("\n" + "=" * 40)


def run_protected_audit(license_key, output_file="sysaudit_report.json"):
    """Run, export and submit a security audit if the license is valid."""

    license_result = check_license(
        license_key,
        activate=True,
    )

    if not license_result.get("allowed", False):
        print("License validation failed.")
        print(
            f"Reason : "
            f"{license_result.get('reason', 'Invalid license.')}"
        )
        return None

    report = run_security_audit()

    export_report_to_json(report, output_file)

    device_id = license_result.get("device_id")

    if not device_id:
        print("Audit report submission skipped.")
        print("Reason : Device ID is unavailable.")
        return report

    submission = submit_audit_report(
        license_key,
        device_id,
        report,
    )

    if not submission.get("saved", False):
        print("Audit report submission failed.")
        print(
            f"Reason : "
            f"{submission.get('error', 'Unknown error.')}"
        )
        return report

    print(
        "Audit report submitted successfully. "
        f"Report ID : {submission.get('report_id')}"
    )

    return report


if __name__ == "__main__":
    report = run_and_export_security_audit()
    print_security_report(report)
