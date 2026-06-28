from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "LICENSE",
    "docs/DEVPOST_SUBMISSION.md",
    "docs/PROJECT_STORY.md",
    "docs/MAESTRO_EVIDENCE_CAPTURE.md",
    "docs/CODING_AGENTS_BONUS_PROOF.md",
    "docs/TRACK2_FINAL_READINESS.md",
    "bpmn/order_to_cash_mvp.md",
    "services/exception_agent/app.py",
    "services/collections_agent/app.py",
    "ui/control_center.html",
    "ui/index.html",
]

MANUAL_REQUIRED = [
    "Automation Cloud Maestro run evidence captured (happy + exception paths)",
    "Demo video link inserted in docs/DEVPOST_SUBMISSION.md",
    "Presentation deck link inserted in docs/DEVPOST_SUBMISSION.md",
    "Devpost page fields finalized and aligned to Track 2 wording",
]


def check_files() -> dict:
    present = []
    missing = []
    for rel in REQUIRED_FILES:
        if (ROOT / rel).exists():
            present.append(rel)
        else:
            missing.append(rel)
    return {"present": present, "missing": missing}


def check_readme_keywords() -> dict:
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    keywords = [
        "UiPath Maestro BPMN",
        "UiPath Automation Cloud",
        "policy",
        "fairness",
        "rollback",
        "control_center",
    ]
    keywords_lower = [k.lower() for k in keywords]
    found = [k for k in keywords_lower if k in readme]
    missing = [k for k in keywords_lower if k not in readme]
    return {"found": found, "missing": missing}


def main() -> int:
    file_check = check_files()
    keyword_check = check_readme_keywords()

    report = {
        "file_check": {
            "present_count": len(file_check["present"]),
            "missing_count": len(file_check["missing"]),
            "missing_files": file_check["missing"],
        },
        "readme_keyword_check": {
            "found_count": len(keyword_check["found"]),
            "missing_count": len(keyword_check["missing"]),
            "missing_keywords": keyword_check["missing"],
        },
        "manual_required": MANUAL_REQUIRED,
        "status": "PASS" if not file_check["missing"] and not keyword_check["missing"] else "WARN",
    }

    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
