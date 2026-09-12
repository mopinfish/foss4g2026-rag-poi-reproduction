"""
agent_tools.py - Agentic RAG用ツール定義

Phase 9: Agentic RAGシステムで使用するツール群
LangGraphエージェントから呼び出される関数とツール定義

作成日: 2026-02-03
プロジェクト: experiments-local-llm
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.tools import tool

# ローカルモジュール（パッケージ/スクリプト両対応）
try:
    from .geo_utils import (
        get_nearest_pois,
        filter_by_radius,
        count_by_radius,
        compare_by_radius,
        haversine_distance,
        SHIBUYA_STATION,
        STATIONS,
        AREA_STATION_MAP,
        filter_east_side,
        filter_west_side,
        analyze_radius_sensitivity,
        detect_target_area,
    )
    from .aggregator import (
        count_by_category,
        compare_east_west,
        compare_north_south,
        get_top_categories,
        filter_by_category,
        analyze_category_by_direction
    )
except ImportError:
    from geo_utils import (
        get_nearest_pois,
        filter_by_radius,
        count_by_radius,
        compare_by_radius,
        haversine_distance,
        SHIBUYA_STATION,
        STATIONS,
        AREA_STATION_MAP,
        filter_east_side,
        filter_west_side,
        analyze_radius_sensitivity,
        detect_target_area,
    )
    from aggregator import (
        count_by_category,
        compare_east_west,
        compare_north_south,
        get_top_categories,
        filter_by_category,
        analyze_category_by_direction
    )


# =============================================================================
# グローバルPOIデータ（初期化時にセット）
# =============================================================================

_GLOBAL_POIS: List[Dict[str, Any]] = []
_GLOBAL_POIS_BY_AREA: Dict[str, List[Dict[str, Any]]] = {}
_GLOBAL_AREAS_CONFIG: Dict[str, Any] = {}


def set_global_pois(pois: List[Dict[str, Any]]) -> None:
    """
    グローバルPOIデータを設定（後方互換）

    Args:
        pois: POIデータのリスト（空間情報付き）
    """
    global _GLOBAL_POIS
    _GLOBAL_POIS = pois


def set_global_pois_multi_area(
    pois: List[Dict[str, Any]],
    areas_config: Dict[str, Any]
) -> None:
    """
    複数エリアのPOIデータを設定

    Args:
        pois: 全エリアのPOIデータリスト（空間情報付き）
        areas_config: エリア設定辞書
    """
    global _GLOBAL_POIS, _GLOBAL_POIS_BY_AREA, _GLOBAL_AREAS_CONFIG
    _GLOBAL_POIS = pois
    _GLOBAL_AREAS_CONFIG = areas_config
    _GLOBAL_POIS_BY_AREA = {}
    for poi in pois:
        area_key = (poi.get("area_key")
                     or poi.get("metadata", {}).get("area_key", "shibuya"))
        _GLOBAL_POIS_BY_AREA.setdefault(area_key, []).append(poi)


def get_global_pois(area: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    グローバルPOIデータを取得

    Args:
        area: エリアキー。指定時はそのエリアのPOIのみ返す。
              None時は全POIを返す。

    Returns:
        POIリスト
    """
    if area and area in _GLOBAL_POIS_BY_AREA:
        return _GLOBAL_POIS_BY_AREA[area]
    return _GLOBAL_POIS


