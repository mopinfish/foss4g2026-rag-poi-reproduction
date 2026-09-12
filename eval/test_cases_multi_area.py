#!/usr/bin/env python3
"""
test_cases_multi_area.py - Phase 9-B: 複数エリア対応テストケース（130件）

テスト構成:
- A. エリア別テスト: 80件（4エリア × 20件、各エリアL1-L5 × 4件）
- B. クロスエリアテスト: 20件（エリア間比較・参照・集計・条件付き）
- C. ランドマークテスト: 15件（空間推論・制約充足・複合推論）
- D. エリア検出テスト: 15件（明示的・暗黙的・不明）

対象エリア:
- shibuya（渋谷）: MA-SBY-L{1-5}-{01-04}
- shinjuku（新宿）: MA-SJK-L{1-5}-{01-04}
- ikebukuro（池袋）: MA-IKB-L{1-5}-{01-04}
- tokyo（東京）: MA-TKY-L{1-5}-{01-04}

作成日: 2026-02-18
プロジェクト: experiments-local-llm
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict

try:
    from .geo_utils import LANDMARKS
except ImportError:
    from geo_utils import LANDMARKS


# =============================================================================
# データクラス定義
# =============================================================================

@dataclass
class MultiAreaTestCase:
    """複数エリア対応テストケース定義（Phase 9-B用）"""
    id: str                          # "MA-SBY-L1-01" 形式
    level: int                       # 1-5
    category: str                    # テストカテゴリ
    subcategory: str                 # subcategory体系に準拠
    prompt: str                      # 質問文
    expected_keywords: List[str]     # 期待キーワード
    difficulty: str                  # easy/medium/hard/expert
    description: str                 # テスト説明
    evaluation_points: List[str]     # 評価ポイント
    target_area: Optional[str] = None        # "shibuya" etc. None=cross-area
    target_areas: Optional[List[str]] = None # cross-area用
    query_type: str = "single_area"          # "single_area" or "cross_area"
    expected_poi_category: Optional[str] = None
    constraints: Optional[List[str]] = None

    @property
    def level_name(self) -> str:
        """レベル名を取得"""
        level_names = {
            1: "基礎検索",
            2: "空間推論",
            3: "制約充足",
            4: "意思決定支援",
            5: "高度推論"
        }
        return level_names.get(self.level, "不明")


# =============================================================================
# 渋谷テストケースとV2マッピング
# =============================================================================

SHIBUYA_V2_MAPPING = {
    "MA-SBY-L1-01": "L1-01",
    "MA-SBY-L1-02": "L1-06",
    "MA-SBY-L2-01": "L2-01",
    "MA-SBY-L2-02": "L2-07",
    "MA-SBY-L2-03": "L2-11",
    "MA-SBY-L3-01": "L3-05",
    "MA-SBY-L3-02": "L3-06",
    # others are new
}


# =============================================================================
# A. エリア別テスト: 渋谷（20件）
# =============================================================================

SHIBUYA_TEST_CASES = [
    # L1 (4件)
    MultiAreaTestCase(
        id="MA-SBY-L1-01",
        level=1,
        category="basic_retrieval",
        subcategory="basic_location",
        prompt="渋谷駅の場所を教えてください",
        expected_keywords=["渋谷", "駅", "35.", "139."],
        difficulty="easy",
        description="渋谷駅の位置検索",
        evaluation_points=["座標情報の提供", "POI名の含有"],
        target_area="shibuya",
        expected_poi_category="交通/鉄道駅",
    ),
    MultiAreaTestCase(
        id="MA-SBY-L1-02",
        level=1,
        category="basic_retrieval",
        subcategory="basic_location",
        prompt="渋谷駅周辺のコンビニを教えてください",
        expected_keywords=["コンビニ", "ローソン", "ファミリーマート", "セブン"],
        difficulty="easy",
        description="渋谷駅周辺のコンビニ検索",
        evaluation_points=["複数POIの列挙"],
        target_area="shibuya",
        expected_poi_category="商店/コンビニ",
    ),
    MultiAreaTestCase(
        id="MA-SBY-L1-03",
        level=1,
        category="basic_retrieval",
        subcategory="brand",
        prompt="渋谷駅周辺のスターバックスはありますか？",
        expected_keywords=["スターバックス", "渋谷"],
        difficulty="easy",
        description="渋谷駅周辺のスターバックス検索",
        evaluation_points=["ブランド名の認識", "POIの列挙"],
        target_area="shibuya",
        expected_poi_category="飲食店/カフェ",
    ),
    MultiAreaTestCase(
        id="MA-SBY-L1-04",
        level=1,
        category="basic_retrieval",
        subcategory="area_detection",
        prompt="渋谷駅近くのカフェはありますか？",
        expected_keywords=["カフェ", "渋谷"],
        difficulty="easy",
        description="渋谷エリア検出+カフェ検索",
        evaluation_points=["エリアの正しい検出", "カフェの列挙"],
        target_area="shibuya",
        expected_poi_category="飲食店/カフェ",
    ),

    # L2 (4件)
    MultiAreaTestCase(
        id="MA-SBY-L2-01",
        level=2,
        category="spatial_reasoning",
        subcategory="proximity",
        prompt="渋谷駅に最も近いコンビニはどれですか？距離も推定してください",
        expected_keywords=["コンビニ", "近い", "距離", "m"],
        difficulty="medium",
        description="渋谷駅最近傍コンビニの検索と距離推定",
        evaluation_points=["最近傍選択", "距離推定"],
        target_area="shibuya",
        expected_poi_category="商店/コンビニ",
    ),
    MultiAreaTestCase(
        id="MA-SBY-L2-02",
        level=2,
        category="spatial_reasoning",
        subcategory="aggregation",
        prompt="渋谷駅周辺のカフェとバー、どちらが多いですか？",
        expected_keywords=["カフェ", "バー", "多い", "数"],
        difficulty="medium",
        description="渋谷駅周辺のカフェ・バー件数比較",
        evaluation_points=["カウント比較", "数値の提示"],
        target_area="shibuya",
    ),
    MultiAreaTestCase(
        id="MA-SBY-L2-03",
        level=2,
        category="spatial_reasoning",
        subcategory="comparison",
        prompt="渋谷駅の東側と西側、どちらにカフェが多いですか？",
        expected_keywords=["カフェ", "東", "西", "多い"],
        difficulty="medium",
        description="渋谷駅の東西カフェ比較",
        evaluation_points=["方向別比較", "定量的判断"],
        target_area="shibuya",
    ),
    MultiAreaTestCase(
        id="MA-SBY-L2-04",
        level=2,
        category="spatial_reasoning",
        subcategory="landmark_origin",
        prompt="渋谷ヒカリエから最も近いカフェはどこですか？",
        expected_keywords=["カフェ", "ヒカリエ", "近い"],
        difficulty="medium",
        description="渋谷ヒカリエ起点の最近傍カフェ検索",
        evaluation_points=["ランドマーク起点の検索", "最近傍選択"],
        target_area="shibuya",
        expected_poi_category="飲食店/カフェ",
    ),

    # L3 (4件)
    MultiAreaTestCase(
        id="MA-SBY-L3-01",
        level=3,
        category="constraint_satisfaction",
        subcategory="constraint_single",
        prompt="渋谷駅周辺で24時間営業のコンビニはありますか？",
        expected_keywords=["コンビニ", "24時間", "営業"],
        difficulty="medium",
        description="渋谷駅周辺の24時間営業コンビニ検索",
        evaluation_points=["営業時間制約の充足"],
        target_area="shibuya",
        constraints=["24時間営業"],
    ),
    MultiAreaTestCase(
        id="MA-SBY-L3-02",
        level=3,
        category="constraint_satisfaction",
        subcategory="constraint_multi",
        prompt="渋谷駅から500m以内で、電話番号がわかるカフェを教えてください",
        expected_keywords=["カフェ", "500m", "電話"],
        difficulty="hard",
        description="渋谷駅周辺の距離+属性制約付きカフェ検索",
        evaluation_points=["距離制約の充足", "属性制約の充足"],
        target_area="shibuya",
        constraints=["距離500m以内", "電話番号あり"],
    ),
    MultiAreaTestCase(
        id="MA-SBY-L3-03",
        level=3,
        category="constraint_satisfaction",
        subcategory="brand",
        prompt="渋谷駅周辺のドトールを全て教えてください",
        expected_keywords=["ドトール", "渋谷"],
        difficulty="medium",
        description="渋谷駅周辺のドトール全店舗検索",
        evaluation_points=["ブランド名の認識", "網羅的な列挙"],
        target_area="shibuya",
        expected_poi_category="飲食店/カフェ",
    ),
    MultiAreaTestCase(
        id="MA-SBY-L3-04",
        level=3,
        category="constraint_satisfaction",
        subcategory="landmark_origin",
        prompt="渋谷109の近くでランチができるレストランは？",
        expected_keywords=["109", "レストラン", "ランチ"],
        difficulty="medium",
        description="渋谷109起点のランチレストラン検索",
        evaluation_points=["ランドマーク起点の検索", "用途制約の充足"],
        target_area="shibuya",
        expected_poi_category="飲食店/レストラン",
    ),

    # L4 (4件)
    MultiAreaTestCase(
        id="MA-SBY-L4-01",
        level=4,
        category="decision_support",
        subcategory="decision_support",
        prompt="渋谷駅から近い順にカフェを3つ教えてください",
        expected_keywords=["カフェ", "近い", "順", "3"],
        difficulty="hard",
        description="渋谷駅からのカフェ距離順ランキング",
        evaluation_points=["距離順ソート", "件数指定の充足"],
        target_area="shibuya",
        expected_poi_category="飲食店/カフェ",
    ),
    MultiAreaTestCase(
        id="MA-SBY-L4-02",
        level=4,
        category="decision_support",
        subcategory="relation",
        prompt="渋谷駅周辺でカフェとコンビニが両方近い場所は？",
        expected_keywords=["カフェ", "コンビニ", "近い"],
        difficulty="hard",
        description="渋谷駅周辺のカフェ・コンビニ共近接エリア",
        evaluation_points=["複数POI間の関係分析", "共近接エリアの特定"],
        target_area="shibuya",
    ),
    MultiAreaTestCase(
        id="MA-SBY-L4-03",
        level=4,
        category="decision_support",
        subcategory="landmark_origin",
        prompt="ハチ公像の周辺300mにある飲食店を教えてください",
        expected_keywords=["ハチ公", "300m", "飲食店"],
        difficulty="hard",
        description="ハチ公像起点の飲食店検索（半径指定）",
        evaluation_points=["ランドマーク起点の検索", "距離制約の充足"],
        target_area="shibuya",
        constraints=["ハチ公像から300m以内"],
    ),
    MultiAreaTestCase(
        id="MA-SBY-L4-04",
        level=4,
        category="decision_support",
        subcategory="sensitivity",
        prompt="渋谷駅500m圏と1km圏でカフェの件数はどう変わりますか？",
        expected_keywords=["カフェ", "500m", "1km", "件数"],
        difficulty="hard",
        description="渋谷駅のカフェ半径別件数の感度分析",
        evaluation_points=["半径別件数の比較", "変化の分析"],
        target_area="shibuya",
    ),

    # L5 (4件)
    MultiAreaTestCase(
        id="MA-SBY-L5-01",
        level=5,
        category="advanced_reasoning",
        subcategory="multi_hop",
        prompt="渋谷駅から最も近いカフェと、そこから300m以内の他カフェ数は？",
        expected_keywords=["カフェ", "近い", "300m", "数"],
        difficulty="expert",
        description="渋谷駅のマルチホップ推論（最近傍+周辺カウント）",
        evaluation_points=["マルチホップ推論", "段階的な情報取得"],
        target_area="shibuya",
    ),
    MultiAreaTestCase(
        id="MA-SBY-L5-02",
        level=5,
        category="advanced_reasoning",
        subcategory="competitor",
        prompt="渋谷駅周辺でコンビニの競合状況を分析してください",
        expected_keywords=["コンビニ", "競合", "セブン", "ファミリーマート", "ローソン"],
        difficulty="expert",
        description="渋谷駅周辺のコンビニ競合分析",
        evaluation_points=["競合分析", "ブランド別の比較"],
        target_area="shibuya",
    ),
    MultiAreaTestCase(
        id="MA-SBY-L5-03",
        level=5,
        category="advanced_reasoning",
        subcategory="complementary",
        prompt="渋谷駅周辺でカフェの近くにある書店を教えてください",
        expected_keywords=["カフェ", "書店", "近く"],
        difficulty="expert",
        description="渋谷駅周辺のカフェ・書店の補完関係分析",
        evaluation_points=["補完関係の分析", "POI間近接の検索"],
        target_area="shibuya",
    ),
    MultiAreaTestCase(
        id="MA-SBY-L5-04",
        level=5,
        category="advanced_reasoning",
        subcategory="sensitivity",
        prompt="渋谷駅周辺のカフェの平均距離と最寄り・最遠の距離差は？",
        expected_keywords=["カフェ", "平均", "距離", "最寄り", "最遠"],
        difficulty="expert",
        description="渋谷駅周辺カフェの距離統計分析",
        evaluation_points=["距離統計の算出", "統計的分析"],
        target_area="shibuya",
    ),
]


# =============================================================================
# A. エリア別テスト: 新宿（20件）
# =============================================================================

SHINJUKU_TEST_CASES = [
    # L1 (4件)
    MultiAreaTestCase(
        id="MA-SJK-L1-01",
        level=1,
        category="basic_retrieval",
        subcategory="basic_location",
        prompt="新宿駅の場所を教えてください",
        expected_keywords=["新宿", "駅", "35.", "139."],
        difficulty="easy",
        description="新宿駅の位置検索",
        evaluation_points=["座標情報の提供", "POI名の含有"],
        target_area="shinjuku",
        expected_poi_category="交通/鉄道駅",
    ),
    MultiAreaTestCase(
        id="MA-SJK-L1-02",
        level=1,
        category="basic_retrieval",
        subcategory="basic_location",
        prompt="新宿駅周辺のコンビニを教えてください",
        expected_keywords=["コンビニ", "ファミリーマート", "セブン"],
        difficulty="easy",
        description="新宿駅周辺のコンビニ検索",
        evaluation_points=["複数POIの列挙"],
        target_area="shinjuku",
        expected_poi_category="商店/コンビニ",
    ),
    MultiAreaTestCase(
        id="MA-SJK-L1-03",
        level=1,
        category="basic_retrieval",
        subcategory="brand",
        prompt="新宿駅周辺のスターバックスはありますか？",
        expected_keywords=["スターバックス", "新宿"],
        difficulty="easy",
        description="新宿駅周辺のスターバックス検索",
        evaluation_points=["ブランド名の認識", "POIの列挙"],
        target_area="shinjuku",
        expected_poi_category="飲食店/カフェ",
    ),
    MultiAreaTestCase(
        id="MA-SJK-L1-04",
        level=1,
        category="basic_retrieval",
        subcategory="area_detection",
        prompt="新宿駅近くのカフェはありますか？",
        expected_keywords=["カフェ", "新宿"],
        difficulty="easy",
        description="新宿エリア検出+カフェ検索",
        evaluation_points=["エリアの正しい検出", "カフェの列挙"],
        target_area="shinjuku",
        expected_poi_category="飲食店/カフェ",
    ),

    # L2 (4件)
    MultiAreaTestCase(
        id="MA-SJK-L2-01",
        level=2,
        category="spatial_reasoning",
        subcategory="proximity",
        prompt="新宿駅に最も近いコンビニはどれですか？",
        expected_keywords=["コンビニ", "近い", "距離"],
        difficulty="medium",
        description="新宿駅最近傍コンビニの検索",
        evaluation_points=["最近傍選択", "距離推定"],
        target_area="shinjuku",
        expected_poi_category="商店/コンビニ",
    ),
    MultiAreaTestCase(
        id="MA-SJK-L2-02",
        level=2,
        category="spatial_reasoning",
        subcategory="aggregation",
        prompt="新宿駅から500m以内にカフェは何件ありますか？",
        expected_keywords=["カフェ", "500m", "件"],
        difficulty="medium",
        description="新宿駅500m圏内のカフェ件数",
        evaluation_points=["半径フィルタ", "件数カウント"],
        target_area="shinjuku",
    ),
    MultiAreaTestCase(
        id="MA-SJK-L2-03",
        level=2,
        category="spatial_reasoning",
        subcategory="comparison",
        prompt="新宿駅の東側と西側、どちらに飲食店が多いですか？",
        expected_keywords=["飲食店", "東", "西", "多い"],
        difficulty="medium",
        description="新宿駅の東西飲食店比較",
        evaluation_points=["方向別比較", "定量的判断"],
        target_area="shinjuku",
    ),
    MultiAreaTestCase(
        id="MA-SJK-L2-04",
        level=2,
        category="spatial_reasoning",
        subcategory="landmark_origin",
        prompt="新宿御苑から最も近いカフェはどこですか？",
        expected_keywords=["カフェ", "新宿御苑", "近い"],
        difficulty="medium",
        description="新宿御苑起点の最近傍カフェ検索",
        evaluation_points=["ランドマーク起点の検索", "最近傍選択"],
        target_area="shinjuku",
        expected_poi_category="飲食店/カフェ",
    ),

    # L3 (4件)
    MultiAreaTestCase(
        id="MA-SJK-L3-01",
        level=3,
        category="constraint_satisfaction",
        subcategory="constraint_single",
        prompt="新宿駅周辺で24時間営業のコンビニは？",
        expected_keywords=["コンビニ", "24時間", "営業"],
        difficulty="medium",
        description="新宿駅周辺の24時間営業コンビニ検索",
        evaluation_points=["営業時間制約の充足"],
        target_area="shinjuku",
        constraints=["24時間営業"],
    ),
    MultiAreaTestCase(
        id="MA-SJK-L3-02",
        level=3,
        category="constraint_satisfaction",
        subcategory="constraint_multi",
        prompt="新宿駅から300m以内でWi-Fiが使えるカフェは？",
        expected_keywords=["カフェ", "300m", "Wi-Fi"],
        difficulty="hard",
        description="新宿駅周辺の距離+Wi-Fi制約付きカフェ検索",
        evaluation_points=["距離制約の充足", "Wi-Fi制約の充足"],
        target_area="shinjuku",
        constraints=["距離300m以内", "Wi-Fiあり"],
    ),
    MultiAreaTestCase(
        id="MA-SJK-L3-03",
        level=3,
        category="constraint_satisfaction",
        subcategory="brand",
        prompt="新宿駅周辺のドトールを全て教えてください",
        expected_keywords=["ドトール", "新宿"],
        difficulty="medium",
        description="新宿駅周辺のドトール全店舗検索",
        evaluation_points=["ブランド名の認識", "網羅的な列挙"],
        target_area="shinjuku",
        expected_poi_category="飲食店/カフェ",
    ),
    MultiAreaTestCase(
        id="MA-SJK-L3-04",
        level=3,
        category="constraint_satisfaction",
        subcategory="landmark_origin",
        prompt="東京都庁の近くでランチができるレストランは？",
        expected_keywords=["都庁", "レストラン", "ランチ"],
        difficulty="medium",
        description="東京都庁起点のランチレストラン検索",
        evaluation_points=["ランドマーク起点の検索", "用途制約の充足"],
        target_area="shinjuku",
        expected_poi_category="飲食店/レストラン",
    ),

    # L4 (4件)
    MultiAreaTestCase(
        id="MA-SJK-L4-01",
        level=4,
        category="decision_support",
        subcategory="decision_support",
        prompt="新宿駅から近い順にカフェを3つ教えてください",
        expected_keywords=["カフェ", "近い", "順", "3"],
        difficulty="hard",
        description="新宿駅からのカフェ距離順ランキング",
        evaluation_points=["距離順ソート", "件数指定の充足"],
        target_area="shinjuku",
        expected_poi_category="飲食店/カフェ",
    ),
    MultiAreaTestCase(
        id="MA-SJK-L4-02",
        level=4,
        category="decision_support",
        subcategory="relation",
        prompt="新宿駅周辺でカフェとコンビニが両方近い場所は？",
        expected_keywords=["カフェ", "コンビニ", "近い"],
        difficulty="hard",
        description="新宿駅周辺のカフェ・コンビニ共近接エリア",
        evaluation_points=["複数POI間の関係分析", "共近接エリアの特定"],
        target_area="shinjuku",
    ),
    MultiAreaTestCase(
        id="MA-SJK-L4-03",
        level=4,
        category="decision_support",
        subcategory="landmark_origin",
        prompt="歌舞伎町の周辺300mにある飲食店を教えてください",
        expected_keywords=["歌舞伎町", "300m", "飲食店"],
        difficulty="hard",
        description="歌舞伎町起点の飲食店検索（半径指定）",
        evaluation_points=["ランドマーク起点の検索", "距離制約の充足"],
        target_area="shinjuku",
        constraints=["歌舞伎町から300m以内"],
    ),
    MultiAreaTestCase(
        id="MA-SJK-L4-04",
        level=4,
        category="decision_support",
        subcategory="sensitivity",
        prompt="新宿駅500m圏と1km圏でカフェの件数はどう変わりますか？",
        expected_keywords=["カフェ", "500m", "1km", "件数"],
        difficulty="hard",
        description="新宿駅のカフェ半径別件数の感度分析",
        evaluation_points=["半径別件数の比較", "変化の分析"],
        target_area="shinjuku",
    ),

    # L5 (4件)
    MultiAreaTestCase(
        id="MA-SJK-L5-01",
        level=5,
        category="advanced_reasoning",
        subcategory="multi_hop",
        prompt="新宿駅から最も近いカフェと、そこから300m以内の他カフェ数は？",
        expected_keywords=["カフェ", "近い", "300m", "数"],
        difficulty="expert",
        description="新宿駅のマルチホップ推論（最近傍+周辺カウント）",
        evaluation_points=["マルチホップ推論", "段階的な情報取得"],
        target_area="shinjuku",
    ),
    MultiAreaTestCase(
        id="MA-SJK-L5-02",
        level=5,
        category="advanced_reasoning",
        subcategory="competitor",
        prompt="新宿駅周辺でコンビニの競合状況を分析してください",
        expected_keywords=["コンビニ", "競合", "セブン", "ファミリーマート"],
        difficulty="expert",
        description="新宿駅周辺のコンビニ競合分析",
        evaluation_points=["競合分析", "ブランド別の比較"],
        target_area="shinjuku",
    ),
    MultiAreaTestCase(
        id="MA-SJK-L5-03",
        level=5,
        category="advanced_reasoning",
        subcategory="complementary",
        prompt="新宿駅周辺でカフェの近くにある書店を教えてください",
        expected_keywords=["カフェ", "書店", "近く", "紀伊國屋"],
        difficulty="expert",
        description="新宿駅周辺のカフェ・書店の補完関係分析",
        evaluation_points=["補完関係の分析", "POI間近接の検索"],
        target_area="shinjuku",
    ),
    MultiAreaTestCase(
        id="MA-SJK-L5-04",
        level=5,
        category="advanced_reasoning",
        subcategory="sensitivity",
        prompt="新宿駅周辺のカフェの平均距離と最寄り・最遠の距離差は？",
        expected_keywords=["カフェ", "平均", "距離", "最寄り", "最遠"],
        difficulty="expert",
        description="新宿駅周辺カフェの距離統計分析",
        evaluation_points=["距離統計の算出", "統計的分析"],
        target_area="shinjuku",
    ),
]


# =============================================================================
# A. エリア別テスト: 池袋（20件）
# =============================================================================

IKEBUKURO_TEST_CASES = [
    # L1 (4件)
    MultiAreaTestCase(
        id="MA-IKB-L1-01",
        level=1,
        category="basic_retrieval",
        subcategory="basic_location",
        prompt="池袋駅の場所を教えてください",
        expected_keywords=["池袋", "駅", "35.", "139."],
        difficulty="easy",
        description="池袋駅の位置検索",
        evaluation_points=["座標情報の提供", "POI名の含有"],
        target_area="ikebukuro",
        expected_poi_category="交通/鉄道駅",
    ),
    MultiAreaTestCase(
        id="MA-IKB-L1-02",
        level=1,
        category="basic_retrieval",
        subcategory="basic_location",
        prompt="池袋駅周辺のコンビニを教えてください",
        expected_keywords=["コンビニ", "ファミリーマート", "セブン"],
        difficulty="easy",
        description="池袋駅周辺のコンビニ検索",
        evaluation_points=["複数POIの列挙"],
        target_area="ikebukuro",
        expected_poi_category="商店/コンビニ",
    ),
    MultiAreaTestCase(
        id="MA-IKB-L1-03",
        level=1,
        category="basic_retrieval",
        subcategory="brand",
        prompt="池袋駅周辺のスターバックスはありますか？",
        expected_keywords=["スターバックス", "池袋"],
        difficulty="easy",
        description="池袋駅周辺のスターバックス検索",
        evaluation_points=["ブランド名の認識", "POIの列挙"],
        target_area="ikebukuro",
        expected_poi_category="飲食店/カフェ",
    ),
    MultiAreaTestCase(
        id="MA-IKB-L1-04",
        level=1,
        category="basic_retrieval",
        subcategory="area_detection",
        prompt="池袋駅近くのカフェはありますか？",
        expected_keywords=["カフェ", "池袋"],
        difficulty="easy",
        description="池袋エリア検出+カフェ検索",
        evaluation_points=["エリアの正しい検出", "カフェの列挙"],
        target_area="ikebukuro",
        expected_poi_category="飲食店/カフェ",
    ),

    # L2 (4件)
    MultiAreaTestCase(
        id="MA-IKB-L2-01",
        level=2,
        category="spatial_reasoning",
        subcategory="proximity",
        prompt="池袋駅に最も近いコンビニはどれですか？",
        expected_keywords=["コンビニ", "近い", "距離"],
        difficulty="medium",
        description="池袋駅最近傍コンビニの検索",
        evaluation_points=["最近傍選択", "距離推定"],
        target_area="ikebukuro",
        expected_poi_category="商店/コンビニ",
    ),
    MultiAreaTestCase(
        id="MA-IKB-L2-02",
        level=2,
        category="spatial_reasoning",
        subcategory="aggregation",
        prompt="池袋駅から500m以内にカフェは何件ありますか？",
        expected_keywords=["カフェ", "500m", "件"],
        difficulty="medium",
        description="池袋駅500m圏内のカフェ件数",
        evaluation_points=["半径フィルタ", "件数カウント"],
        target_area="ikebukuro",
    ),
    MultiAreaTestCase(
        id="MA-IKB-L2-03",
        level=2,
        category="spatial_reasoning",
        subcategory="comparison",
        prompt="池袋駅の東側と西側、どちらに飲食店が多いですか？",
        expected_keywords=["飲食店", "東", "西", "多い"],
        difficulty="medium",
        description="池袋駅の東西飲食店比較",
        evaluation_points=["方向別比較", "定量的判断"],
        target_area="ikebukuro",
    ),
    MultiAreaTestCase(
        id="MA-IKB-L2-04",
        level=2,
        category="spatial_reasoning",
        subcategory="landmark_origin",
        prompt="サンシャインシティから最も近いカフェはどこですか？",
        expected_keywords=["カフェ", "サンシャイン", "近い"],
        difficulty="medium",
        description="サンシャインシティ起点の最近傍カフェ検索",
        evaluation_points=["ランドマーク起点の検索", "最近傍選択"],
        target_area="ikebukuro",
        expected_poi_category="飲食店/カフェ",
    ),

    # L3 (4件)
    MultiAreaTestCase(
        id="MA-IKB-L3-01",
        level=3,
        category="constraint_satisfaction",
        subcategory="constraint_single",
        prompt="池袋駅周辺で24時間営業のコンビニは？",
        expected_keywords=["コンビニ", "24時間", "営業"],
        difficulty="medium",
        description="池袋駅周辺の24時間営業コンビニ検索",
        evaluation_points=["営業時間制約の充足"],
        target_area="ikebukuro",
        constraints=["24時間営業"],
    ),
    MultiAreaTestCase(
        id="MA-IKB-L3-02",
        level=3,
        category="constraint_satisfaction",
        subcategory="constraint_multi",
        prompt="池袋駅から300m以内でWi-Fiが使えるカフェは？",
        expected_keywords=["カフェ", "300m", "Wi-Fi"],
        difficulty="hard",
        description="池袋駅周辺の距離+Wi-Fi制約付きカフェ検索",
        evaluation_points=["距離制約の充足", "Wi-Fi制約の充足"],
        target_area="ikebukuro",
        constraints=["距離300m以内", "Wi-Fiあり"],
    ),
    MultiAreaTestCase(
        id="MA-IKB-L3-03",
        level=3,
        category="constraint_satisfaction",
        subcategory="brand",
        prompt="池袋駅周辺のマツモトキヨシを全て教えてください",
        expected_keywords=["マツモトキヨシ", "池袋"],
        difficulty="medium",
        description="池袋駅周辺のマツモトキヨシ全店舗検索",
        evaluation_points=["ブランド名の認識", "網羅的な列挙"],
        target_area="ikebukuro",
        expected_poi_category="医療/薬局",
    ),
    MultiAreaTestCase(
        id="MA-IKB-L3-04",
        level=3,
        category="constraint_satisfaction",
        subcategory="landmark_origin",
        prompt="池袋西口公園の近くでランチができるレストランは？",
        expected_keywords=["西口公園", "レストラン", "ランチ"],
        difficulty="medium",
        description="池袋西口公園起点のランチレストラン検索",
        evaluation_points=["ランドマーク起点の検索", "用途制約の充足"],
        target_area="ikebukuro",
        expected_poi_category="飲食店/レストラン",
    ),

    # L4 (4件)
    MultiAreaTestCase(
        id="MA-IKB-L4-01",
        level=4,
        category="decision_support",
        subcategory="decision_support",
        prompt="池袋駅から近い順にカフェを3つ教えてください",
        expected_keywords=["カフェ", "近い", "順", "3"],
        difficulty="hard",
        description="池袋駅からのカフェ距離順ランキング",
        evaluation_points=["距離順ソート", "件数指定の充足"],
        target_area="ikebukuro",
        expected_poi_category="飲食店/カフェ",
    ),
    MultiAreaTestCase(
        id="MA-IKB-L4-02",
        level=4,
        category="decision_support",
        subcategory="relation",
        prompt="池袋駅周辺でカフェとコンビニが両方近い場所は？",
        expected_keywords=["カフェ", "コンビニ", "近い"],
        difficulty="hard",
        description="池袋駅周辺のカフェ・コンビニ共近接エリア",
        evaluation_points=["複数POI間の関係分析", "共近接エリアの特定"],
        target_area="ikebukuro",
    ),
    MultiAreaTestCase(
        id="MA-IKB-L4-03",
        level=4,
        category="decision_support",
        subcategory="landmark_origin",
        prompt="東武百貨店池袋店の周辺300mにある飲食店を教えてください",
        expected_keywords=["東武百貨店", "300m", "飲食店"],
        difficulty="hard",
        description="東武百貨店池袋店起点の飲食店検索（半径指定）",
        evaluation_points=["ランドマーク起点の検索", "距離制約の充足"],
        target_area="ikebukuro",
        constraints=["東武百貨店池袋店から300m以内"],
    ),
    MultiAreaTestCase(
        id="MA-IKB-L4-04",
        level=4,
        category="decision_support",
        subcategory="sensitivity",
        prompt="池袋駅500m圏と1km圏でカフェの件数はどう変わりますか？",
        expected_keywords=["カフェ", "500m", "1km", "件数"],
        difficulty="hard",
        description="池袋駅のカフェ半径別件数の感度分析",
        evaluation_points=["半径別件数の比較", "変化の分析"],
        target_area="ikebukuro",
    ),

    # L5 (4件)
    MultiAreaTestCase(
        id="MA-IKB-L5-01",
        level=5,
        category="advanced_reasoning",
        subcategory="multi_hop",
        prompt="池袋駅から最も近いカフェと、そこから300m以内の他カフェ数は？",
        expected_keywords=["カフェ", "近い", "300m", "数"],
        difficulty="expert",
        description="池袋駅のマルチホップ推論（最近傍+周辺カウント）",
        evaluation_points=["マルチホップ推論", "段階的な情報取得"],
        target_area="ikebukuro",
    ),
    MultiAreaTestCase(
        id="MA-IKB-L5-02",
        level=5,
        category="advanced_reasoning",
        subcategory="competitor",
        prompt="池袋駅周辺でコンビニの競合状況を分析してください",
        expected_keywords=["コンビニ", "競合", "セブン", "ファミリーマート"],
        difficulty="expert",
        description="池袋駅周辺のコンビニ競合分析",
        evaluation_points=["競合分析", "ブランド別の比較"],
        target_area="ikebukuro",
    ),
    MultiAreaTestCase(
        id="MA-IKB-L5-03",
        level=5,
        category="advanced_reasoning",
        subcategory="complementary",
        prompt="池袋駅周辺でカフェの近くにある書店を教えてください",
        expected_keywords=["カフェ", "書店", "近く", "ジュンク堂"],
        difficulty="expert",
        description="池袋駅周辺のカフェ・書店の補完関係分析",
        evaluation_points=["補完関係の分析", "POI間近接の検索"],
        target_area="ikebukuro",
    ),
    MultiAreaTestCase(
        id="MA-IKB-L5-04",
        level=5,
        category="advanced_reasoning",
        subcategory="sensitivity",
        prompt="池袋駅周辺のカフェの平均距離と最寄り・最遠の距離差は？",
        expected_keywords=["カフェ", "平均", "距離", "最寄り", "最遠"],
        difficulty="expert",
        description="池袋駅周辺カフェの距離統計分析",
        evaluation_points=["距離統計の算出", "統計的分析"],
        target_area="ikebukuro",
    ),
]


# =============================================================================
# A. エリア別テスト: 東京（20件）
# =============================================================================

TOKYO_TEST_CASES = [
    # L1 (4件)
    MultiAreaTestCase(
        id="MA-TKY-L1-01",
        level=1,
        category="basic_retrieval",
        subcategory="basic_location",
        prompt="東京駅の場所を教えてください",
        expected_keywords=["東京駅", "35.", "139."],
        difficulty="easy",
        description="東京駅の位置検索",
        evaluation_points=["座標情報の提供", "POI名の含有"],
        target_area="tokyo",
        expected_poi_category="交通/鉄道駅",
    ),
    MultiAreaTestCase(
        id="MA-TKY-L1-02",
        level=1,
        category="basic_retrieval",
        subcategory="basic_location",
        prompt="東京駅周辺のコンビニを教えてください",
        expected_keywords=["コンビニ", "ファミリーマート", "セブン"],
        difficulty="easy",
        description="東京駅周辺のコンビニ検索",
        evaluation_points=["複数POIの列挙"],
        target_area="tokyo",
        expected_poi_category="商店/コンビニ",
    ),
    MultiAreaTestCase(
        id="MA-TKY-L1-03",
        level=1,
        category="basic_retrieval",
        subcategory="brand",
        prompt="東京駅周辺のスターバックスはありますか？",
        expected_keywords=["スターバックス", "東京駅"],
        difficulty="easy",
        description="東京駅周辺のスターバックス検索",
        evaluation_points=["ブランド名の認識", "POIの列挙"],
        target_area="tokyo",
        expected_poi_category="飲食店/カフェ",
    ),
    MultiAreaTestCase(
        id="MA-TKY-L1-04",
        level=1,
        category="basic_retrieval",
        subcategory="area_detection",
        prompt="東京駅近くのカフェはありますか？",
        expected_keywords=["カフェ", "東京駅"],
        difficulty="easy",
        description="東京駅エリア検出+カフェ検索",
        evaluation_points=["エリアの正しい検出", "カフェの列挙"],
        target_area="tokyo",
        expected_poi_category="飲食店/カフェ",
    ),

    # L2 (4件)
    MultiAreaTestCase(
        id="MA-TKY-L2-01",
        level=2,
        category="spatial_reasoning",
        subcategory="proximity",
        prompt="東京駅に最も近いコンビニはどれですか？",
        expected_keywords=["コンビニ", "近い", "距離"],
        difficulty="medium",
        description="東京駅最近傍コンビニの検索",
        evaluation_points=["最近傍選択", "距離推定"],
        target_area="tokyo",
        expected_poi_category="商店/コンビニ",
    ),
    MultiAreaTestCase(
        id="MA-TKY-L2-02",
        level=2,
        category="spatial_reasoning",
        subcategory="aggregation",
        prompt="東京駅から500m以内にカフェは何件ありますか？",
        expected_keywords=["カフェ", "500m", "件"],
        difficulty="medium",
        description="東京駅500m圏内のカフェ件数",
        evaluation_points=["半径フィルタ", "件数カウント"],
        target_area="tokyo",
    ),
    MultiAreaTestCase(
        id="MA-TKY-L2-03",
        level=2,
        category="spatial_reasoning",
        subcategory="comparison",
        prompt="東京駅の東側と西側、どちらに飲食店が多いですか？",
        expected_keywords=["飲食店", "東", "西", "多い"],
        difficulty="medium",
        description="東京駅の東西飲食店比較",
        evaluation_points=["方向別比較", "定量的判断"],
        target_area="tokyo",
    ),
    MultiAreaTestCase(
        id="MA-TKY-L2-04",
        level=2,
        category="spatial_reasoning",
        subcategory="landmark_origin",
        prompt="KITTEから最も近いカフェはどこですか？",
        expected_keywords=["カフェ", "KITTE", "近い"],
        difficulty="medium",
        description="KITTE起点の最近傍カフェ検索",
        evaluation_points=["ランドマーク起点の検索", "最近傍選択"],
        target_area="tokyo",
        expected_poi_category="飲食店/カフェ",
    ),

    # L3 (4件)
    MultiAreaTestCase(
        id="MA-TKY-L3-01",
        level=3,
        category="constraint_satisfaction",
        subcategory="constraint_single",
        prompt="東京駅周辺で24時間営業のコンビニは？",
        expected_keywords=["コンビニ", "24時間", "営業"],
        difficulty="medium",
        description="東京駅周辺の24時間営業コンビニ検索",
        evaluation_points=["営業時間制約の充足"],
        target_area="tokyo",
        constraints=["24時間営業"],
    ),
    MultiAreaTestCase(
        id="MA-TKY-L3-02",
        level=3,
        category="constraint_satisfaction",
        subcategory="constraint_multi",
        prompt="東京駅から300m以内でWi-Fiが使えるカフェは？",
        expected_keywords=["カフェ", "300m", "Wi-Fi"],
        difficulty="hard",
        description="東京駅周辺の距離+Wi-Fi制約付きカフェ検索",
        evaluation_points=["距離制約の充足", "Wi-Fi制約の充足"],
        target_area="tokyo",
        constraints=["距離300m以内", "Wi-Fiあり"],
    ),
    MultiAreaTestCase(
        id="MA-TKY-L3-03",
        level=3,
        category="constraint_satisfaction",
        subcategory="brand",
        prompt="東京駅周辺のタリーズコーヒーを全て教えてください",
        expected_keywords=["タリーズ", "東京駅"],
        difficulty="medium",
        description="東京駅周辺のタリーズコーヒー全店舗検索",
        evaluation_points=["ブランド名の認識", "網羅的な列挙"],
        target_area="tokyo",
        expected_poi_category="飲食店/カフェ",
    ),
    MultiAreaTestCase(
        id="MA-TKY-L3-04",
        level=3,
        category="constraint_satisfaction",
        subcategory="landmark_origin",
        prompt="東京国際フォーラムの近くでランチができるレストランは？",
        expected_keywords=["国際フォーラム", "レストラン", "ランチ"],
        difficulty="medium",
        description="東京国際フォーラム起点のランチレストラン検索",
        evaluation_points=["ランドマーク起点の検索", "用途制約の充足"],
        target_area="tokyo",
        expected_poi_category="飲食店/レストラン",
    ),

    # L4 (4件)
    MultiAreaTestCase(
        id="MA-TKY-L4-01",
        level=4,
        category="decision_support",
        subcategory="decision_support",
        prompt="東京駅から近い順にカフェを3つ教えてください",
        expected_keywords=["カフェ", "近い", "順", "3"],
        difficulty="hard",
        description="東京駅からのカフェ距離順ランキング",
        evaluation_points=["距離順ソート", "件数指定の充足"],
        target_area="tokyo",
        expected_poi_category="飲食店/カフェ",
    ),
    MultiAreaTestCase(
        id="MA-TKY-L4-02",
        level=4,
        category="decision_support",
        subcategory="relation",
        prompt="東京駅周辺でカフェとコンビニが両方近い場所は？",
        expected_keywords=["カフェ", "コンビニ", "近い"],
        difficulty="hard",
        description="東京駅周辺のカフェ・コンビニ共近接エリア",
        evaluation_points=["複数POI間の関係分析", "共近接エリアの特定"],
        target_area="tokyo",
    ),
    MultiAreaTestCase(
        id="MA-TKY-L4-03",
        level=4,
        category="decision_support",
        subcategory="landmark_origin",
        prompt="丸ビルの周辺300mにある飲食店を教えてください",
        expected_keywords=["丸ビル", "300m", "飲食店"],
        difficulty="hard",
        description="丸ビル起点の飲食店検索（半径指定）",
        evaluation_points=["ランドマーク起点の検索", "距離制約の充足"],
        target_area="tokyo",
        constraints=["丸ビルから300m以内"],
    ),
    MultiAreaTestCase(
        id="MA-TKY-L4-04",
        level=4,
        category="decision_support",
        subcategory="sensitivity",
        prompt="東京駅500m圏と1km圏でカフェの件数はどう変わりますか？",
        expected_keywords=["カフェ", "500m", "1km", "件数"],
        difficulty="hard",
        description="東京駅のカフェ半径別件数の感度分析",
        evaluation_points=["半径別件数の比較", "変化の分析"],
        target_area="tokyo",
    ),

    # L5 (4件)
    MultiAreaTestCase(
        id="MA-TKY-L5-01",
        level=5,
        category="advanced_reasoning",
        subcategory="multi_hop",
        prompt="東京駅から最も近いカフェと、そこから300m以内の他カフェ数は？",
        expected_keywords=["カフェ", "近い", "300m", "数"],
        difficulty="expert",
        description="東京駅のマルチホップ推論（最近傍+周辺カウント）",
        evaluation_points=["マルチホップ推論", "段階的な情報取得"],
        target_area="tokyo",
    ),
    MultiAreaTestCase(
        id="MA-TKY-L5-02",
        level=5,
        category="advanced_reasoning",
        subcategory="competitor",
        prompt="東京駅周辺でコンビニの競合状況を分析してください",
        expected_keywords=["コンビニ", "競合", "セブン", "ファミリーマート"],
        difficulty="expert",
        description="東京駅周辺のコンビニ競合分析",
        evaluation_points=["競合分析", "ブランド別の比較"],
        target_area="tokyo",
    ),
    MultiAreaTestCase(
        id="MA-TKY-L5-03",
        level=5,
        category="advanced_reasoning",
        subcategory="complementary",
        prompt="東京駅周辺でカフェの近くにある書店を教えてください",
        expected_keywords=["カフェ", "書店", "近く", "丸善"],
        difficulty="expert",
        description="東京駅周辺のカフェ・書店の補完関係分析",
        evaluation_points=["補完関係の分析", "POI間近接の検索"],
        target_area="tokyo",
    ),
    MultiAreaTestCase(
        id="MA-TKY-L5-04",
        level=5,
        category="advanced_reasoning",
        subcategory="sensitivity",
        prompt="東京駅周辺のカフェの平均距離と最寄り・最遠の距離差は？",
        expected_keywords=["カフェ", "平均", "距離", "最寄り", "最遠"],
        difficulty="expert",
        description="東京駅周辺カフェの距離統計分析",
        evaluation_points=["距離統計の算出", "統計的分析"],
        target_area="tokyo",
    ),
]


# =============================================================================
# B. クロスエリアテスト（20件）
# =============================================================================

CROSS_AREA_TEST_CASES = [
    # B1 比較 (8件) - L3, medium
    MultiAreaTestCase(
        id="MA-CROSS-01",
        level=3,
        category="cross_area",
        subcategory="cross_area_comparison",
        prompt="渋谷駅と新宿駅の周辺、カフェが多いのはどちらですか？",
        expected_keywords=["カフェ", "渋谷", "新宿", "多い"],
        difficulty="medium",
        description="渋谷・新宿のカフェ件数比較",
        evaluation_points=["エリア間比較", "定量的判断"],
        target_area=None,
        target_areas=["shibuya", "shinjuku"],
        query_type="cross_area",
    ),
    MultiAreaTestCase(
        id="MA-CROSS-02",
        level=3,
        category="cross_area",
        subcategory="cross_area_comparison",
        prompt="池袋と渋谷で、コンビニの密度が高いのはどちらですか？",
        expected_keywords=["コンビニ", "池袋", "渋谷", "密度"],
        difficulty="medium",
        description="池袋・渋谷のコンビニ密度比較",
        evaluation_points=["エリア間比較", "密度評価"],
        target_area=None,
        target_areas=["ikebukuro", "shibuya"],
        query_type="cross_area",
    ),
    MultiAreaTestCase(
        id="MA-CROSS-03",
        level=3,
        category="cross_area",
        subcategory="cross_area_comparison",
        prompt="東京駅と新宿駅の周辺で、飲食店の種類が豊富なのはどちらですか？",
        expected_keywords=["飲食店", "東京駅", "新宿", "種類"],
        difficulty="medium",
        description="東京・新宿の飲食店多様性比較",
        evaluation_points=["エリア間比較", "カテゴリ多様性の評価"],
        target_area=None,
        target_areas=["tokyo", "shinjuku"],
        query_type="cross_area",
    ),
    MultiAreaTestCase(
        id="MA-CROSS-04",
        level=3,
        category="cross_area",
        subcategory="cross_area_comparison",
        prompt="4エリアの中で最もカフェが多い駅はどこですか？",
        expected_keywords=["カフェ", "多い", "駅"],
        difficulty="medium",
        description="4エリアのカフェ件数ランキング",
        evaluation_points=["全エリア比較", "ランキング作成"],
        target_area=None,
        target_areas=["shibuya", "shinjuku", "ikebukuro", "tokyo"],
        query_type="cross_area",
    ),
    MultiAreaTestCase(
        id="MA-CROSS-05",
        level=3,
        category="cross_area",
        subcategory="cross_area_comparison",
        prompt="渋谷と池袋、24時間営業の店舗が多いのはどちらですか？",
        expected_keywords=["24時間", "渋谷", "池袋", "多い"],
        difficulty="medium",
        description="渋谷・池袋の24時間営業店舗比較",
        evaluation_points=["エリア間比較", "営業時間による絞り込み"],
        target_area=None,
        target_areas=["shibuya", "ikebukuro"],
        query_type="cross_area",
    ),
    MultiAreaTestCase(
        id="MA-CROSS-06",
        level=3,
        category="cross_area",
        subcategory="cross_area_comparison",
        prompt="スターバックスが最も多いエリアはどこですか？",
        expected_keywords=["スターバックス", "多い", "エリア"],
        difficulty="medium",
        description="4エリアのスターバックス件数ランキング",
        evaluation_points=["全エリア比較", "ブランド別カウント"],
        target_area=None,
        target_areas=["shibuya", "shinjuku", "ikebukuro", "tokyo"],
        query_type="cross_area",
    ),
    MultiAreaTestCase(
        id="MA-CROSS-07",
        level=3,
        category="cross_area",
        subcategory="cross_area_comparison",
        prompt="各エリアで最もPOI密度が高いカテゴリは同じですか？",
        expected_keywords=["カテゴリ", "密度", "エリア"],
        difficulty="medium",
        description="4エリアの主要カテゴリ比較",
        evaluation_points=["全エリア比較", "カテゴリ密度分析"],
        target_area=None,
        target_areas=["shibuya", "shinjuku", "ikebukuro", "tokyo"],
        query_type="cross_area",
    ),
    MultiAreaTestCase(
        id="MA-CROSS-08",
        level=3,
        category="cross_area",
        subcategory="cross_area_comparison",
        prompt="4エリアの中で駅から最も近いカフェがあるのはどこですか？",
        expected_keywords=["カフェ", "近い", "駅"],
        difficulty="medium",
        description="4エリアの最近傍カフェ比較",
        evaluation_points=["全エリア比較", "最近傍距離の比較"],
        target_area=None,
        target_areas=["shibuya", "shinjuku", "ikebukuro", "tokyo"],
        query_type="cross_area",
    ),

    # B2 参照 (5件) - L4, hard
    MultiAreaTestCase(
        id="MA-CROSS-09",
        level=4,
        category="cross_area",
        subcategory="cross_area_comparison",
        prompt="渋谷駅周辺にあるスターバックスは、新宿駅周辺と比べて何店舗差がありますか？",
        expected_keywords=["スターバックス", "渋谷", "新宿", "店舗"],
        difficulty="hard",
        description="渋谷・新宿のスターバックス店舗数差",
        evaluation_points=["エリア間差分の算出", "定量的比較"],
        target_area=None,
        target_areas=["shibuya", "shinjuku"],
        query_type="cross_area",
    ),
    MultiAreaTestCase(
        id="MA-CROSS-10",
        level=4,
        category="cross_area",
        subcategory="cross_area_comparison",
        prompt="東京駅の最寄りカフェと渋谷駅の最寄りカフェ、駅からの距離が近いのはどちらですか？",
        expected_keywords=["カフェ", "東京駅", "渋谷", "距離"],
        difficulty="hard",
        description="東京・渋谷の最寄りカフェ距離比較",
        evaluation_points=["最近傍距離の比較", "エリア間の距離比較"],
        target_area=None,
        target_areas=["tokyo", "shibuya"],
        query_type="cross_area",
    ),
    MultiAreaTestCase(
        id="MA-CROSS-11",
        level=4,
        category="cross_area",
        subcategory="cross_area_comparison",
        prompt="新宿と池袋でマクドナルドの店舗数を比較してください",
        expected_keywords=["マクドナルド", "新宿", "池袋", "店舗"],
        difficulty="hard",
        description="新宿・池袋のマクドナルド店舗数比較",
        evaluation_points=["ブランド別の比較", "エリア間の定量比較"],
        target_area=None,
        target_areas=["shinjuku", "ikebukuro"],
        query_type="cross_area",
    ),
    MultiAreaTestCase(
        id="MA-CROSS-12",
        level=4,
        category="cross_area",
        subcategory="cross_area_comparison",
        prompt="渋谷駅500m圏のコンビニ数と東京駅500m圏のコンビニ数、どちらが多い？",
        expected_keywords=["コンビニ", "渋谷", "東京駅", "500m"],
        difficulty="hard",
        description="渋谷・東京の500m圏コンビニ数比較",
        evaluation_points=["半径制約付きの比較", "エリア間の定量比較"],
        target_area=None,
        target_areas=["shibuya", "tokyo"],
        query_type="cross_area",
    ),
    MultiAreaTestCase(
        id="MA-CROSS-13",
        level=4,
        category="cross_area",
        subcategory="cross_area_comparison",
        prompt="各エリアの最寄りコンビニの距離を比較してください",
        expected_keywords=["コンビニ", "最寄り", "距離", "比較"],
        difficulty="hard",
        description="4エリアの最寄りコンビニ距離比較",
        evaluation_points=["全エリア比較", "最近傍距離の算出"],
        target_area=None,
        target_areas=["shibuya", "shinjuku", "ikebukuro", "tokyo"],
        query_type="cross_area",
    ),

    # B3 集計 (4件) - L2, medium
    MultiAreaTestCase(
        id="MA-CROSS-14",
        level=2,
        category="cross_area",
        subcategory="cross_area_comparison",
        prompt="4エリア全体でコンビニは合計何件ありますか？",
        expected_keywords=["コンビニ", "合計", "件"],
        difficulty="medium",
        description="4エリア全体のコンビニ合計件数",
        evaluation_points=["全エリア集計", "合計値の算出"],
        target_area=None,
        target_areas=["shibuya", "shinjuku", "ikebukuro", "tokyo"],
        query_type="cross_area",
    ),
    MultiAreaTestCase(
        id="MA-CROSS-15",
        level=2,
        category="cross_area",
        subcategory="cross_area_comparison",
        prompt="全エリアで最も多いPOIカテゴリは何ですか？",
        expected_keywords=["カテゴリ", "多い"],
        difficulty="medium",
        description="4エリア全体の最多カテゴリ特定",
        evaluation_points=["全エリア集計", "カテゴリランキング"],
        target_area=None,
        target_areas=["shibuya", "shinjuku", "ikebukuro", "tokyo"],
        query_type="cross_area",
    ),
    MultiAreaTestCase(
        id="MA-CROSS-16",
        level=2,
        category="cross_area",
        subcategory="cross_area_comparison",
        prompt="4エリアの総POI数を教えてください",
        expected_keywords=["POI", "総数"],
        difficulty="medium",
        description="4エリア全体の総POI数",
        evaluation_points=["全エリア集計", "合計値の算出"],
        target_area=None,
        target_areas=["shibuya", "shinjuku", "ikebukuro", "tokyo"],
        query_type="cross_area",
    ),
    MultiAreaTestCase(
        id="MA-CROSS-17",
        level=2,
        category="cross_area",
        subcategory="cross_area_comparison",
        prompt="全エリアのカフェを合計すると何件ですか？",
        expected_keywords=["カフェ", "合計", "件"],
        difficulty="medium",
        description="4エリア全体のカフェ合計件数",
        evaluation_points=["全エリア集計", "カテゴリ別合計"],
        target_area=None,
        target_areas=["shibuya", "shinjuku", "ikebukuro", "tokyo"],
        query_type="cross_area",
    ),

    # B4 条件付き (3件) - L4, hard
    MultiAreaTestCase(
        id="MA-CROSS-18",
        level=4,
        category="cross_area",
        subcategory="cross_area_comparison",
        prompt="ラーメン店が3件以上ある駅はどこですか？",
        expected_keywords=["ラーメン", "3件", "駅"],
        difficulty="hard",
        description="条件付きエリアフィルタリング（ラーメン3件以上）",
        evaluation_points=["条件付きフィルタリング", "全エリア評価"],
        target_area=None,
        target_areas=["shibuya", "shinjuku", "ikebukuro", "tokyo"],
        query_type="cross_area",
    ),
    MultiAreaTestCase(
        id="MA-CROSS-19",
        level=4,
        category="cross_area",
        subcategory="cross_area_comparison",
        prompt="駅から200m以内にカフェが最も多いエリアはどこですか？",
        expected_keywords=["カフェ", "200m", "多い", "エリア"],
        difficulty="hard",
        description="200m圏内カフェ数でのエリアランキング",
        evaluation_points=["半径制約付きの比較", "全エリアランキング"],
        target_area=None,
        target_areas=["shibuya", "shinjuku", "ikebukuro", "tokyo"],
        query_type="cross_area",
    ),
    MultiAreaTestCase(
        id="MA-CROSS-20",
        level=4,
        category="cross_area",
        subcategory="cross_area_comparison",
        prompt="24時間営業のコンビニが10件以上あるエリアはどこですか？",
        expected_keywords=["24時間", "コンビニ", "10件", "エリア"],
        difficulty="hard",
        description="条件付きエリアフィルタリング（24時間コンビニ10件以上）",
        evaluation_points=["条件付きフィルタリング", "全エリア評価"],
        target_area=None,
        target_areas=["shibuya", "shinjuku", "ikebukuro", "tokyo"],
        query_type="cross_area",
    ),
]


# =============================================================================
# C. ランドマークテスト（15件）
# =============================================================================

LANDMARK_TEST_CASES = [
    # C1 空間推論 (5件) - L2, medium
    MultiAreaTestCase(
        id="MA-LM-01",
        level=2,
        category="landmark_query",
        subcategory="landmark_origin",
        prompt="渋谷109から最も近いカフェはどこですか？",
        expected_keywords=["109", "カフェ", "近い"],
        difficulty="medium",
        description="渋谷109起点の最近傍カフェ検索",
        evaluation_points=["ランドマーク起点の検索", "最近傍選択"],
        target_area="shibuya",
        query_type="single_area",
    ),
    MultiAreaTestCase(
        id="MA-LM-02",
        level=2,
        category="landmark_query",
        subcategory="landmark_origin",
        prompt="サンシャインシティから500m以内にコンビニは何件ありますか？",
        expected_keywords=["サンシャイン", "コンビニ", "500m", "件"],
        difficulty="medium",
        description="サンシャインシティ起点のコンビニ件数",
        evaluation_points=["ランドマーク起点の検索", "半径フィルタ"],
        target_area="ikebukuro",
        query_type="single_area",
    ),
    MultiAreaTestCase(
        id="MA-LM-03",
        level=2,
        category="landmark_query",
        subcategory="landmark_origin",
        prompt="東京国際フォーラムの最寄りのレストランを教えてください",
        expected_keywords=["国際フォーラム", "レストラン", "最寄り"],
        difficulty="medium",
        description="東京国際フォーラム起点の最寄りレストラン検索",
        evaluation_points=["ランドマーク起点の検索", "最近傍選択"],
        target_area="tokyo",
        query_type="single_area",
    ),
    MultiAreaTestCase(
        id="MA-LM-04",
        level=2,
        category="landmark_query",
        subcategory="landmark_origin",
        prompt="新宿アルタから一番近い銀行はどこですか？",
        expected_keywords=["アルタ", "銀行", "近い"],
        difficulty="medium",
        description="新宿アルタ起点の最近傍銀行検索",
        evaluation_points=["ランドマーク起点の検索", "最近傍選択"],
        target_area="shinjuku",
        query_type="single_area",
    ),
    MultiAreaTestCase(
        id="MA-LM-05",
        level=2,
        category="landmark_query",
        subcategory="landmark_origin",
        prompt="KITTEから300m以内のカフェを教えてください",
        expected_keywords=["KITTE", "カフェ", "300m"],
        difficulty="medium",
        description="KITTE起点のカフェ検索（半径指定）",
        evaluation_points=["ランドマーク起点の検索", "距離制約の充足"],
        target_area="tokyo",
        query_type="single_area",
    ),

    # C2 制約充足 (5件) - L3, hard
    MultiAreaTestCase(
        id="MA-LM-06",
        level=3,
        category="landmark_query",
        subcategory="landmark_origin",
        prompt="渋谷ヒカリエの近くで24時間営業のコンビニはありますか？",
        expected_keywords=["ヒカリエ", "24時間", "コンビニ"],
        difficulty="hard",
        description="渋谷ヒカリエ起点の24時間コンビニ検索",
        evaluation_points=["ランドマーク起点の検索", "営業時間制約の充足"],
        target_area="shibuya",
        query_type="single_area",
        constraints=["24時間営業"],
    ),
    MultiAreaTestCase(
        id="MA-LM-07",
        level=3,
        category="landmark_query",
        subcategory="landmark_origin",
        prompt="皇居前広場の近くで食事できるレストランは？",
        expected_keywords=["皇居", "レストラン", "食事"],
        difficulty="hard",
        description="皇居前広場起点のレストラン検索",
        evaluation_points=["ランドマーク起点の検索", "用途制約の充足"],
        target_area="tokyo",
        query_type="single_area",
    ),
    MultiAreaTestCase(
        id="MA-LM-08",
        level=3,
        category="landmark_query",
        subcategory="landmark_origin",
        prompt="池袋西口公園の周辺でWi-Fiが使えるカフェは？",
        expected_keywords=["西口公園", "Wi-Fi", "カフェ"],
        difficulty="hard",
        description="池袋西口公園起点のWi-Fi対応カフェ検索",
        evaluation_points=["ランドマーク起点の検索", "Wi-Fi制約の充足"],
        target_area="ikebukuro",
        query_type="single_area",
        constraints=["Wi-Fiあり"],
    ),
    MultiAreaTestCase(
        id="MA-LM-09",
        level=3,
        category="landmark_query",
        subcategory="landmark_origin",
        prompt="丸ビルの近くでスターバックスはありますか？",
        expected_keywords=["丸ビル", "スターバックス"],
        difficulty="hard",
        description="丸ビル起点のスターバックス検索",
        evaluation_points=["ランドマーク起点の検索", "ブランド名の認識"],
        target_area="tokyo",
        query_type="single_area",
    ),
    MultiAreaTestCase(
        id="MA-LM-10",
        level=3,
        category="landmark_query",
        subcategory="landmark_origin",
        prompt="歌舞伎町の近くで深夜営業しているバーは？",
        expected_keywords=["歌舞伎町", "深夜", "バー"],
        difficulty="hard",
        description="歌舞伎町起点の深夜営業バー検索",
        evaluation_points=["ランドマーク起点の検索", "営業時間制約の充足"],
        target_area="shinjuku",
        query_type="single_area",
        constraints=["深夜営業"],
    ),

    # C3 複合推論 (5件) - L4, hard
    MultiAreaTestCase(
        id="MA-LM-11",
        level=4,
        category="landmark_query",
        subcategory="landmark_origin",
        prompt="東京都庁から最も近いカフェと、その駅からの距離は？",
        expected_keywords=["都庁", "カフェ", "駅", "距離"],
        difficulty="hard",
        description="東京都庁起点の最近傍カフェ+駅距離の複合推論",
        evaluation_points=["ランドマーク起点の検索", "マルチホップ推論"],
        target_area="shinjuku",
        query_type="single_area",
    ),
    MultiAreaTestCase(
        id="MA-LM-12",
        level=4,
        category="landmark_query",
        subcategory="landmark_origin",
        prompt="サンシャインシティの近くにあるカフェとコンビニの数は？",
        expected_keywords=["サンシャイン", "カフェ", "コンビニ", "数"],
        difficulty="hard",
        description="サンシャインシティ周辺のカフェ・コンビニ件数",
        evaluation_points=["ランドマーク起点の検索", "複数カテゴリのカウント"],
        target_area="ikebukuro",
        query_type="single_area",
    ),
    MultiAreaTestCase(
        id="MA-LM-13",
        level=4,
        category="landmark_query",
        subcategory="landmark_origin",
        prompt="渋谷スクランブルスクエアの周辺で飲食店のカテゴリ別件数は？",
        expected_keywords=["スクランブルスクエア", "飲食店", "カテゴリ", "件数"],
        difficulty="hard",
        description="渋谷スクランブルスクエア周辺の飲食店カテゴリ分析",
        evaluation_points=["ランドマーク起点の検索", "カテゴリ別集計"],
        target_area="shibuya",
        query_type="single_area",
    ),
    MultiAreaTestCase(
        id="MA-LM-14",
        level=4,
        category="landmark_query",
        subcategory="landmark_origin",
        prompt="新宿御苑から最寄りのカフェまでの距離と方角は？",
        expected_keywords=["新宿御苑", "カフェ", "距離", "方角"],
        difficulty="hard",
        description="新宿御苑起点の最近傍カフェ距離・方角",
        evaluation_points=["ランドマーク起点の検索", "距離・方角の算出"],
        target_area="shinjuku",
        query_type="single_area",
    ),
    MultiAreaTestCase(
        id="MA-LM-15",
        level=4,
        category="landmark_query",
        subcategory="landmark_origin",
        prompt="ハチ公像から見て東側にあるカフェを教えてください",
        expected_keywords=["ハチ公", "東", "カフェ"],
        difficulty="hard",
        description="ハチ公像起点の東側カフェ検索",
        evaluation_points=["ランドマーク起点の検索", "方向フィルタ"],
        target_area="shibuya",
        query_type="single_area",
    ),
]


# =============================================================================
# D. エリア検出テスト（15件）
# =============================================================================

DETECTION_TEST_CASES = [
    # D1 明示的 (5件) - L1, easy
    MultiAreaTestCase(
        id="MA-DET-01",
        level=1,
        category="area_detection",
        subcategory="area_detection",
        prompt="池袋駅周辺のホテルを教えてください",
        expected_keywords=["池袋", "ホテル"],
        difficulty="easy",
        description="池袋エリアの明示的検出+ホテル検索",
        evaluation_points=["エリアの正しい検出"],
        target_area="ikebukuro",
        query_type="single_area",
    ),
    MultiAreaTestCase(
        id="MA-DET-02",
        level=1,
        category="area_detection",
        subcategory="area_detection",
        prompt="東京駅近くの銀行はありますか？",
        expected_keywords=["東京駅", "銀行"],
        difficulty="easy",
        description="東京駅エリアの明示的検出+銀行検索",
        evaluation_points=["エリアの正しい検出"],
        target_area="tokyo",
        query_type="single_area",
    ),
    MultiAreaTestCase(
        id="MA-DET-03",
        level=1,
        category="area_detection",
        subcategory="area_detection",
        prompt="渋谷109の近くのカフェを教えてください",
        expected_keywords=["109", "カフェ"],
        difficulty="easy",
        description="渋谷エリアのランドマーク経由検出+カフェ検索",
        evaluation_points=["ランドマーク経由のエリア検出"],
        target_area="shibuya",
        query_type="single_area",
    ),
    MultiAreaTestCase(
        id="MA-DET-04",
        level=1,
        category="area_detection",
        subcategory="area_detection",
        prompt="新宿駅西口付近のコンビニはどこですか？",
        expected_keywords=["新宿", "西口", "コンビニ"],
        difficulty="easy",
        description="新宿エリアの明示的検出+コンビニ検索",
        evaluation_points=["エリアの正しい検出"],
        target_area="shinjuku",
        query_type="single_area",
    ),
    MultiAreaTestCase(
        id="MA-DET-05",
        level=1,
        category="area_detection",
        subcategory="area_detection",
        prompt="池袋駅から最も近い薬局は？",
        expected_keywords=["池袋", "薬局", "近い"],
        difficulty="easy",
        description="池袋エリアの明示的検出+薬局検索",
        evaluation_points=["エリアの正しい検出"],
        target_area="ikebukuro",
        query_type="single_area",
    ),

    # D2 暗黙的 (5件) - L2, medium
    MultiAreaTestCase(
        id="MA-DET-06",
        level=2,
        category="area_detection",
        subcategory="area_detection",
        prompt="サンシャインシティの近くのレストランは？",
        expected_keywords=["サンシャイン", "レストラン"],
        difficulty="medium",
        description="池袋エリアのランドマーク暗黙検出+レストラン検索",
        evaluation_points=["ランドマーク経由の暗黙的エリア検出"],
        target_area="ikebukuro",
        query_type="single_area",
    ),
    MultiAreaTestCase(
        id="MA-DET-07",
        level=2,
        category="area_detection",
        subcategory="area_detection",
        prompt="歌舞伎町の近くで食事できる場所は？",
        expected_keywords=["歌舞伎町", "食事"],
        difficulty="medium",
        description="新宿エリアのランドマーク暗黙検出+飲食店検索",
        evaluation_points=["ランドマーク経由の暗黙的エリア検出"],
        target_area="shinjuku",
        query_type="single_area",
    ),
    MultiAreaTestCase(
        id="MA-DET-08",
        level=2,
        category="area_detection",
        subcategory="area_detection",
        prompt="丸の内で朝食が取れるカフェは？",
        expected_keywords=["丸の内", "朝食", "カフェ"],
        difficulty="medium",
        description="東京駅エリアの地名暗黙検出+朝食カフェ検索",
        evaluation_points=["地名による暗黙的エリア検出"],
        target_area="tokyo",
        query_type="single_area",
    ),
    MultiAreaTestCase(
        id="MA-DET-09",
        level=2,
        category="area_detection",
        subcategory="area_detection",
        prompt="ハチ公像の周りにコンビニはある？",
        expected_keywords=["ハチ公", "コンビニ"],
        difficulty="medium",
        description="渋谷エリアのランドマーク暗黙検出+コンビニ検索",
        evaluation_points=["ランドマーク経由の暗黙的エリア検出"],
        target_area="shibuya",
        query_type="single_area",
    ),
    MultiAreaTestCase(
        id="MA-DET-10",
        level=2,
        category="area_detection",
        subcategory="area_detection",
        prompt="都庁前でランチができる場所は？",
        expected_keywords=["都庁", "ランチ"],
        difficulty="medium",
        description="新宿エリアのランドマーク暗黙検出+ランチ検索",
        evaluation_points=["ランドマーク経由の暗黙的エリア検出"],
        target_area="shinjuku",
        query_type="single_area",
    ),

    # D3 不明 (5件) - L1, easy
    MultiAreaTestCase(
        id="MA-DET-11",
        level=1,
        category="area_detection",
        subcategory="area_detection",
        prompt="おすすめのカフェを教えてください",
        expected_keywords=["カフェ"],
        difficulty="easy",
        description="エリア不明のカフェ検索",
        evaluation_points=["エリア不明時の適切な応答"],
        target_area=None,
        query_type="single_area",
    ),
    MultiAreaTestCase(
        id="MA-DET-12",
        level=1,
        category="area_detection",
        subcategory="area_detection",
        prompt="24時間営業のコンビニはどこにありますか？",
        expected_keywords=["24時間", "コンビニ"],
        difficulty="easy",
        description="エリア不明の24時間コンビニ検索",
        evaluation_points=["エリア不明時の適切な応答"],
        target_area=None,
        query_type="single_area",
    ),
    MultiAreaTestCase(
        id="MA-DET-13",
        level=1,
        category="area_detection",
        subcategory="area_detection",
        prompt="美味しいラーメン屋を探しています",
        expected_keywords=["ラーメン"],
        difficulty="easy",
        description="エリア不明のラーメン検索",
        evaluation_points=["エリア不明時の適切な応答"],
        target_area=None,
        query_type="single_area",
    ),
    MultiAreaTestCase(
        id="MA-DET-14",
        level=1,
        category="area_detection",
        subcategory="area_detection",
        prompt="Wi-Fiが使える場所を教えてください",
        expected_keywords=["Wi-Fi"],
        difficulty="easy",
        description="エリア不明のWi-Fiスポット検索",
        evaluation_points=["エリア不明時の適切な応答"],
        target_area=None,
        query_type="single_area",
    ),
    MultiAreaTestCase(
        id="MA-DET-15",
        level=1,
        category="area_detection",
        subcategory="area_detection",
        prompt="近くに薬局はありますか？",
        expected_keywords=["薬局"],
        difficulty="easy",
        description="エリア不明の薬局検索",
        evaluation_points=["エリア不明時の適切な応答"],
        target_area=None,
        query_type="single_area",
    ),
]


# =============================================================================
# 全テストケースの統合
# =============================================================================

AREA_TEST_CASES = {
    "shibuya": SHIBUYA_TEST_CASES,
    "shinjuku": SHINJUKU_TEST_CASES,
    "ikebukuro": IKEBUKURO_TEST_CASES,
    "tokyo": TOKYO_TEST_CASES,
}

ALL_MULTI_AREA_TEST_CASES: List[MultiAreaTestCase] = (
    SHIBUYA_TEST_CASES
    + SHINJUKU_TEST_CASES
    + IKEBUKURO_TEST_CASES
    + TOKYO_TEST_CASES
    + CROSS_AREA_TEST_CASES
    + LANDMARK_TEST_CASES
    + DETECTION_TEST_CASES
)


# =============================================================================
# ユーティリティ関数
# =============================================================================

def get_area_tests(area_key: str) -> List[MultiAreaTestCase]:
    """指定エリアのテストケースを取得"""
    return AREA_TEST_CASES.get(area_key, [])


def get_cross_area_tests() -> List[MultiAreaTestCase]:
    """クロスエリアテストケースを取得"""
    return CROSS_AREA_TEST_CASES


def get_landmark_tests() -> List[MultiAreaTestCase]:
    """ランドマークテストケースを取得"""
    return LANDMARK_TEST_CASES


def get_detection_tests() -> List[MultiAreaTestCase]:
    """エリア検出テストケースを取得"""
    return DETECTION_TEST_CASES


def get_tests_by_level(level: int) -> List[MultiAreaTestCase]:
    """指定レベルのテストケースを取得"""
    return [tc for tc in ALL_MULTI_AREA_TEST_CASES if tc.level == level]


def get_tests_by_subcategory(subcategory: str) -> List[MultiAreaTestCase]:
    """指定サブカテゴリのテストケースを取得"""
    return [tc for tc in ALL_MULTI_AREA_TEST_CASES if tc.subcategory == subcategory]


def get_quick_test_cases() -> List[MultiAreaTestCase]:
    """Quick Test用: SBY 5件 + SJK 5件 + cross-area 3件 = 13件"""
    quick = []

    # SBY: 各レベルから1件ずつ (5件)
    for level in range(1, 6):
        sby_level = [tc for tc in SHIBUYA_TEST_CASES if tc.level == level]
        if sby_level:
            quick.append(sby_level[0])

    # SJK: 各レベルから1件ずつ (5件)
    for level in range(1, 6):
        sjk_level = [tc for tc in SHINJUKU_TEST_CASES if tc.level == level]
        if sjk_level:
            quick.append(sjk_level[0])

    # cross-area: 3件 (B1, B2, B3から各1件)
    quick.append(CROSS_AREA_TEST_CASES[0])   # MA-CROSS-01 (B1 比較)
    quick.append(CROSS_AREA_TEST_CASES[8])   # MA-CROSS-09 (B2 参照)
    quick.append(CROSS_AREA_TEST_CASES[13])  # MA-CROSS-14 (B3 集計)

    return quick


def get_test_case_stats() -> Dict:
    """テストケースの統計情報を取得"""
    levels = {}
    categories = {}
    subcategories = {}
    difficulties = {}
    areas = {}
    query_types = {}

    for tc in ALL_MULTI_AREA_TEST_CASES:
        levels[tc.level] = levels.get(tc.level, 0) + 1
        categories[tc.category] = categories.get(tc.category, 0) + 1
        subcategories[tc.subcategory] = subcategories.get(tc.subcategory, 0) + 1
        difficulties[tc.difficulty] = difficulties.get(tc.difficulty, 0) + 1

        area = tc.target_area or "cross/none"
        areas[area] = areas.get(area, 0) + 1

        query_types[tc.query_type] = query_types.get(tc.query_type, 0) + 1

    return {
        "total": len(ALL_MULTI_AREA_TEST_CASES),
        "by_level": dict(sorted(levels.items())),
        "by_category": categories,
        "by_subcategory": subcategories,
        "by_difficulty": difficulties,
        "by_area": areas,
        "by_query_type": query_types,
    }


# =============================================================================
# メインブロック: バリデーション
# =============================================================================

if __name__ == "__main__":
    all_cases = ALL_MULTI_AREA_TEST_CASES
    errors = []

    # 1. 総数チェック
    total = len(all_cases)
    if total != 130:
        errors.append(f"総数が130件ではありません: {total}件")

    # 2. エリア別件数チェック
    for area_key, area_cases in AREA_TEST_CASES.items():
        if len(area_cases) != 20:
            errors.append(f"{area_key} のテスト数が20件ではありません: {len(area_cases)}件")
        # レベル別チェック
        for level in range(1, 6):
            level_cases = [tc for tc in area_cases if tc.level == level]
            if len(level_cases) != 4:
                errors.append(
                    f"{area_key} L{level} のテスト数が4件ではありません: {len(level_cases)}件"
                )

    # クロスエリア件数
    if len(CROSS_AREA_TEST_CASES) != 20:
        errors.append(f"クロスエリアテスト数が20件ではありません: {len(CROSS_AREA_TEST_CASES)}件")

    # ランドマーク件数
    if len(LANDMARK_TEST_CASES) != 15:
        errors.append(f"ランドマークテスト数が15件ではありません: {len(LANDMARK_TEST_CASES)}件")

    # エリア検出件数
    if len(DETECTION_TEST_CASES) != 15:
        errors.append(f"エリア検出テスト数が15件ではありません: {len(DETECTION_TEST_CASES)}件")

    # 3. expected_keywords 非空チェック
    for tc in all_cases:
        if not tc.expected_keywords:
            errors.append(f"{tc.id}: expected_keywords が空です")

    # 4. ID一意性チェック
    ids = [tc.id for tc in all_cases]
    duplicates = [id_ for id_ in ids if ids.count(id_) > 1]
    if duplicates:
        errors.append(f"重複IDがあります: {set(duplicates)}")

    # 5. ランドマーク名の存在チェック
    # テストケースのプロンプトに含まれるランドマーク名がLANDMARKSに存在するか確認
    landmark_names_in_geo = set(LANDMARKS.keys())
    for tc in LANDMARK_TEST_CASES:
        found = False
        for lm_name in landmark_names_in_geo:
            if lm_name in tc.prompt:
                found = True
                break
        if not found:
            # 部分一致チェック（109 → 渋谷109 等）
            for lm_name in landmark_names_in_geo:
                for keyword in tc.expected_keywords:
                    if keyword in lm_name or lm_name in keyword:
                        found = True
                        break
                if found:
                    break
        if not found:
            errors.append(
                f"{tc.id}: プロンプトにLANDMARKSのランドマーク名が見つかりません: {tc.prompt}"
            )

    # 結果表示
    if errors:
        print("=== バリデーションエラー ===")
        for err in errors:
            print(f"  NG: {err}")
    else:
        print("=== バリデーション: 全チェックOK ===")

    # 6. 統計表示
    stats = get_test_case_stats()
    print(f"\nテストケース総数: {stats['total']}件")

    print("\nレベル別:")
    for level, count in stats["by_level"].items():
        level_name = {
            1: "基礎検索", 2: "空間推論", 3: "制約充足",
            4: "意思決定支援", 5: "高度推論"
        }[level]
        print(f"  L{level} ({level_name}): {count}件")

    print("\n難易度別:")
    for diff, count in stats["by_difficulty"].items():
        print(f"  {diff}: {count}件")

    print("\nカテゴリ別:")
    for cat, count in stats["by_category"].items():
        print(f"  {cat}: {count}件")

    print("\nサブカテゴリ別:")
    for subcat, count in stats["by_subcategory"].items():
        print(f"  {subcat}: {count}件")

    print("\nエリア別:")
    for area, count in stats["by_area"].items():
        print(f"  {area}: {count}件")

    print("\nクエリタイプ別:")
    for qt, count in stats["by_query_type"].items():
        print(f"  {qt}: {count}件")

    print(f"\nSHIBUYA_V2_MAPPING: {len(SHIBUYA_V2_MAPPING)}件")

    # Quick test
    quick = get_quick_test_cases()
    print(f"\nQuick Test: {len(quick)}件")
    for tc in quick:
        print(f"  {tc.id}: {tc.prompt[:40]}...")
