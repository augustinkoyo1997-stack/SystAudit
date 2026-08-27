import json
from pathlib import Path


def export_report_to_json(report, output_file="sysaudit_report.json"):
    """Export a SystAudit report to a JSON file."""

    output_path = Path(output_file)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    return output_path