def _get_area_station(area: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """エリアキーから基準駅情報を取得"""
    if area and area in _GLOBAL_AREAS_CONFIG:
        return _GLOBAL_AREAS_CONFIG[area].get("station")
    if area and area in AREA_STATION_MAP:
        station_name = AREA_STATION_MAP[area]
        return STATIONS.get(station_name)
    return None


# =============================================================================
# ツール出力の日本語自然文変換（中国語混入対策）
# =============================================================================

def format_tool_output_japanese(tool_name: str, output: Any) -> str:
    """
    ツール出力をJSON形式から日本語自然文に変換する

    Phase 9の中国語混入問題への対策。LLMにはJSON構造ではなく
    日本語テキストとしてツール結果を渡す。

    Args:
        tool_name: ツール名
        output: ツール出力（dict or str）

    Returns:
        日本語自然文テキスト
    """
    # 文字列の場合はJSONパースを試みる
    if isinstance(output, str):
        try:
            output = json.loads(output)
        except (json.JSONDecodeError, TypeError):
            return output

    if not isinstance(output, dict):
        return str(output)

    # エラーの場合
    if "error" in output:
        return f"エラー: {output['error']}"

    if tool_name == "tool_get_nearest_pois":
        category = output.get("category", "全て")
        count = output.get("count", 0)
        lines = [f"{category}の検索結果（{count}件）:"]
        for poi in output.get("pois", []):
            name = poi.get("name", "不明")
            direction = poi.get("direction", "不明")
            distance = poi.get("distance_m", "不明")
            if isinstance(distance, (int, float)):
                lines.append(f"  - {name}: 駅から{direction}方向に{distance:.1f}メートル")
            else:
                lines.append(f"  - {name}: 駅から{direction}方向に{distance}メートル")
        return "\n".join(lines)

    elif tool_name == "tool_count_pois_in_radius":
        radius = output.get("radius_m", "不明")
        category = output.get("category", "全て")
        count = output.get("count", 0)
        return f"半径{radius}メートル以内の{category}は{count}件です。"

    elif tool_name == "tool_compare_radius":
        r1 = output.get("radius1_m", "不明")
        r2 = output.get("radius2_m", "不明")
        c1 = output.get("count1", 0)
        c2 = output.get("count2", 0)
        category = output.get("category", "全て")
        diff = output.get("difference", c2 - c1 if isinstance(c1, int) and isinstance(c2, int) else "不明")
        summary = output.get("summary_jp", "")
        if summary:
            return summary
        return (f"{category}の半径比較: {r1}m以内は{c1}件、{r2}m以内は{c2}件"
                f"（差: {diff}件）。")

    elif tool_name == "tool_analyze_sensitivity":
        lines = ["感度分析結果:"]
        if isinstance(output, dict):
            for key, value in output.items():
                if isinstance(value, dict):
                    lines.append(f"  半径{key}: {value}")
                else:
                    lines.append(f"  {key}: {value}")
        return "\n".join(lines)

    elif tool_name == "tool_filter_by_area":
        radius = output.get("radius_m", "不明")
        category = output.get("category", "全て")
        count = output.get("count", 0)
        lines = [f"半径{radius}メートル以内の{category}（{count}件）:"]
        for poi in output.get("pois", [])[:10]:
            name = poi.get("name", "不明")
            distance = poi.get("distance_m", "不明")
            direction = poi.get("direction", "不明")
            lines.append(f"  - {name}: {direction}方向に{distance}メートル")
        return "\n".join(lines)

    elif tool_name == "tool_calculate_distance":
        poi1 = output.get("poi1", {}).get("name", "不明")
        poi2 = output.get("poi2", {}).get("name", "不明")
        distance = output.get("distance_m", "不明")
        return f"{poi1}から{poi2}までの距離は{distance}メートルです。"

    elif tool_name == "tool_compare_east_west":
        category = output.get("category", "全て")
        east = output.get("east_count", 0)
        west = output.get("west_count", 0)
        summary = output.get("summary_jp", "")
        if summary:
            return summary
        return f"{category}の東西比較: 東側{east}件、西側{west}件。"

    elif tool_name == "tool_compare_north_south":
        category = output.get("category", "全て")
        north = output.get("north_count", 0)
        south = output.get("south_count", 0)
        summary = output.get("summary_jp", "")
        if summary:
            return summary
        return f"{category}の南北比較: 北側{north}件、南側{south}件。"

    elif tool_name == "tool_count_by_category":
        lines = ["カテゴリ別集計:"]
        for cat, count in output.items():
            lines.append(f"  - {cat}: {count}件")
        return "\n".join(lines)

    elif tool_name == "tool_get_top_categories":
        top_n = output.get("top_n", 5)
        lines = [f"カテゴリランキング（上位{top_n}件）:"]
        for cat_info in output.get("categories", []):
            rank = cat_info.get("rank", "")
            category = cat_info.get("category", "不明")
            count = cat_info.get("count", 0)
            lines.append(f"  {rank}位: {category}（{count}件）")
        return "\n".join(lines)

    elif tool_name == "tool_analyze_category_by_direction":
        lines = ["方向別分析:"]
        for key, value in output.items():
            lines.append(f"  {key}: {value}")
        return "\n".join(lines)

    elif tool_name == "tool_vector_search":
        query = output.get("query", "")
        count = output.get("count", 0)
        lines = [f"「{query}」の検索結果（{count}件）:"]
        for poi in output.get("pois", []):
            name = poi.get("name", "不明")
            category = poi.get("category", "不明")
            lines.append(f"  - {name}（{category}）")
        return "\n".join(lines)

    elif tool_name == "tool_find_pois_by_keyword":
        keyword = output.get("keyword", "")
        count = output.get("count", 0)
        lines = [f"「{keyword}」のキーワード検索結果（{count}件）:"]
        for poi in output.get("pois", [])[:10]:
            name = poi.get("name", "不明")
            category = poi.get("category", "不明")
            lines.append(f"  - {name}（{category}）")
        return "\n".join(lines)

    elif tool_name == "tool_find_nearby_similar_pois":
        origin = output.get("origin_poi", "不明")
        count = output.get("count", 0)
        lines = [f"{origin}の近くにある同カテゴリPOI（{count}件）:"]
        for poi in output.get("nearby_pois", []):
            name = poi.get("name", "不明")
            distance = poi.get("distance_m", "不明")
            lines.append(f"  - {name}: {distance}メートル")
        return "\n".join(lines)

    elif tool_name == "tool_find_complementary_pois":
        origin = output.get("origin_poi", "不明")
        target = output.get("target_category", "不明")
        count = output.get("count", 0)
        lines = [f"{origin}の近くにある{target}（{count}件）:"]
        for poi in output.get("complementary_pois", []):
            name = poi.get("name", "不明")
            distance = poi.get("distance_m", "不明")
            lines.append(f"  - {name}: {distance}メートル")
        return "\n".join(lines)

    elif tool_name == "tool_find_pois_in_same_area":
        origin = output.get("origin_poi", "不明")
        area = output.get("area_cluster", "不明")
        count = output.get("count", 0)
        lines = [f"{origin}と同じエリア（{area}）のPOI（{count}件）:"]
        for poi in output.get("same_area_pois", [])[:10]:
            name = poi.get("name", "不明")
            category = poi.get("category", "不明")
            lines.append(f"  - {name}（{category}）")
        return "\n".join(lines)

    # フォールバック: 辞書のキーと値を日本語テキスト化
    lines = []
    for key, value in output.items():
        if isinstance(value, list) and len(value) > 0:
            lines.append(f"{key}: {len(value)}件")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines) if lines else json.dumps(output, ensure_ascii=False)


