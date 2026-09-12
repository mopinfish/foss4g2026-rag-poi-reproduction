#!/usr/bin/env python3
"""Phase 2 の130件テストケースを questions.json / questions.md に書き出す。

eval/test_cases_multi_area.py の dataclass 定義を正本とし、
コードを読まなくても質問内容・期待キーワード・対象エリアが分かる形式にする。
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "eval"))
sys.path.insert(0, str(REPO_ROOT / "src"))

from test_cases_multi_area import ALL_MULTI_AREA_TEST_CASES  # noqa: E402


def to_record(tc):
    return {
        "id": tc.id,
        "level": tc.level,
        "level_name": tc.level_name,
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
        "# Phase 2 質問リスト（130件）",
        "",
        "`eval/test_cases_multi_area.py` から自動生成。詳細は `questions.json` を参照。",
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
