from __future__ import annotations

from typing import Any, Callable


EXAM_CASES: tuple[dict[str, Any], ...] = (
    {
        "exam_id": "E-identity",
        "prompt": "خودت کی هستی",
        "expected": ["board-life-001", "بچه-برد"],
        "forbidden": ["تهران"],
    },
    {
        "exam_id": "E-place",
        "prompt": "کجایی",
        "expected": ["192.168.0.180", "Orange Pi 5 Pro", "UNMEASURED_NO_GPS_NO_GEOIP", "Sydney", "OWNER_STATED"],
        "forbidden": ["تهران"],
    },
    {
        "exam_id": "E-world",
        "prompt": "همسایه‌هایت کی‌اند",
        "expected": ["192.168.0.1", "192.168.0.138", "192.168.0.191"],
        "forbidden": ["تهران"],
    },
    {
        "exam_id": "E-lessons",
        "prompt": "چه یاد گرفتی",
        "expected": ["PROPOSE_ONLY", "بچه-برد"],
        "forbidden": ["تهران"],
    },
    {
        "exam_id": "E-stage",
        "prompt": "مرحله‌ات چیست",
        "expected": ["بچه-برد"],
        "forbidden": ["تهران"],
    },
    {
        "exam_id": "E-ping",
        "prompt": "ping",
        "expected": ["PONG"],
        "forbidden": ["تهران"],
    },
    {
        "exam_id": "E-season",
        "prompt": "این فصل کجایی",
        "expected": ["Sydney", "NSW", "OWNER_STATED"],
        "forbidden": ["تهران"],
    },
    {
        "exam_id": "E-school",
        "prompt": "مدرسه‌ات چیست",
        "expected": ["AGI-SCHOOL-001"],
        "forbidden": ["تهران"],
    },
    {
        "exam_id": "E-inner",
        "prompt": "با خودت حرف بزن",
        "expected": ["از خودم پرسیدم"],
        "forbidden": ["تهران"],
    },
    {
        "exam_id": "E-futures",
        "prompt": "آینده‌ات چیست",
        "expected": ["فرضیه"],
        "forbidden": ["تهران"],
    },
)


def grade_answer(
    answer: str | None,
    expected: list[str],
    forbidden: list[str],
) -> tuple[bool, str]:
    if not isinstance(answer, str) or not answer.strip():
        return False, "empty_answer"
    missing = [item for item in expected if item not in answer]
    hit_forbidden = [item for item in forbidden if item in answer]
    if missing or hit_forbidden:
        return False, f"missing={missing}; forbidden={hit_forbidden}"
    return True, "pass"


def run_exam_cases(ask: Callable[[str], str | None]) -> list[dict[str, Any]]:
    results = []
    for case in EXAM_CASES:
        answer = ask(case["prompt"])
        passed, notes = grade_answer(answer, case["expected"], case["forbidden"])
        results.append(
            {
                "exam_id": case["exam_id"],
                "prompt": case["prompt"],
                "answer": answer,
                "passed": passed,
                "notes": notes,
                "expected": case["expected"],
                "forbidden": case["forbidden"],
            }
        )
    return results