# =============================================================================
# 空間計算ツール群
# =============================================================================

@tool
def tool_get_nearest_pois(
    category: Optional[str] = None,
    top_n: int = 3,
    area: Optional[str] = None
) -> str:
    """
    指定エリアの駅から最も近いPOIを検索します。

    Args:
        category: 検索するカテゴリ（例: "カフェ", "飲食店", "コンビニ"）。Noneの場合は全カテゴリ対象。
        top_n: 取得する件数（デフォルト: 3）
        area: エリアキー（"shibuya", "shinjuku", "ikebukuro", "tokyo"）。Noneの場合は全エリア対象。

    Returns:
        最寄りPOI情報の日本語テキスト

    Examples:
        - 渋谷の最寄りカフェ: tool_get_nearest_pois(category="カフェ", top_n=3, area="shibuya")
        - 新宿の最寄りPOI: tool_get_nearest_pois(top_n=5, area="shinjuku")
    """
    pois = get_global_pois(area)
    nearest = get_nearest_pois(pois, category, top_n)

    result = {
        "category": category or "全て",
        "count": len(nearest),
        "pois": [
            {
                "name": poi.get("name", "不明"),
                "category": poi.get("category", "不明"),
                "distance_m": poi.get("distance_from_station", "不明"),
                "direction": poi.get("direction_from_station_jp", "不明")
            }
            for poi in nearest
        ]
    }

    return format_tool_output_japanese("tool_get_nearest_pois", result)


@tool
def tool_count_pois_in_radius(
    radius_m: float,
    category: Optional[str] = None,
    area: Optional[str] = None
) -> str:
    """
    指定した半径内のPOI件数を集計します。

    Args:
        radius_m: 半径（メートル）
        category: フィルタするカテゴリ（部分一致）。Noneの場合は全カテゴリ対象。
        area: エリアキー（"shibuya", "shinjuku", "ikebukuro", "tokyo"）。Noneの場合は全エリア対象。

    Returns:
        集計結果の日本語テキスト

    Examples:
        - 渋谷の500m以内のカフェ: tool_count_pois_in_radius(radius_m=500, category="カフェ", area="shibuya")
        - 新宿の300m以内の全POI: tool_count_pois_in_radius(radius_m=300, area="shinjuku")
    """
    pois = get_global_pois(area)
    count = count_by_radius(pois, radius_m, category)

    result = {
        "radius_m": radius_m,
        "category": category or "全て",
        "count": count
    }

    return format_tool_output_japanese("tool_count_pois_in_radius", result)


