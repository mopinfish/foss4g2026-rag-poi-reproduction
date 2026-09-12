#!/usr/bin/env python3
"""Export the 90 Phase 1 test cases (55 Structured + 35 GraphRAG) to
questions_phase1.json / questions_phase1.md.

Source of truth: eval/test_cases_v2.py (TEST_CASES_V2) and
eval/test_cases_graphrag.py (GRAPHRAG_TEST_CASES).

Note: `level_name` for the 55 Structured-RAG-oriented cases is mapped to an
English label locally (same approach as scripts/export_questions.py), without
touching the eval/test code. The 35 GraphRAG-oriented cases have no level
field in the source data (they were designed to probe specific graph-relation
categories, not the L1-L5 difficulty ladder).
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "eval"))

from test_cases_v2 import TEST_CASES_V2  # noqa: E402
from test_cases_graphrag import GRAPHRAG_TEST_CASES  # noqa: E402

LEVEL_NAMES_EN = {
    1: "L1 Basic retrieval",
    2: "L2 Spatial reasoning",
    3: "L3 Constraint satisfaction",
    4: "L4 Decision support",
    5: "L5 Advanced reasoning",
}


def structured_record(tc):
    return {
        "id": tc.id,
        "source": "structured",
        "level": tc.level,
        "level_name": LEVEL_NAMES_EN.get(tc.level),
        "category": tc.category,
        "subcategory": tc.subcategory,
        "prompt": tc.prompt,
        "expected_keywords": tc.expected_keywords,
        "difficulty": tc.difficulty,
        "description": tc.description,
    }


def graphrag_record(tc):
    return {
        "id": tc.id,
        "source": "graphrag",
        "level": None,
        "level_name": None,
        "category": tc.category,
        "subcategory": None,
        "prompt": tc.question,
        "expected_keywords": tc.expected_keywords,
        "difficulty": None,
        "description": None,
    }


def main():
    records = [structured_record(tc) for tc in TEST_CASES_V2]
    records += [graphrag_record(tc) for tc in GRAPHRAG_TEST_CASES]

    json_path = REPO_ROOT / "questions_phase1.json"
    json_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    md_lines = [
        "# Phase 1 Question List (90 cases: 55 Structured + 35 GraphRAG)",
        "",
        "Auto-generated from `eval/test_cases_v2.py` and `eval/test_cases_graphrag.py`. "
        "See `questions_phase1.json` for details.",
        "",
        "Questions are in Japanese, matching what was actually tested "
        "(the RAG systems answer Japanese-language questions about Shibuya POIs).",
        "",
        "See `docs/phase1_vs_phase2_test_design.md` for how these Phase 1 questions compare "
        "to Phase 2's, particularly at L4/L5.",
        "",
        "| ID | Source | Level | Category | Question | Expected Keywords |",
        "|---|---|---|---|---|---|",
    ]
    for r in records:
        level = r["level_name"] or "-"
        keywords = ", ".join(r["expected_keywords"])
        prompt = r["prompt"].replace("|", "\\|")
        md_lines.append(
            f"| {r['id']} | {r['source']} | {level} | {r['category']} | {prompt} | {keywords} |"
        )

    md_path = REPO_ROOT / "questions_phase1.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"Wrote {len(records)} questions to {json_path} and {md_path}")


if __name__ == "__main__":
    main()
