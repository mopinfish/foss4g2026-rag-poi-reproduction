"""Smoke tests covering everything that can be verified without a GPU/LLM.

The notebooks themselves (loading and running inference with Qwen2.5-7B-Instruct)
require a GPU, so this suite instead verifies that the code and data the
notebooks depend on are not broken:

Phase 2 (4-area, 130-case):
- The 130 test cases load and match the expected count
- The 4 per-area POI JSON files parse and concatenate to the combined set
- geo_utils / aggregator spatial calculations work
- GraphRAGSystem (no LLM required) builds a POI graph and answers a real query
- evaluators_multi_area.MultiAreaEvaluator runs to completion with a dummy system_fn

Phase 1 (Shibuya-only, 90-case):
- The 55 Structured-RAG-oriented and 35 GraphRAG-oriented test cases load
  and match the expected counts, with no duplicate IDs
"""
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "eval"))

AREAS = ["shibuya", "shinjuku", "ikebukuro", "tokyo"]


@pytest.fixture(scope="module")
def flat_pois():
    from geo_utils import STATIONS

    areas_config = {
        "shibuya": {"name": "渋谷駅周辺", "station": STATIONS["渋谷駅"]},
        "shinjuku": {"name": "新宿駅周辺", "station": STATIONS["新宿駅"]},
        "ikebukuro": {"name": "池袋駅周辺", "station": STATIONS["池袋駅"]},
        "tokyo": {"name": "東京駅周辺", "station": STATIONS["東京駅"]},
    }
    raw_pois = []
    for area_key in areas_config:
        with open(REPO_ROOT / "data" / f"poi_{area_key}.json", encoding="utf-8") as f:
            raw_pois.extend(json.load(f))

    flat = [p["metadata"].copy() if "metadata" in p else p for p in raw_pois]
    return areas_config, flat


def test_poi_data_loads_and_matches_expected_total(flat_pois):
    _, flat = flat_pois
    assert len(flat) == 3567

    counts = {}
    for poi in flat:
        counts[poi.get("area_key", "unknown")] = counts.get(poi.get("area_key"), 0) + 1
    assert set(counts.keys()) == set(AREAS)


def test_geo_utils_enrich_all_areas(flat_pois):
    from geo_utils import enrich_all_areas

    areas_config, flat = flat_pois
    enriched = enrich_all_areas(flat, areas_config)
    assert len(enriched) == len(flat)
    sample = enriched[0]
    assert "distance_from_station" in sample


def test_130_multi_area_test_cases_load():
    from test_cases_multi_area import ALL_MULTI_AREA_TEST_CASES

    assert len(ALL_MULTI_AREA_TEST_CASES) == 130
    ids = [tc.id for tc in ALL_MULTI_AREA_TEST_CASES]
    assert len(ids) == len(set(ids)), "duplicate test case ids"


def test_graph_rag_system_answers_without_gpu(flat_pois):
    """GraphRAGSystem needs no LLM, so it can answer a real query even without a GPU."""
    from geo_utils import enrich_all_areas
    from graph_rag_system import GraphRAGSystem

    areas_config, flat = flat_pois
    enriched = enrich_all_areas(flat, areas_config)

    system = GraphRAGSystem(areas_config=areas_config, all_pois=enriched)
    assert len(system.graphs) == len(AREAS)

    result = system.query("渋谷駅から一番近いカフェは？")
    assert result.context
    assert isinstance(result.context, str)


def test_multi_area_evaluator_runs_with_dummy_system(flat_pois):
    from evaluators_multi_area import MultiAreaEvaluator
    from geo_utils import enrich_all_areas
    from test_cases_multi_area import get_quick_test_cases

    areas_config, flat = flat_pois
    enriched = enrich_all_areas(flat, areas_config)

    evaluator = MultiAreaEvaluator(areas_config=areas_config, all_pois=enriched)
    quick_cases = get_quick_test_cases()
    assert len(quick_cases) > 0

    def dummy_system_fn(question: str) -> dict:
        return {"answer": f"dummy answer for: {question}", "detected_area": None}

    results = evaluator.evaluate_all(
        system_name="dummy", system_fn=dummy_system_fn, test_cases=quick_cases
    )
    assert len(results) == len(quick_cases)

    summary = evaluator.generate_summary(results)
    assert "overall" in summary


def test_phase1_test_cases_load():
    from test_cases_v2 import TEST_CASES_V2
    from test_cases_graphrag import GRAPHRAG_TEST_CASES

    assert len(TEST_CASES_V2) == 55
    assert len(GRAPHRAG_TEST_CASES) == 35

    all_ids = [tc.id for tc in TEST_CASES_V2] + [tc.id for tc in GRAPHRAG_TEST_CASES]
    assert len(all_ids) == len(set(all_ids)), "duplicate test case ids across Phase 1 sets"