@tool
def tool_compare_radius(
    radius1_m: float,
    radius2_m: float,
    category: Optional[str] = None,
    area: Optional[str] = None
) -> str:
    """
    異なる半径での件数を比較します（感度分析）。
    半径を変えた時にPOI件数がどう変化するかを分析できます。

    Args:
        radius1_m: 半径1（メートル）
        radius2_m: 半径2（メートル）
        category: フィルタするカテゴリ。Noneの場合は全カテゴリ対象。
        area: エリアキー（"shibuya", "shinjuku", "ikebukuro", "tokyo"）。Noneの場合は全エリア対象。

    Returns:
        比較結果の日本語テキスト

    Examples:
        - 渋谷で300mと500mのカフェ比較: tool_compare_radius(radius1_m=300, radius2_m=500, category="カフェ", area="shibuya")
    """
    pois = get_global_pois(area)
    comparison = compare_by_radius(pois, radius1_m, radius2_m, category)

    result = {
        "radius1_m": comparison.radius1_m,
        "radius2_m": comparison.radius2_m,
        "count1": comparison.count1,
        "count2": comparison.count2,
        "difference": comparison.difference,
        "ratio": comparison.ratio,
        "category": comparison.category or "全て",
        "summary_jp": comparison.to_japanese()
    }

    return format_tool_output_japanese("tool_compare_radius", result)


@tool
def tool_analyze_sensitivity(
    category: Optional[str] = None,
    radii: Optional[List[float]] = None,
    area: Optional[str] = None
) -> str:
    """
    複数の半径でのPOI件数変化を分析します（詳細な感度分析）。

    Args:
        category: フィルタするカテゴリ
        radii: 分析する半径のリスト。Noneの場合は[100, 200, 300, 500, 800, 1000]
        area: エリアキー（"shibuya", "shinjuku", "ikebukuro", "tokyo"）。Noneの場合は全エリア対象。

    Returns:
        感度分析結果の日本語テキスト

    Examples:
        - 渋谷のカフェの半径別件数: tool_analyze_sensitivity(category="カフェ", area="shibuya")
    """
    pois = get_global_pois(area)
    result = analyze_radius_sensitivity(pois, category, radii)

    return format_tool_output_japanese("tool_analyze_sensitivity", result)


@tool
def tool_filter_by_area(
    radius_m: float,
    category: Optional[str] = None,
    area: Optional[str] = None
) -> str:
    """
    指定した半径内のPOIリストを取得します。

    Args:
        radius_m: 半径（メートル）
        category: フィルタするカテゴリ
        area: エリアキー（"shibuya", "shinjuku", "ikebukuro", "tokyo"）。Noneの場合は全エリア対象。

    Returns:
        POIリストの日本語テキスト

    Examples:
        - 渋谷の500m以内のカフェ: tool_filter_by_area(radius_m=500, category="カフェ", area="shibuya")
    """
    pois = get_global_pois(area)
    filtered = filter_by_radius(pois, radius_m, category)

    result = {
        "radius_m": radius_m,
        "category": category or "全て",
        "count": len(filtered),
        "pois": [
            {
                "name": poi.get("name", "不明"),
                "category": poi.get("category", "不明"),
                "distance_m": poi.get("distance_from_station", "不明"),
                "direction": poi.get("direction_from_station_jp", "不明")
            }
            for poi in filtered[:20]
        ]
    }

    return format_tool_output_japanese("tool_filter_by_area", result)


@tool
def tool_calculate_distance(
    poi_name1: str,
    poi_name2: str
) -> str:
    """
    2つのPOI間の距離を計算します。

    Args:
        poi_name1: POI名1（部分一致で検索）
        poi_name2: POI名2（部分一致で検索）

    Returns:
        距離計算結果のJSON文字列

    Examples:
        - 2つの店舗間の距離: tool_calculate_distance(poi_name1="スターバックス", poi_name2="タリーズ")
    """
    pois = get_global_pois()

    # POI検索
    poi1 = None
    poi2 = None
    for poi in pois:
        if poi_name1.lower() in poi.get("name", "").lower() and poi1 is None:
            poi1 = poi
        if poi_name2.lower() in poi.get("name", "").lower() and poi2 is None:
            poi2 = poi
        if poi1 and poi2:
            break

    if not poi1:
        return format_tool_output_japanese("tool_calculate_distance", {"error": f"POI '{poi_name1}' が見つかりません"})
    if not poi2:
        return format_tool_output_japanese("tool_calculate_distance", {"error": f"POI '{poi_name2}' が見つかりません"})

    # メタデータ内のlat/lonにも対応
    lat1 = poi1.get("lat") or poi1.get("metadata", {}).get("lat")
    lon1 = poi1.get("lon") or poi1.get("metadata", {}).get("lon")
    lat2 = poi2.get("lat") or poi2.get("metadata", {}).get("lat")
    lon2 = poi2.get("lon") or poi2.get("metadata", {}).get("lon")

    if not all([lat1, lon1, lat2, lon2]):
        return format_tool_output_japanese("tool_calculate_distance", {"error": "座標情報が不足しています"})

    distance = haversine_distance(lat1, lon1, lat2, lon2)

    result = {
        "poi1": {"name": poi1.get("name", "不明"), "category": poi1.get("category", "不明")},
        "poi2": {"name": poi2.get("name", "不明"), "category": poi2.get("category", "不明")},
        "distance_m": round(distance, 2)
    }

    return format_tool_output_japanese("tool_calculate_distance", result)


