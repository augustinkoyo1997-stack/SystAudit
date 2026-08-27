import json

from src.report_export import export_report_to_json


def test_export_report_to_json(tmp_path):
    report = {
        "score": 90,
        "summary": {
            "high": 0,
            "medium": 1,
            "low": 0,
        },
        "recommendations": [
            {
                "risk": "medium",
                "reason": "BitLocker désactivé",
                "recommendation": "Activer BitLocker",
            }
        ],
    }

    output_file = tmp_path / "report.json"

    result = export_report_to_json(report, output_file)

    assert result == output_file
    assert output_file.exists()


def test_exported_json_content(tmp_path):
    report = {
        "score": 90,
        "message": "Sécurité système",
    }

    output_file = tmp_path / "report.json"

    export_report_to_json(report, output_file)

    with output_file.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data == report
    assert data["message"] == "Sécurité système"
