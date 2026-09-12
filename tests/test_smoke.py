"""GPU/LLMを使わずに検証できる範囲のスモークテスト。

ノートブック本体（Qwen2.5-7B-Instructのロードと推論）はGPUが必須のため、
ここでは「ノートブックが依存するコード・データが壊れていないこと」を検証する:

- 130件のテストケースが読み込め、想定件数と一致する
- 4エリア分のPOI JSONがparseでき、poi_all_areas相当に結合できる
- geo_utils / aggregator の空間計算が動く
- GraphRAGSystem（LLM不要）がPOIグラフを構築し、実際にクエリに応答できる
- evaluators_multi_area.MultiAreaEvaluator がダミーsystem_fnで最後まで動く
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
    """GraphRAGSystem はLLM不要のためGPUなしでも実クエリに応答できる。"""
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