# =============================================================================
# 比較・集計ツール群
# =============================================================================

@tool
def tool_compare_east_west(
    category: Optional[str] = None,
    area: Optional[str] = None
) -> str:
    """
    指定エリアの駅の東側と西側でPOI件数を比較します。

    Args:
        category: 比較するカテゴリ。Noneの場合は全カテゴリ対象。
        area: エリアキー（"shibuya", "shinjuku", "ikebukuro", "tokyo"）。Noneの場合は全エリア対象。

    Returns:
        東西比較結果の日本語テキスト

    Examples:
        - 渋谷のカフェ東西比較: tool_compare_east_west(category="カフェ", area="shibuya")
        - 新宿の全POI東西比較: tool_compare_east_west(area="shinjuku")
    """
    pois = get_global_pois(area)
    comparison = compare_east_west(pois, category)

    result = {
        "category": category or "全て",
        "east_count": comparison.item1_count,
        "west_count": comparison.item2_count,
        "winner": comparison.winner,
        "difference": comparison.difference,
        "summary_jp": comparison.to_japanese()
    }

    return format_tool_output_japanese("tool_compare_east_west", result)


@tool
def tool_compare_north_south(
    category: Optional[str] = None,
    area: Optional[str] = None
) -> str:
    """
    指定エリアの駅の北側と南側でPOI件数を比較します。

    Args:
        category: 比較するカテゴリ。Noneの場合は全カテゴリ対象。
        area: エリアキー（"shibuya", "shinjuku", "ikebukuro", "tokyo"）。Noneの場合は全エリア対象。

    Returns:
        南北比較結果の日本語テキスト
    """
    pois = get_global_pois(area)
    comparison = compare_north_south(pois, category)

    result = {
        "category": category or "全て",
        "north_count": comparison.item1_count,
        "south_count": comparison.item2_count,
        "winner": comparison.winner,
        "difference": comparison.difference,
        "summary_jp": comparison.to_japanese()
    }

    return format_tool_output_japanese("tool_compare_north_south", result)


@tool
def tool_count_by_category(
    categories: Optional[List[str]] = None,
    area: Optional[str] = None
) -> str:
    """
    カテゴリ別にPOI件数を集計します。

    Args:
        categories: 集計するカテゴリのリスト。Noneの場合は全カテゴリを集計。
        area: エリアキー（"shibuya", "shinjuku", "ikebukuro", "tokyo"）。Noneの場合は全エリア対象。

    Returns:
        カテゴリ別集計結果の日本語テキスト

    Examples:
        - 渋谷の全カテゴリ集計: tool_count_by_category(area="shibuya")
        - 新宿の特定カテゴリ集計: tool_count_by_category(categories=["カフェ", "レストラン"], area="shinjuku")
    """
    pois = get_global_pois(area)

    if categories:
        result = {}
        for cat in categories:
            filtered = filter_by_category(pois, cat)
            result[cat] = len(filtered)
    else:
        result = count_by_category(pois)

    return format_tool_output_japanese("tool_count_by_category", result)


@tool
def tool_get_top_categories(
    top_n: int = 5,
    area: Optional[str] = None
) -> str:
    """
    件数上位のカテゴリランキングを取得します。

    Args:
        top_n: 取得する件数（デフォルト: 5）
        area: エリアキー（"shibuya", "shinjuku", "ikebukuro", "tokyo"）。Noneの場合は全エリア対象。

    Returns:
        ランキング結果の日本語テキスト

    Examples:
        - 渋谷のトップ5カテゴリ: tool_get_top_categories(top_n=5, area="shibuya")
        - 全エリアのトップ10: tool_get_top_categories(top_n=10)
    """
    pois = get_global_pois(area)
    top_cats = get_top_categories(pois, top_n, include_examples=True, example_count=3)

    result = {
        "top_n": top_n,
        "categories": [
            {
                "rank": i + 1,
                "category": cat.category,
                "count": cat.count,
                "examples": cat.examples
            }
            for i, cat in enumerate(top_cats)
        ]
    }

    return format_tool_output_japanese("tool_get_top_categories", result)


