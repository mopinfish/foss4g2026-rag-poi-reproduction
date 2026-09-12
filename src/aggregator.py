"""
aggregator.py - POI集計・比較ユーティリティ

Phase 6: RAG改善のためのカテゴリ別・方向別集計・比較機能
Phase 9-B: エリア間比較・エリア別分割

作成日: 2026-01-22
更新日: 2026-02-18
プロジェクト: experiments-local-llm
"""

from typing import List, Dict, Any, Tuple, Optional
from collections import Counter, defaultdict
from dataclasses import dataclass, field


# =============================================================================
# データクラス
# =============================================================================

@dataclass
class CategoryCount:
    """カテゴリ別件数"""
    category: str
    count: int
    examples: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "count": self.count,
            "examples": self.examples
        }


@dataclass
class DirectionCount:
    """方向別件数"""
    direction: str
    direction_jp: str
    count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "direction": self.direction,
            "direction_jp": self.direction_jp,
            "count": self.count
        }


@dataclass
class ComparisonResult:
    """比較結果"""
    item1_name: str
    item1_count: int
    item2_name: str
    item2_count: int
    winner: str
    difference: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "item1": {"name": self.item1_name, "count": self.item1_count},
            "item2": {"name": self.item2_name, "count": self.item2_count},
            "winner": self.winner,
            "difference": self.difference
        }
    
    def to_japanese(self) -> str:
        """日本語での比較結果"""
        if self.difference == 0:
            return f"{self.item1_name}と{self.item2_name}は同数（{self.item1_count}件）"
        return f"{self.winner}が{self.difference}件多い（{self.item1_name}: {self.item1_count}件、{self.item2_name}: {self.item2_count}件）"


@dataclass
class AggregationResult:
    """集計結果"""
    total: int
    by_category: Dict[str, int]
    by_direction: Dict[str, int]
    top_categories: List[CategoryCount]
    east_west_comparison: Optional[ComparisonResult] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "by_category": self.by_category,
            "by_direction": self.by_direction,
            "top_categories": [c.to_dict() for c in self.top_categories],
            "east_west_comparison": self.east_west_comparison.to_dict() if self.east_west_comparison else None
        }


# =============================================================================
# 基本集計関数
# =============================================================================

def count_total(pois: List[Dict[str, Any]]) -> int:
    """
    POI総数をカウント
    
    Args:
        pois: POIデータのリスト
    
    Returns:
        総数
    """
    return len(pois)


