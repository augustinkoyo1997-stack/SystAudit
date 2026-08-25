from src.security_analysis import analyze_security
from src.security_analysis import calculate_security_score
from src.security_recommendations import generate_recommendations
from src.security_report import generate_security_report


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