@tool
def tool_analyze_category_by_direction(
    category: str,
    area: Optional[str] = None
) -> str:
    """
    特定カテゴリのPOIを方向別に詳細分析します。

    Args:
        category: 分析するカテゴリ
        area: エリアキー（"shibuya", "shinjuku", "ikebukuro", "tokyo"）。Noneの場合は全エリア対象。

    Returns:
        方向別分析結果の日本語テキスト

    Examples:
        - 渋谷のカフェ方向別分析: tool_analyze_category_by_direction(category="カフェ", area="shibuya")
    """
    pois = get_global_pois(area)
    analysis = analyze_category_by_direction(pois, category)

    return format_tool_output_japanese("tool_analyze_category_by_direction", analysis)


# =============================================================================
# 検索ツール群
# =============================================================================

@tool
def tool_vector_search(
    query: str,
    k: int = 5
) -> str:
    """
    セマンティック検索でPOIを検索します。
    質問の意図に近いPOIを意味的に検索します。

    Args:
        query: 検索クエリ
        k: 取得件数

    Returns:
        検索結果のJSON文字列

    Examples:
        - "コーヒーが飲める場所": tool_vector_search(query="コーヒーが飲める場所", k=5)
    """
    # TODO: ベクトル検索の実装（chromadbとの連携）
    # 現在は簡易実装
    pois = get_global_pois()

    # キーワードベースの簡易検索
    query_lower = query.lower()
    results = []
    for poi in pois:
        name = poi.get("name", "").lower()
        category = poi.get("category", "").lower()
        if query_lower in name or query_lower in category:
            results.append(poi)

    result = {
        "query": query,
        "count": len(results[:k]),
        "pois": [
            {
                "name": poi.get("name", "不明"),
                "category": poi.get("category", "不明"),
                "distance_m": poi.get("distance_from_station", "不明"),
                "direction": poi.get("direction_from_station_jp", "不明")
            }
            for poi in results[:k]
        ]
    }

    return format_tool_output_japanese("tool_vector_search", result)


@tool
def tool_find_pois_by_keyword(
    keyword: str
) -> str:
    """
    キーワードでPOIを検索します（名前またはカテゴリに含まれるもの）。

    Args:
        keyword: 検索キーワード

    Returns:
        検索結果の日本語テキスト

    Examples:
        - "スターバックス"を検索: tool_find_pois_by_keyword(keyword="スターバックス")
        - "カフェ"を検索: tool_find_pois_by_keyword(keyword="カフェ")
    """
    pois = get_global_pois()
    keyword_lower = keyword.lower()

    results = [
        poi for poi in pois
        if keyword_lower in poi.get("name", "").lower() or
           keyword_lower in poi.get("category", "").lower()
    ]

    result = {
        "keyword": keyword,
        "count": len(results),
        "pois": [
            {
                "name": poi.get("name", "不明"),
                "category": poi.get("category", "不明"),
                "distance_m": poi.get("distance_from_station", "不明"),
                "direction": poi.get("direction_from_station_jp", "不明")
            }
            for poi in results[:20]
        ]
    }

    return format_tool_output_japanese("tool_find_pois_by_keyword", result)


# =============================================================================
# グラフトラバーサル風ツール群
# =============================================================================

@tool
def tool_find_nearby_similar_pois(
    poi_name: str,
    max_distance_m: float = 200
) -> str:
    """
    特定のPOIの近くにある同じカテゴリのPOIを検索します（競合店検索）。

    Args:
        poi_name: 起点となるPOI名（部分一致で検索）
        max_distance_m: 最大距離（メートル、デフォルト: 200m）

    Returns:
        近隣の同カテゴリPOIのJSON文字列

    Examples:
        - スターバックスの近くにある他のカフェ: tool_find_nearby_similar_pois(poi_name="スターバックス", max_distance_m=200)
    """
    pois = get_global_pois()

    # 起点POIを検索
    origin_poi = None
    for poi in pois:
        if poi_name.lower() in poi.get("name", "").lower():
            origin_poi = poi
            break

    if not origin_poi:
        return format_tool_output_japanese("tool_find_nearby_similar_pois", {"error": f"POI '{poi_name}' が見つかりません"})

    # 同カテゴリで近隣のPOIを検索
    origin_category = origin_poi.get("category", "")
    origin_lat = origin_poi.get("lat") or origin_poi.get("metadata", {}).get("lat")
    origin_lon = origin_poi.get("lon") or origin_poi.get("metadata", {}).get("lon")

    if not origin_lat or not origin_lon:
        return format_tool_output_japanese("tool_find_nearby_similar_pois", {"error": "起点POIの座標情報がありません"})

    nearby_pois = []
    for poi in pois:
        if poi.get("name") == origin_poi.get("name"):
            continue

        if origin_category in poi.get("category", ""):
            poi_lat = poi.get("lat") or poi.get("metadata", {}).get("lat")
            poi_lon = poi.get("lon") or poi.get("metadata", {}).get("lon")
            if not poi_lat or not poi_lon:
                continue
            distance = haversine_distance(origin_lat, origin_lon, poi_lat, poi_lon)
            if distance <= max_distance_m:
                nearby_pois.append({
                    "name": poi.get("name", "不明"),
                    "category": poi.get("category", "不明"),
                    "distance_m": round(distance, 2),
                    "direction": poi.get("direction_from_station_jp", "不明")
                })

    nearby_pois.sort(key=lambda x: x["distance_m"])

    result = {
        "origin_poi": origin_poi.get("name"),
        "origin_category": origin_category,
        "max_distance_m": max_distance_m,
        "count": len(nearby_pois),
        "nearby_pois": nearby_pois[:10]
    }

    return format_tool_output_japanese("tool_find_nearby_similar_pois", result)


