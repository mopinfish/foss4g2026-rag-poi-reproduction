#!/usr/bin/env python3
"""
test_cases_graphrag.py - GraphRAG評価用テストケース（35件）

グラフRAGの強みを測定するために設計されたテストケース。
構造化RAGとの比較評価で使用。

カテゴリ:
- relation: 関係性クエリ（5件） - SAME_AREA, NEAR_TOエッジを活用
- multi_hop: マルチホップクエリ（3件） - グラフトラバーサル
- aggregation: 集計クエリ（3件） - ノード集計
- comparison: 比較クエリ（2件） - 方向別比較
- proximity: 近接性クエリ（2件） - 距離ソート
- brand: ブランドクエリ（5件） - SAME_BRANDエッジを活用
- complementary: 補完関係クエリ（5件） - COMPLEMENTARYエッジを活用
- competitor: 競合関係クエリ（3件） - COMPETITORエッジを活用
- cuisine: 料理ジャンルクエリ（4件） - SAME_CUISINEエッジを活用
- hours: 営業時間クエリ（3件） - SAME_HOURSエッジを活用
"""
from dataclasses import dataclass
from typing import List


@dataclass
class GraphRAGTestCase:
    """グラフRAG評価用テストケース"""
    id: str
    category: str  # relation, multi_hop, aggregation, comparison, proximity
    question: str
    expected_keywords: List[str]
    description: str
    graph_advantage: str  # グラフRAGの想定優位性


