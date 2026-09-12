#!/usr/bin/env python3
"""Export the 130 Phase 2 test cases to questions.json / questions.md.

The dataclass definitions in eval/test_cases_multi_area.py are the source of
truth; this script renders them into a form that's readable without opening
the code (question text, expected keywords, target area).

Note: `level_name` in eval/test_cases_multi_area.py is Japanese (it labels the
actual system-under-test's difficulty tiers). This script maps it to an
English label locally so questions.json/questions.md read in English, without
touching the eval/test code itself.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "eval"))
sys.path.insert(0, str(REPO_ROOT / "src"))

from test_cases_multi_area import ALL_MULTI_AREA_TEST_CASES  # noqa: E402

LEVEL_NAMES_EN = {
    1: "L1 Basic retrieval",
    2: "L2 Spatial reasoning",
    3: "L3 Constraint satisfaction",
    4: "L4 Decision support",
    5: "L5 Advanced reasoning",
}


def to_record(tc):
    return {
        "id": tc.id,
        "level": tc.level,
        "level_name": LEVEL_NAMES_EN.get(tc.level, tc.level_name),
        "category": tc.category,
        "subcategory": tc.subcategory,
        "prompt": tc.prompt,
        "expected_keywords": tc.expected_keywords,
        "difficulty": tc.difficulty,
        "target_area": tc.target_area,
        "target_areas": tc.target_areas,
        "query_type": tc.query_type,
        "description": tc.description,
    }


def main():
    records = [to_record(tc) for tc in ALL_MULTI_AREA_TEST_CASES]

    json_path = REPO_ROOT / "questions.json"
    json_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    md_lines = [
        "# Phase 2 Question List (130 cases)",
        "",
        "Auto-generated from `eval/test_cases_multi_area.py`. See `questions.json` for details.",
        "",
        "Questions are in Japanese, matching what was actually tested "
        "(the RAG systems answer Japanese-language questions about Tokyo POIs).",
        "",
        "| ID | Level | Area | Query Type | Question | Expected Keywords |",
        "|---|---|---|---|---|---|",
    ]
    for r in records:
        area = r["target_area"] or ",".join(r["target_areas"] or []) or "-"
        keywords = ", ".join(r["expected_keywords"])
        prompt = r["prompt"].replace("|", "\\|")
        md_lines.append(
            f"| {r['id']} | {r['level_name']} | {area} | {r['query_type']} | {prompt} | {keywords} |"
        )

    md_path = REPO_ROOT / "questions.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"Wrote {len(records)} questions to {json_path} and {md_path}")


if __name__ == "__main__":
    main()