@tool
def tool_find_complementary_pois(
    poi_name: str,
    target_category: str,
    max_distance_m: float = 200
) -> str:
    """
    特定のPOIの近くにある異なるカテゴリのPOIを検索します（相補的POI検索）。
    例: ホテルの近くのレストラン、映画館の近くのカフェなど

    Args:
        poi_name: 起点となるPOI名（部分一致で検索）
        target_category: 検索したいカテゴリ（部分一致）
        max_distance_m: 最大距離（メートル、デフォルト: 200m）

    Returns:
        近隣の異カテゴリPOIのJSON文字列

    Examples:
        - ホテル近くのレストラン: tool_find_complementary_pois(poi_name="ホテル", target_category="レストラン", max_distance_m=300)
        - 映画館近くのカフェ: tool_find_complementary_pois(poi_name="シネマ", target_category="カフェ")
    """
    pois = get_global_pois()

    # 起点POIを検索
    origin_poi = None
    for poi in pois:
        if poi_name.lower() in poi.get("name", "").lower():
            origin_poi = poi
            break

    if not origin_poi:
        return format_tool_output_japanese("tool_find_complementary_pois", {"error": f"POI '{poi_name}' が見つかりません"})

    # 指定カテゴリで近隣のPOIを検索
    origin_lat = origin_poi.get("lat") or origin_poi.get("metadata", {}).get("lat")
    origin_lon = origin_poi.get("lon") or origin_poi.get("metadata", {}).get("lon")

    if not origin_lat or not origin_lon:
        return format_tool_output_japanese("tool_find_complementary_pois", {"error": "起点POIの座標情報がありません"})

    nearby_pois = []
    for poi in pois:
        if target_category.lower() in poi.get("category", "").lower():
            poi_lat = poi.get("lat") or poi.get("metadata", {}).get("lat")
            poi_lon = poi.get("lon") or poi.get("metadata", {}).get("lon")
            if not poi_lat or not poi_lon:
                continue
            distance = haversine_distance(origin_lat, origin_lon, poi_lat, poi_lon)
            if distance <= max_distance_m:
                nearby_pois.append({
                    "name": poi.get("name", "不明"),
                    "category": poi.get("category", "不明"),
                    "distance_m": round(distance, 2),
                    "direction": poi.get("direction_from_station_jp", "不明")
                })

    nearby_pois.sort(key=lambda x: x["distance_m"])

    result = {
        "origin_poi": origin_poi.get("name"),
        "origin_category": origin_poi.get("category", "不明"),
        "target_category": target_category,
        "max_distance_m": max_distance_m,
        "count": len(nearby_pois),
        "complementary_pois": nearby_pois[:10]
    }

    return format_tool_output_japanese("tool_find_complementary_pois", result)


@tool
def tool_find_pois_in_same_area(
    poi_name: str,
    target_category: Optional[str] = None
) -> str:
    """
    特定のPOIと同じエリアクラスタにあるPOIを検索します。

    Args:
        poi_name: 起点となるPOI名（部分一致で検索）
        target_category: 検索したいカテゴリ（Noneの場合は全カテゴリ）

    Returns:
        同エリアのPOIのJSON文字列

    Examples:
        - 同じエリアのカフェ: tool_find_pois_in_same_area(poi_name="スターバックス", target_category="カフェ")
    """
    pois = get_global_pois()

    # 起点POIを検索
    origin_poi = None
    for poi in pois:
        if poi_name.lower() in poi.get("name", "").lower():
            origin_poi = poi
            break

    if not origin_poi:
        return format_tool_output_japanese("tool_find_pois_in_same_area", {"error": f"POI '{poi_name}' が見つかりません"})

    # 同じエリアクラスタのPOIを検索
    origin_area = origin_poi.get("area_cluster", "")
    if not origin_area:
        return format_tool_output_japanese("tool_find_pois_in_same_area", {"error": "起点POIのエリア情報がありません"})

    same_area_pois = []
    for poi in pois:
        if poi.get("name") == origin_poi.get("name"):
            continue

        if poi.get("area_cluster") == origin_area:
            if target_category and target_category.lower() not in poi.get("category", "").lower():
                continue

            same_area_pois.append({
                "name": poi.get("name", "不明"),
                "category": poi.get("category", "不明"),
                "distance_m": poi.get("distance_from_station", "不明"),
                "direction": poi.get("direction_from_station_jp", "不明")
            })

    result = {
        "origin_poi": origin_poi.get("name"),
        "area_cluster": origin_area,
        "target_category": target_category or "全て",
        "count": len(same_area_pois),
        "same_area_pois": same_area_pois[:20]
    }

    return format_tool_output_japanese("tool_find_pois_in_same_area", result)