GRAPHRAG_TEST_CASES: List[GraphRAGTestCase] = [
    # ==========================================================================
    # 関係性クエリ（5件）- SAME_AREA, NEAR_TOエッジを活用
    # ==========================================================================
    GraphRAGTestCase(
        id="GR-01",
        category="relation",
        question="渋谷駅の東側にあるカフェで、同じエリアにコンビニもある場所はどこですか？",
        expected_keywords=["カフェ", "コンビニ", "東"],
        description="2カテゴリの空間的共起を問う",
        graph_advantage="SAME_AREAエッジで効率的に共起を検出"
    ),
    GraphRAGTestCase(
        id="GR-02",
        category="relation",
        question="銀行とカフェが両方あるエリアを教えてください",
        expected_keywords=["銀行", "カフェ", "エリア"],
        description="2カテゴリのエリア共起を問う",
        graph_advantage="エリアノードを介した効率的な検索"
    ),
    GraphRAGTestCase(
        id="GR-03",
        category="relation",
        question="ホテルの近くにあるレストランを教えてください",
        expected_keywords=["ホテル", "レストラン", "近く"],
        description="POI間の近接関係を問う",
        graph_advantage="NEAR_TOエッジで直接検索"
    ),
    GraphRAGTestCase(
        id="GR-04",
        category="relation",
        question="駅周辺で、薬局とコンビニが同じ場所にあるところはありますか？",
        expected_keywords=["薬局", "コンビニ", "駅"],
        description="駅周辺エリアでの共起を問う",
        graph_advantage="エリアフィルタ + 共起検索"
    ),
    GraphRAGTestCase(
        id="GR-05",
        category="relation",
        question="映画館の近くにあるカフェはどこですか？",
        expected_keywords=["映画館", "カフェ"],
        description="娯楽施設と飲食店の関係を問う",
        graph_advantage="NEAR_TOエッジで直接検索"
    ),

    # ==========================================================================
    # マルチホップクエリ（3件）- グラフトラバーサル
    # ==========================================================================
    GraphRAGTestCase(
        id="GR-06",
        category="multi_hop",
        question="カフェを起点に、そこから50m以内にある書店を教えてください",
        expected_keywords=["カフェ", "書店", "50m"],
        description="2ホップの経路探索",
        graph_advantage="グラフトラバーサルによる経路探索"
    ),
    GraphRAGTestCase(
        id="GR-07",
        category="multi_hop",
        question="渋谷駅から100m以内のコンビニと、そこから近いカフェを教えてください",
        expected_keywords=["コンビニ", "カフェ", "100m"],
        description="距離制約付き2ホップ検索",
        graph_advantage="DISTANCE_FROM + NEAR_TOの連鎖"
    ),
    GraphRAGTestCase(
        id="GR-08",
        category="multi_hop",
        question="ホテルから徒歩で行ける範囲にあるレストランとカフェを教えてください",
        expected_keywords=["ホテル", "レストラン", "カフェ"],
        description="ホテルを起点とした飲食店探索",
        graph_advantage="複数カテゴリへの同時トラバーサル"
    ),

    # ==========================================================================
    # 集計クエリ（3件）- ノード集計
    # ==========================================================================
    GraphRAGTestCase(
        id="GR-09",
        category="aggregation",
        question="飲食店が最も多いエリアはどこですか？",
        expected_keywords=["飲食店", "エリア", "多い"],
        description="エリア別カテゴリ集計",
        graph_advantage="LOCATED_INエッジのカウント"
    ),
    GraphRAGTestCase(
        id="GR-10",
        category="aggregation",
        question="北側と南側でPOIの数が多いのはどちらですか？",
        expected_keywords=["北", "南", "数", "多い"],
        description="方向別POI集計",
        graph_advantage="方向属性によるフィルタ集計"
    ),
    GraphRAGTestCase(
        id="GR-11",
        category="aggregation",
        question="渋谷で最も多いカテゴリのPOIは何ですか？上位3つを教えてください",
        expected_keywords=["カテゴリ", "多い", "上位"],
        description="カテゴリ別POIランキング",
        graph_advantage="カテゴリノードへのエッジ集計"
    ),

    # ==========================================================================
    # 比較クエリ（2件）- 方向別比較
    # ==========================================================================
    GraphRAGTestCase(
        id="GR-12",
        category="comparison",
        question="東側と西側で、飲食店のカテゴリ多様性が高いのはどちらですか？",
        expected_keywords=["東", "西", "飲食店", "多様性"],
        description="方向別カテゴリ多様性比較",
        graph_advantage="サブカテゴリノードの数で多様性を計算"
    ),
    GraphRAGTestCase(
        id="GR-13",
        category="comparison",
        question="駅の近く（200m以内）と遠く（500m以上）で、どちらにホテルが多いですか？",
        expected_keywords=["駅", "近く", "遠く", "ホテル"],
        description="距離帯別POI比較",
        graph_advantage="distance_zoneによるフィルタ比較"
    ),

    # ==========================================================================
    # 近接性クエリ（2件）- 距離ソート
    # ==========================================================================
    GraphRAGTestCase(
        id="GR-14",
        category="proximity",
        question="渋谷駅に最も近いホテルはどこですか？",
        expected_keywords=["駅", "近い", "ホテル"],
        description="最寄りPOI検索",
        graph_advantage="DISTANCE_FROMエッジによる距離ソート"
    ),
    GraphRAGTestCase(
        id="GR-15",
        category="proximity",
        question="渋谷駅から300m以内にある映画館を距離順に教えてください",
        expected_keywords=["映画館", "300m", "距離"],
        description="距離制約付き近接検索",
        graph_advantage="距離フィルタ + ソート"
    ),

    # ==========================================================================
    # ブランドクエリ（5件）- SAME_BRANDエッジを活用
    # ==========================================================================
    GraphRAGTestCase(
        id="GR-16",
        category="brand",
        question="渋谷にあるスターバックスは何店舗ありますか？",
        expected_keywords=["スターバックス", "店舗", "数"],
        description="チェーン店の店舗数を問う",
        graph_advantage="SAME_BRANDエッジによるチェーン店カウント"
    ),
    GraphRAGTestCase(
        id="GR-17",
        category="brand",
        question="ファミリーマートとローソン、どちらが店舗数が多いですか？",
        expected_keywords=["ファミリーマート", "ローソン", "多い"],
        description="チェーン店間の比較",
        graph_advantage="ブランドノードのPOIカウント比較"
    ),
    GraphRAGTestCase(
        id="GR-18",
        category="brand",
        question="渋谷駅の東側にあるドトールコーヒーを教えてください",
        expected_keywords=["ドトール", "東"],
        description="ブランド + 方向でのフィルタ",
        graph_advantage="SAME_BRAND + 方向属性フィルタ"
    ),
    GraphRAGTestCase(
        id="GR-19",
        category="brand",
        question="マクドナルドの近くにあるスターバックスはありますか？",
        expected_keywords=["マクドナルド", "スターバックス", "近く"],
        description="異なるブランド間の近接関係",
        graph_advantage="ブランドフィルタ + NEAR_TOエッジ"
    ),
    GraphRAGTestCase(
        id="GR-20",
        category="brand",
        question="渋谷で最も店舗数が多いコンビニチェーンはどこですか？",
        expected_keywords=["コンビニ", "多い", "チェーン"],
        description="カテゴリ内ブランドランキング",
        graph_advantage="カテゴリ + ブランドの集計"
    ),

    # ==========================================================================
    # 補完関係クエリ（5件）- COMPLEMENTARYエッジを活用
    # ==========================================================================
    GraphRAGTestCase(
        id="GR-21",
        category="complementary",
        question="ホテルに泊まる場合、近くで食事できるレストランを教えてください",
        expected_keywords=["ホテル", "レストラン", "近く"],
        description="宿泊と飲食の補完関係",
        graph_advantage="COMPLEMENTARYエッジ（DINING_NEAR_HOTEL）"
    ),
    GraphRAGTestCase(
        id="GR-22",
        category="complementary",
        question="映画を見た後に行けるカフェを探しています",
        expected_keywords=["映画", "カフェ"],
        description="エンタメと飲食の補完関係",
        graph_advantage="COMPLEMENTARYエッジ（ENTERTAINMENT_COMBO）"
    ),
    GraphRAGTestCase(
        id="GR-23",
        category="complementary",
        question="渋谷駅を出てすぐのところで軽食を取れる場所はありますか？",
        expected_keywords=["駅", "軽食", "近く"],
        description="交通と飲食の補完関係",
        graph_advantage="COMPLEMENTARYエッジ（TRANSIT_AMENITY）"
    ),
    GraphRAGTestCase(
        id="GR-24",
        category="complementary",
        question="本屋で本を買った後にコーヒーを飲めるカフェは近くにありますか？",
        expected_keywords=["本屋", "書店", "カフェ", "コーヒー"],
        description="レジャーの補完関係",
        graph_advantage="COMPLEMENTARYエッジ（LEISURE_COMBO）"
    ),
    GraphRAGTestCase(
        id="GR-25",
        category="complementary",
        question="観光名所の近くで食事ができる場所を教えてください",
        expected_keywords=["観光", "名所", "食事"],
        description="観光と飲食の補完関係",
        graph_advantage="COMPLEMENTARYエッジ（TOURISM_COMBO）"
    ),

    # ==========================================================================
    # 競合関係クエリ（3件）- COMPETITORエッジを活用
    # ==========================================================================
    GraphRAGTestCase(
        id="GR-26",
        category="competitor",
        question="このカフェが混んでいる場合、近くに代わりのカフェはありますか？",
        expected_keywords=["カフェ", "代わり", "近く"],
        description="同カテゴリの代替POI検索",
        graph_advantage="COMPETITORエッジで代替店舗を提示"
    ),
    GraphRAGTestCase(
        id="GR-27",
        category="competitor",
        question="渋谷駅周辺でラーメン屋が密集しているエリアはどこですか？",
        expected_keywords=["ラーメン", "密集", "エリア"],
        description="競合店舗の密集エリア検出",
        graph_advantage="COMPETITORエッジの密度分析"
    ),
    GraphRAGTestCase(
        id="GR-28",
        category="competitor",
        question="この居酒屋の他に、同じエリアで別の選択肢を教えてください",
        expected_keywords=["居酒屋", "選択肢", "エリア"],
        description="同カテゴリ・同エリアの代替",
        graph_advantage="COMPETITOR + SAME_AREAエッジ"
    ),

    # ==========================================================================
    # 料理ジャンルクエリ（4件）- SAME_CUISINEエッジを活用
    # ==========================================================================
    GraphRAGTestCase(
        id="GR-29",
        category="cuisine",
        question="渋谷でイタリアン料理を食べられるお店を教えてください",
        expected_keywords=["イタリアン", "料理", "店"],
        description="料理ジャンルでの検索",
        graph_advantage="SAME_CUISINEエッジによるジャンル検索"
    ),
    GraphRAGTestCase(
        id="GR-30",
        category="cuisine",
        question="和食と洋食、どちらの店が渋谷には多いですか？",
        expected_keywords=["和食", "洋食", "多い"],
        description="料理ジャンル間の比較",
        graph_advantage="cuisine属性による集計比較"
    ),
    GraphRAGTestCase(
        id="GR-31",
        category="cuisine",
        question="ラーメン屋が集まっているエリアを教えてください",
        expected_keywords=["ラーメン", "集まっている", "エリア"],
        description="特定ジャンルの集積エリア検出",
        graph_advantage="SAME_CUISINE + SAME_AREAの組み合わせ"
    ),
    GraphRAGTestCase(
        id="GR-32",
        category="cuisine",
        question="寿司屋の近くにある別の和食店を教えてください",
        expected_keywords=["寿司", "和食", "近く"],
        description="同系統ジャンルの近接検索",
        graph_advantage="cuisineフィルタ + NEAR_TOエッジ"
    ),

    # ==========================================================================
    # 営業時間クエリ（3件）- SAME_HOURSエッジを活用
    # ==========================================================================
    GraphRAGTestCase(
        id="GR-33",
        category="hours",
        question="渋谷で24時間営業のお店を教えてください",
        expected_keywords=["24時間", "営業"],
        description="24時間営業店舗の検索",
        graph_advantage="is_24h属性によるフィルタ"
    ),
    GraphRAGTestCase(
        id="GR-34",
        category="hours",
        question="深夜でも食事ができるレストランはありますか？",
        expected_keywords=["深夜", "食事", "レストラン"],
        description="深夜営業店舗の検索",
        graph_advantage="late_night属性によるフィルタ"
    ),
    GraphRAGTestCase(
        id="GR-35",
        category="hours",
        question="早朝から営業しているカフェを教えてください",
        expected_keywords=["早朝", "営業", "カフェ"],
        description="早朝営業店舗の検索",
        graph_advantage="early_morning属性によるフィルタ"
    ),
]


def get_graphrag_test_cases() -> List[GraphRAGTestCase]:
    """GraphRAGテストケースを取得"""
    return GRAPHRAG_TEST_CASES


def get_graphrag_test_cases_by_category(category: str) -> List[GraphRAGTestCase]:
    """カテゴリ別にテストケースを取得"""
    return [tc for tc in GRAPHRAG_TEST_CASES if tc.category == category]


def get_graphrag_test_case_stats() -> dict:
    """テストケースの統計情報を取得"""
    from collections import Counter
    categories = Counter(tc.category for tc in GRAPHRAG_TEST_CASES)
    return {
        "total": len(GRAPHRAG_TEST_CASES),
        "by_category": dict(categories)
    }


if __name__ == "__main__":
    stats = get_graphrag_test_case_stats()
    print(f"GraphRAGテストケース総数: {stats['total']}件")
    print(f"\nカテゴリ別:")
    for cat, count in stats["by_category"].items():
        print(f"  {cat}: {count}件")