def count_by_category(pois: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    カテゴリ別のPOI件数を集計
    
    Args:
        pois: POIデータのリスト
    
    Returns:
        カテゴリ別件数の辞書
    
    Example:
        >>> count_by_category(pois)
        {'飲食店/カフェ': 45, '商店/コンビニ': 23, ...}
    """
    return dict(Counter(poi.get("category", "不明") for poi in pois))


def count_by_subcategory(pois: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    サブカテゴリ別のPOI件数を集計
    カテゴリが「大分類/小分類」形式の場合、小分類で集計
    
    Args:
        pois: POIデータのリスト
    
    Returns:
        サブカテゴリ別件数の辞書
    """
    subcategories = []
    for poi in pois:
        category = poi.get("category", "不明")
        if "/" in category:
            subcategories.append(category.split("/")[-1])
        else:
            subcategories.append(category)
    
    return dict(Counter(subcategories))


def count_by_main_category(pois: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    大分類別のPOI件数を集計
    カテゴリが「大分類/小分類」形式の場合、大分類で集計
    
    Args:
        pois: POIデータのリスト
    
    Returns:
        大分類別件数の辞書
    """
    main_categories = []
    for poi in pois:
        category = poi.get("category", "不明")
        if "/" in category:
            main_categories.append(category.split("/")[0])
        else:
            main_categories.append(category)
    
    return dict(Counter(main_categories))


def count_by_direction(pois: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    方向別のPOI件数を集計
    
    Args:
        pois: 空間情報を持つPOIデータのリスト
    
    Returns:
        方向別件数の辞書
    """
    return dict(Counter(poi.get("direction_from_station", "不明") for poi in pois))


def count_by_area_cluster(pois: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    エリアクラスタ別のPOI件数を集計
    
    Args:
        pois: 空間情報を持つPOIデータのリスト
    
    Returns:
        エリアクラスタ別件数の辞書
    """
    return dict(Counter(poi.get("area_cluster", "不明") for poi in pois))


def count_by_distance_zone(pois: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    距離ゾーン別のPOI件数を集計
    
    Args:
        pois: 空間情報を持つPOIデータのリスト
    
    Returns:
        距離ゾーン別件数の辞書
    """
    return dict(Counter(poi.get("distance_zone", "不明") for poi in pois))


# =============================================================================
# ランキング関数
# =============================================================================

def get_top_categories(
    pois: List[Dict[str, Any]],
    top_n: int = 5,
    include_examples: bool = True,
    example_count: int = 3
) -> List[CategoryCount]:
    """
    件数上位のカテゴリを取得
    
    Args:
        pois: POIデータのリスト
        top_n: 取得件数
        include_examples: 例を含めるか
        example_count: 例の件数
    
    Returns:
        上位カテゴリのリスト
    """
    counts = count_by_category(pois)
    sorted_cats = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    
    result = []
    for cat, count in sorted_cats[:top_n]:
        examples = []
        if include_examples:
            examples = [
                poi.get("name", "不明")
                for poi in pois
                if poi.get("category") == cat
            ][:example_count]
        
        result.append(CategoryCount(
            category=cat,
            count=count,
            examples=examples
        ))
    
    return result


def get_top_subcategories(
    pois: List[Dict[str, Any]],
    top_n: int = 5
) -> List[Tuple[str, int]]:
    """
    件数上位のサブカテゴリを取得
    
    Args:
        pois: POIデータのリスト
        top_n: 取得件数
    
    Returns:
        (サブカテゴリ名, 件数)のタプルリスト
    """
    counts = count_by_subcategory(pois)
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:top_n]


# =============================================================================
# フィルタリング関数
# =============================================================================

def _get_poi_category(poi: Dict[str, Any]) -> str:
    """POIからカテゴリ文字列を取得（トップレベルまたはmetadata内）"""
    return poi.get("category", "") or poi.get("metadata", {}).get("category", "")


def filter_by_category(
    pois: List[Dict[str, Any]],
    category: str,
    partial_match: bool = True
) -> List[Dict[str, Any]]:
    """
    カテゴリでPOIをフィルタリング

    Args:
        pois: POIデータのリスト
        category: フィルタするカテゴリ（部分一致可）
        partial_match: 部分一致を許可するか

    Returns:
        フィルタリングされたPOIリスト
    """
    if partial_match:
        return [poi for poi in pois if category.lower() in _get_poi_category(poi).lower()]
    else:
        return [poi for poi in pois if _get_poi_category(poi).lower() == category.lower()]


def filter_by_keyword(
    pois: List[Dict[str, Any]],
    keyword: str
) -> List[Dict[str, Any]]:
    """
    キーワードでPOIをフィルタリング（名前またはカテゴリ）
    
    Args:
        pois: POIデータのリスト
        keyword: 検索キーワード
    
    Returns:
        フィルタリングされたPOIリスト
    """
    keyword_lower = keyword.lower()
    return [
        poi for poi in pois
        if keyword_lower in poi.get("name", "").lower() or
           keyword_lower in poi.get("category", "").lower()
    ]


# =============================================================================
# 比較関数
# =============================================================================

def compare_counts(
    name1: str, count1: int,
    name2: str, count2: int
) -> ComparisonResult:
    """
    2つの件数を比較
    
    Args:
        name1, count1: 項目1の名前と件数
        name2, count2: 項目2の名前と件数
    
    Returns:
        ComparisonResult
    """
    if count1 > count2:
        winner = name1
    elif count2 > count1:
        winner = name2
    else:
        winner = "同数"
    
    return ComparisonResult(
        item1_name=name1,
        item1_count=count1,
        item2_name=name2,
        item2_count=count2,
        winner=winner,
        difference=abs(count1 - count2)
    )


def compare_categories(
    pois: List[Dict[str, Any]],
    category1: str,
    category2: str
) -> ComparisonResult:
    """
    2つのカテゴリのPOI件数を比較
    
    Args:
        pois: POIデータのリスト
        category1, category2: 比較するカテゴリ
    
    Returns:
        ComparisonResult
    """
    cat1_pois = filter_by_category(pois, category1)
    cat2_pois = filter_by_category(pois, category2)
    
    return compare_counts(
        category1, len(cat1_pois),
        category2, len(cat2_pois)
    )


def compare_east_west(
    pois: List[Dict[str, Any]],
    category: Optional[str] = None
) -> ComparisonResult:
    """
    東西の件数を比較
    
    Args:
        pois: 空間情報を持つPOIデータのリスト
        category: 特定カテゴリでフィルタする場合
    
    Returns:
        ComparisonResult
    """
    # カテゴリフィルタ
    if category:
        pois = filter_by_category(pois, category)
    
    # 方向別集計
    direction_counts = count_by_direction(pois)
    
    # 東側集計
    east_count = (
        direction_counts.get("east", 0) +
        direction_counts.get("northeast", 0) +
        direction_counts.get("southeast", 0)
    )
    
    # 西側集計
    west_count = (
        direction_counts.get("west", 0) +
        direction_counts.get("northwest", 0) +
        direction_counts.get("southwest", 0)
    )
    
    return compare_counts("東側", east_count, "西側", west_count)


def compare_north_south(
    pois: List[Dict[str, Any]],
    category: Optional[str] = None
) -> ComparisonResult:
    """
    南北の件数を比較
    
    Args:
        pois: 空間情報を持つPOIデータのリスト
        category: 特定カテゴリでフィルタする場合
    
    Returns:
        ComparisonResult
    """
    if category:
        pois = filter_by_category(pois, category)
    
    direction_counts = count_by_direction(pois)
    
    north_count = (
        direction_counts.get("north", 0) +
        direction_counts.get("northeast", 0) +
        direction_counts.get("northwest", 0)
    )
    
    south_count = (
        direction_counts.get("south", 0) +
        direction_counts.get("southeast", 0) +
        direction_counts.get("southwest", 0)
    )
    
    return compare_counts("北側", north_count, "南側", south_count)


# =============================================================================
# 詳細分析関数
# =============================================================================

def analyze_category_by_direction(
    pois: List[Dict[str, Any]],
    category: str
) -> Dict[str, Any]:
    """
    特定カテゴリのPOIを方向別に分析
    
    Args:
        pois: 空間情報を持つPOIデータのリスト
        category: 分析するカテゴリ
    
    Returns:
        分析結果の辞書
    """
    # カテゴリでフィルタリング
    filtered = filter_by_category(pois, category)
    
    # 方向別集計
    direction_counts = count_by_direction(filtered)
    
    # 東西比較
    east_west = compare_east_west(filtered)
    
    # 結果構築
    return {
        "category": category,
        "total": len(filtered),
        "by_direction": direction_counts,
        "east_west_comparison": east_west.to_dict(),
        "east_west_summary": east_west.to_japanese(),
        "examples": [poi.get("name") for poi in filtered[:5]]
    }


def analyze_direction(
    pois: List[Dict[str, Any]],
    direction: str
) -> Dict[str, Any]:
    """
    特定方向のPOIをカテゴリ別に分析
    
    Args:
        pois: 空間情報を持つPOIデータのリスト
        direction: 分析する方向
    
    Returns:
        分析結果の辞書
    """
    # 方向でフィルタリング
    filtered = [poi for poi in pois if poi.get("direction_from_station") == direction]
    
    # カテゴリ別集計
    category_counts = count_by_category(filtered)
    
    # 上位カテゴリ
    top_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "direction": direction,
        "total": len(filtered),
        "by_category": category_counts,
        "top_categories": top_cats,
        "examples": [poi.get("name") for poi in filtered[:5]]
    }


def get_full_aggregation(
    pois: List[Dict[str, Any]],
    top_n: int = 5
) -> AggregationResult:
    """
    POIデータの完全な集計を実行
    
    Args:
        pois: 空間情報を持つPOIデータのリスト
        top_n: 上位カテゴリの件数
    
    Returns:
        AggregationResult
    """
    return AggregationResult(
        total=count_total(pois),
        by_category=count_by_category(pois),
        by_direction=count_by_direction(pois),
        top_categories=get_top_categories(pois, top_n),
        east_west_comparison=compare_east_west(pois)
    )


# =============================================================================
# コンテキスト生成関数
# =============================================================================

def generate_aggregation_context(
    pois: List[Dict[str, Any]],
    analysis_type: str = "full",
    category: Optional[str] = None
) -> str:
    """
    集計結果をLLMコンテキスト用のテキストに変換
    
    Args:
        pois: 空間情報を持つPOIデータのリスト
        analysis_type: 分析タイプ（"full", "category", "ranking", "direction"）
        category: カテゴリ（analysis_type="category"の場合）
    
    Returns:
        コンテキストテキスト
    """
    context_parts = []
    
    if analysis_type == "full":
        agg = get_full_aggregation(pois)
        context_parts.append(f"【POI集計データ】")
        context_parts.append(f"総数: {agg.total}件")
        context_parts.append(f"\nカテゴリ別:")
        for cat in agg.top_categories[:5]:
            context_parts.append(f"  - {cat.category}: {cat.count}件")
        
        if agg.east_west_comparison:
            context_parts.append(f"\n東西比較:")
            context_parts.append(f"  {agg.east_west_comparison.to_japanese()}")
    
    elif analysis_type == "category" and category:
        result = analyze_category_by_direction(pois, category)
        context_parts.append(f"【{category}の分析】")
        context_parts.append(f"総数: {result['total']}件")
        context_parts.append(f"\n方向別:")
        for direction, count in result['by_direction'].items():
            context_parts.append(f"  - {direction}: {count}件")
        context_parts.append(f"\n東西比較:")
        context_parts.append(f"  {result['east_west_summary']}")
    
    elif analysis_type == "ranking":
        top_cats = get_top_categories(pois, top_n=10)
        context_parts.append(f"【POIカテゴリランキング】")
        for i, cat in enumerate(top_cats, 1):
            context_parts.append(f"  {i}位: {cat.category} ({cat.count}件)")
    
    elif analysis_type == "direction":
        direction_counts = count_by_direction(pois)
        context_parts.append(f"【方向別POI件数】")
        for direction, count in sorted(direction_counts.items(), key=lambda x: x[1], reverse=True):
            context_parts.append(f"  - {direction}: {count}件")
    
    return "\n".join(context_parts)


def generate_comparison_context(
    pois: List[Dict[str, Any]],
    comparison_type: str,
    params: Dict[str, Any]
) -> str:
    """
    比較結果をLLMコンテキスト用のテキストに変換
    
    Args:
        pois: 空間情報を持つPOIデータのリスト
        comparison_type: 比較タイプ（"categories", "east_west", "directions"）
        params: パラメータ辞書
    
    Returns:
        コンテキストテキスト
    """
    context_parts = []
    
    if comparison_type == "categories":
        cat1 = params.get("category1", "")
        cat2 = params.get("category2", "")
        result = compare_categories(pois, cat1, cat2)
        context_parts.append(f"【カテゴリ比較: {cat1} vs {cat2}】")
        context_parts.append(result.to_japanese())
    
    elif comparison_type == "east_west":
        category = params.get("category")
        result = compare_east_west(pois, category)
        title = f"【東西比較: {category}】" if category else "【東西比較: 全体】"
        context_parts.append(title)
        context_parts.append(result.to_japanese())
        
        # 詳細も追加
        if category:
            analysis = analyze_category_by_direction(pois, category)
            context_parts.append(f"\n詳細:")
            for direction, count in analysis['by_direction'].items():
                context_parts.append(f"  - {direction}: {count}件")
    
    return "\n".join(context_parts)


# =============================================================================
# Phase 9-B: エリア別分割・エリア間比較
# =============================================================================

def aggregate_by_area(pois: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    POIリストをエリアキーごとに分割する

    Args:
        pois: POIデータのリスト（area_key メタデータを持つこと）

    Returns:
        {area_key: [pois...]} の辞書。area_keyがないPOIは "unknown" に分類。
    """
    result = defaultdict(list)
    for poi in pois:
        area_key = (
            poi.get("area_key")
            or poi.get("metadata", {}).get("area_key")
            or "unknown"
        )
        result[area_key].append(poi)
    return dict(result)


def compare_across_areas(
    pois: List[Dict[str, Any]],
    areas_config: Optional[Dict] = None,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    エリア間でPOI分布を比較する

    Args:
        pois: POIデータのリスト（area_key メタデータ推奨）
        areas_config: エリア設定辞書
        category: 特定カテゴリでフィルタする場合

    Returns:
        エリア間比較結果の辞書
    """
    # カテゴリフィルタ
    if category:
        filtered = filter_by_category(pois, category)
    else:
        filtered = pois

    # エリア別に分割
    by_area = aggregate_by_area(filtered)

    # 各エリアの件数
    area_counts = {}
    for area_key, area_pois in by_area.items():
        area_counts[area_key] = len(area_pois)

    # ランキング
    ranked = sorted(area_counts.items(), key=lambda x: x[1], reverse=True)

    # 結果構築
    result = {
        "category": category,
        "total": len(filtered),
        "by_area": area_counts,
        "ranking": ranked,
    }

    # 最多・最少
    if ranked:
        result["most"] = {"area": ranked[0][0], "count": ranked[0][1]}
        result["least"] = {"area": ranked[-1][0], "count": ranked[-1][1]}

    return result


def generate_cross_area_context(
    pois: List[Dict[str, Any]],
    areas_config: Optional[Dict] = None,
    category: Optional[str] = None
) -> str:
    """
    エリア間比較結果をLLMコンテキスト用テキストに変換

    Args:
        pois: POIデータのリスト
        areas_config: エリア設定辞書
        category: 特定カテゴリ（Noneで全カテゴリ）

    Returns:
        コンテキストテキスト
    """
    comparison = compare_across_areas(pois, areas_config, category)

    cat_label = f"「{category}」" if category else "POI"
    lines = [f"【エリア間{cat_label}比較】"]
    lines.append(f"全体数: {comparison['total']}件")
    lines.append("")

    # エリア別件数（ランキング順）
    for i, (area_key, count) in enumerate(comparison["ranking"], 1):
        lines.append(f"  {i}位: {area_key} ({count}件)")

    # 最多・最少の比較
    if "most" in comparison and "least" in comparison:
        most = comparison["most"]
        least = comparison["least"]
        diff = most["count"] - least["count"]
        lines.append("")
        lines.append(f"最多: {most['area']}（{most['count']}件）")
        lines.append(f"最少: {least['area']}（{least['count']}件）")
        lines.append(f"差: {diff}件")

    return "\n".join(lines)


# =============================================================================
# テスト・デバッグ用関数
# =============================================================================

def test_aggregator():
    """
    aggregator.pyモジュールの動作確認
    """
    print("=" * 60)
    print("aggregator.py 動作確認")
    print("=" * 60)
    
    # テスト用POIデータ
    test_pois = [
        {"name": "スタバ渋谷東口", "category": "飲食店/カフェ", "direction_from_station": "east"},
        {"name": "スタバ渋谷西口", "category": "飲食店/カフェ", "direction_from_station": "west"},
        {"name": "ドトール渋谷", "category": "飲食店/カフェ", "direction_from_station": "east"},
        {"name": "タリーズ渋谷", "category": "飲食店/カフェ", "direction_from_station": "northeast"},
        {"name": "ローソン渋谷駅前", "category": "商店/コンビニ", "direction_from_station": "east"},
        {"name": "セブン渋谷西口", "category": "商店/コンビニ", "direction_from_station": "west"},
        {"name": "ファミマ渋谷", "category": "商店/コンビニ", "direction_from_station": "south"},
        {"name": "TOHOシネマズ", "category": "娯楽/映画館", "direction_from_station": "east"},
        {"name": "渋谷PARCO", "category": "商業施設", "direction_from_station": "northwest"},
        {"name": "渋谷109", "category": "商業施設", "direction_from_station": "west"},
    ]
    
    print(f"\nテストPOI数: {len(test_pois)}件")
    
    # カテゴリ別集計
    print("\n--- カテゴリ別集計 ---")
    cat_counts = count_by_category(test_pois)
    for cat, count in cat_counts.items():
        print(f"  {cat}: {count}件")
    
    # 方向別集計
    print("\n--- 方向別集計 ---")
    dir_counts = count_by_direction(test_pois)
    for direction, count in dir_counts.items():
        print(f"  {direction}: {count}件")
    
    # 東西比較
    print("\n--- 東西比較（全体） ---")
    ew_result = compare_east_west(test_pois)
    print(f"  {ew_result.to_japanese()}")
    
    # 東西比較（カフェ）
    print("\n--- 東西比較（カフェ） ---")
    ew_cafe = compare_east_west(test_pois, "カフェ")
    print(f"  {ew_cafe.to_japanese()}")
    
    # カテゴリ比較
    print("\n--- カテゴリ比較（カフェ vs コンビニ） ---")
    cat_comparison = compare_categories(test_pois, "カフェ", "コンビニ")
    print(f"  {cat_comparison.to_japanese()}")
    
    # コンテキスト生成
    print("\n--- コンテキスト生成 ---")
    context = generate_aggregation_context(test_pois, "full")
    print(context)

    # Phase 9-B: エリア別分割テスト
    print("\n--- Phase 9-B: エリア別分割テスト ---")
    multi_area_pois = [
        {"name": "スタバ渋谷", "category": "飲食店/カフェ", "area_key": "shibuya"},
        {"name": "スタバ新宿", "category": "飲食店/カフェ", "area_key": "shinjuku"},
        {"name": "ドトール渋谷", "category": "飲食店/カフェ", "area_key": "shibuya"},
        {"name": "ローソン池袋", "category": "商店/コンビニ", "area_key": "ikebukuro"},
        {"name": "セブン東京", "category": "商店/コンビニ", "area_key": "tokyo"},
    ]
    by_area = aggregate_by_area(multi_area_pois)
    assert len(by_area["shibuya"]) == 2
    assert len(by_area["shinjuku"]) == 1
    print(f"  エリア別: {', '.join(f'{k}={len(v)}件' for k, v in by_area.items())}")
    print("  ✅ aggregate_by_area() 正常動作")

    # Phase 9-B: エリア間比較テスト
    print("\n--- Phase 9-B: エリア間比較テスト ---")
    comparison = compare_across_areas(multi_area_pois, category="カフェ")
    assert comparison["total"] == 3
    assert comparison["most"]["area"] == "shibuya"
    print(f"  カフェ比較: {comparison['by_area']}")
    print(f"  最多: {comparison['most']}")
    print("  ✅ compare_across_areas() 正常動作")

    # Phase 9-B: エリア間コンテキスト生成テスト
    print("\n--- Phase 9-B: エリア間コンテキスト生成テスト ---")
    context = generate_cross_area_context(multi_area_pois)
    print(context)
    print("  ✅ generate_cross_area_context() 正常動作")

    print("\n✅ aggregator.py 動作確認完了")


if __name__ == "__main__":
    test_aggregator()