# =============================================================================
# ツールリスト取得
# =============================================================================

def get_all_tools() -> List:
    """全ツールのリストを取得"""
    return [
        # 空間計算ツール
        tool_get_nearest_pois,
        tool_count_pois_in_radius,
        tool_compare_radius,
        tool_analyze_sensitivity,
        tool_filter_by_area,
        tool_calculate_distance,
        # 比較・集計ツール
        tool_compare_east_west,
        tool_compare_north_south,
        tool_count_by_category,
        tool_get_top_categories,
        tool_analyze_category_by_direction,
        # 検索ツール
        tool_vector_search,
        tool_find_pois_by_keyword,
        # グラフトラバーサルツール
        tool_find_nearby_similar_pois,
        tool_find_complementary_pois,
        tool_find_pois_in_same_area,
    ]


# =============================================================================
# テスト・デバッグ用
# =============================================================================

def test_tools():
    """ツール動作確認"""
    print("=" * 60)
    print("agent_tools.py 動作確認（Phase 9-B 広域対応 + 中国語混入対策）")
    print("=" * 60)

    # テスト用POIデータ読み込み
    try:
        with open("poi_documents.json", "r", encoding="utf-8") as f:
            raw_pois = json.load(f)
    except FileNotFoundError:
        print("poi_documents.json が見つかりません")
        return

    # メタデータをフラット化
    flat_pois = []
    for poi in raw_pois:
        if "metadata" in poi:
            flat_poi = poi["metadata"].copy()
            flat_pois.append(flat_poi)
        else:
            flat_pois.append(poi)

    # 空間情報付加
    from geo_utils import enrich_all_pois
    pois = enrich_all_pois(flat_pois)
    set_global_pois(pois)

    print(f"\nPOIデータ読み込み完了: {len(pois)}件")

    # ツールテスト（日本語自然文出力の確認）
    print("\n--- 最寄りカフェ検索（日本語出力） ---")
    output = tool_get_nearest_pois.invoke({"category": "カフェ", "top_n": 3})
    print(output)
    # JSON形式でないことを確認
    assert not output.strip().startswith("{"), "ツール出力がJSON形式です（日本語自然文であるべき）"

    print("\n--- 500m以内のカフェ件数（日本語出力） ---")
    output = tool_count_pois_in_radius.invoke({"radius_m": 500, "category": "カフェ"})
    print(output)
    assert not output.strip().startswith("{"), "ツール出力がJSON形式です"

    print("\n--- 東西比較カフェ（日本語出力） ---")
    output = tool_compare_east_west.invoke({"category": "カフェ"})
    print(output)
    assert not output.strip().startswith("{"), "ツール出力がJSON形式です"

    # format_tool_output_japanese のテスト
    print("\n--- format_tool_output_japanese テスト ---")
    test_output = {
        "category": "カフェ",
        "count": 2,
        "pois": [
            {"name": "スターバックス渋谷店", "direction": "東", "distance_m": 150.5},
            {"name": "タリーズ宮益坂店", "direction": "北東", "distance_m": 200.3},
        ]
    }
    formatted = format_tool_output_japanese("tool_get_nearest_pois", test_output)
    assert "スターバックス渋谷店" in formatted
    assert "150.5メートル" in formatted
    assert "{" not in formatted  # JSON形式でないこと
    print(formatted)

    # set_global_pois_multi_area のテスト
    print("\n--- set_global_pois_multi_area テスト ---")
    test_areas_config = {
        "shibuya": {"name": "渋谷駅周辺", "station": {"name": "渋谷駅", "lat": 35.658034, "lon": 139.701636}},
    }
    set_global_pois_multi_area(pois, test_areas_config)
    area_pois = get_global_pois("shibuya")
    print(f"  全POI: {len(get_global_pois())}件")
    print(f"  渋谷POI: {len(area_pois)}件")

    print("\n✅ agent_tools.py 動作確認完了（広域対応 + 中国語混入対策）")


if __name__ == "__main__":
    test_tools()
