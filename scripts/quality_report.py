import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "crisisprocure.db"


def _fetch_rows(query: str, params: tuple = ()):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(query, params)
        return cursor.fetchall()


def decision_quality() -> dict:
    rows = _fetch_rows("SELECT decision FROM risk_runs")
    total = len(rows)
    if total == 0:
        return {"total_evaluations": 0}
    counts = {"auto_approve": 0, "supervisor_review": 0, "human_review": 0}
    for (decision,) in rows:
        counts[decision] = counts.get(decision, 0) + 1
    human_rate = counts["human_review"] / total
    return {
        "total_evaluations": total,
        "distribution": counts,
        "human_review_rate": round(human_rate, 3),
        "over_trigger_warning": human_rate > 0.55,
    }


def fairness_quality() -> dict:
    rows = _fetch_rows("SELECT fairness_report FROM prioritization_runs ORDER BY id DESC LIMIT 50")
    if not rows:
        return {"evaluated_batches": 0}

    flagged = 0
    department_scores: dict[str, list[float]] = {}
    for (report_json,) in rows:
        report = json.loads(report_json)
        if report.get("flagged"):
            flagged += 1
        for dept, score in report.get("departments", {}).items():
            department_scores.setdefault(dept, []).append(score)

    avg_by_dept = {
        dept: round(sum(vals) / len(vals), 3) for dept, vals in department_scores.items() if vals
    }
    repeated_high = [d for d, s in avg_by_dept.items() if s >= 0.75]

    return {
        "evaluated_batches": len(rows),
        "flagged_batches": flagged,
        "flagged_ratio": round(flagged / len(rows), 3),
        "average_score_by_department": avg_by_dept,
        "departments_repeatedly_high": repeated_high,
    }


def resilience_quality() -> dict:
    risk_rows = _fetch_rows("SELECT COUNT(*) FROM risk_runs")
    prio_rows = _fetch_rows("SELECT COUNT(*) FROM prioritization_runs")
    return {
        "audit_history_enabled": DB_PATH.exists(),
        "risk_runs_recorded": risk_rows[0][0] if risk_rows else 0,
        "prioritization_runs_recorded": prio_rows[0][0] if prio_rows else 0,
        "rollback_capability": "available via /policy/history and /policy/rollback once configured",
    }


def main() -> int:
    if not DB_PATH.exists():
        print("No database found yet. Run services and execute a few requests first.")
        return 1

    report = {
        "decision_quality": decision_quality(),
        "fairness_quality": fairness_quality(),
        "resilience_quality": resilience_quality(),
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
