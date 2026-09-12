#!/usr/bin/env python3
"""
test_cases_v2.py - Phase 5: 拡張テストケース定義（55件）

テストレベル:
- L1: 基礎検索（Basic Retrieval）- 10件
- L2: 空間推論（Spatial Reasoning）- 15件
- L3: 制約充足（Constraint Satisfaction）- 10件
- L4: 意思決定支援（Decision Support）- 10件
- L5: 高度推論（Advanced Reasoning）- 10件

評価軸:
- keyword_hit_rate: キーワードヒット率
- coordinate_presence: 座標情報含有
- poi_name_presence: POI名含有
- reasoning_accuracy: 推論の正確性
- evidence_grounding: 根拠の明示度
- constraint_satisfaction: 制約充足度
- uncertainty_handling: 不確実性への言及
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class TestCaseV2:
    """拡張テストケース定義（Phase 5用）"""
    id: str  # "L1-01" 形式
    level: int  # 1-5
    category: str  # テストカテゴリ
    subcategory: str  # サブカテゴリ
    prompt: str  # 質問文
    expected_keywords: List[str]  # 期待されるキーワード
    difficulty: str  # easy, medium, hard, expert
    description: str  # テストの説明
    evaluation_points: List[str]  # 評価ポイント
    expected_poi_category: Optional[str] = None  # 期待されるPOIカテゴリ
    requires_coordinate: bool = False  # 座標情報が必要か
    requires_reasoning: bool = False  # 推論が必要か
    requires_evidence: bool = False  # 根拠提示が必要か
    constraints: Optional[List[str]] = None  # 制約条件
    
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
# Level 1: 基礎検索（Basic Retrieval）- 10件
# =============================================================================

L1_TEST_CASES = [
    # basic_location（5件）
    TestCaseV2(
        id="L1-01",
        level=1,
        category="basic_retrieval",
        subcategory="basic_location",
        prompt="渋谷駅の場所を教えてください",
        expected_keywords=["渋谷", "駅", "35.", "139."],
        difficulty="easy",
        description="主要駅の位置検索",
        evaluation_points=["座標情報の提供", "POI名の含有"],
        expected_poi_category="交通/鉄道駅",
        requires_coordinate=True
    ),
    TestCaseV2(
        id="L1-02",
        level=1,
        category="basic_retrieval",
        subcategory="basic_location",
        prompt="東宝シネマの座標は？",
        expected_keywords=["東宝", "シネマ", "座標", "緯度", "経度"],
        difficulty="easy",
        description="映画館の座標検索",
        evaluation_points=["座標情報の提供"],
        expected_poi_category="娯楽/映画館",
        requires_coordinate=True
    ),
    TestCaseV2(
        id="L1-03",
        level=1,
        category="basic_retrieval",
        subcategory="basic_location",
        prompt="渋谷東武ホテルはどこにありますか？",
        expected_keywords=["東武", "ホテル", "渋谷"],
        difficulty="easy",
        description="ホテルの位置検索",
        evaluation_points=["座標情報の提供", "住所情報"],
        expected_poi_category="宿泊/ホテル",
        requires_coordinate=True
    ),
    TestCaseV2(
        id="L1-04",
        level=1,
        category="basic_retrieval",
        subcategory="basic_location",
        prompt="渋谷神南郵便局の場所を教えて",
        expected_keywords=["神南", "郵便局", "渋谷"],
        difficulty="easy",
        description="郵便局の位置検索",
        evaluation_points=["座標情報の提供"],
        expected_poi_category="公共/郵便局",
        requires_coordinate=True
    ),
    TestCaseV2(
        id="L1-05",
        level=1,
        category="basic_retrieval",
        subcategory="basic_location",
        prompt="三菱UFJ銀行渋谷支店の位置情報",
        expected_keywords=["三菱", "UFJ", "銀行", "渋谷"],
        difficulty="easy",
        description="銀行の位置検索",
        evaluation_points=["座標情報の提供"],
        expected_poi_category="金融/銀行",
        requires_coordinate=True
    ),
    
    # basic_category（5件）
    TestCaseV2(
        id="L1-06",
        level=1,
        category="basic_retrieval",
        subcategory="basic_category",
        prompt="渋谷駅周辺のコンビニを教えてください",
        expected_keywords=["コンビニ", "ローソン", "ファミリーマート", "セブン"],
        difficulty="easy",
        description="コンビニのカテゴリ検索",
        evaluation_points=["複数POIの列挙"],
        expected_poi_category="商店/コンビニ"
    ),
    TestCaseV2(
        id="L1-07",
        level=1,
        category="basic_retrieval",
        subcategory="basic_category",
        prompt="渋谷にあるカフェを3つ教えて",
        expected_keywords=["カフェ", "コーヒー"],
        difficulty="easy",
        description="カフェのカテゴリ検索（件数指定）",
        evaluation_points=["指定件数の提供", "POI名の含有"],
        expected_poi_category="飲食店/カフェ"
    ),
    TestCaseV2(
        id="L1-08",
        level=1,
        category="basic_retrieval",
        subcategory="basic_category",
        prompt="渋谷の映画館を教えてください",
        expected_keywords=["映画館", "シネマ", "cinema"],
        difficulty="easy",
        description="映画館のカテゴリ検索",
        evaluation_points=["複数POIの列挙"],
        expected_poi_category="娯楽/映画館"
    ),
    TestCaseV2(
        id="L1-09",
        level=1,
        category="basic_retrieval",
        subcategory="basic_category",
        prompt="渋谷周辺の薬局はどこですか？",
        expected_keywords=["薬局", "ドラッグ"],
        difficulty="easy",
        description="薬局のカテゴリ検索",
        evaluation_points=["複数POIの列挙"],
        expected_poi_category="医療/薬局"
    ),
    TestCaseV2(
        id="L1-10",
        level=1,
        category="basic_retrieval",
        subcategory="basic_category",
        prompt="渋谷にあるホテルを教えて",
        expected_keywords=["ホテル", "宿泊"],
        difficulty="easy",
        description="ホテルのカテゴリ検索",
        evaluation_points=["複数POIの列挙"],
        expected_poi_category="宿泊/ホテル"
    ),
]


# =============================================================================
# Level 2: 空間推論（Spatial Reasoning）- 15件
# =============================================================================

L2_TEST_CASES = [
    # spatial_proximity（5件）
    TestCaseV2(
        id="L2-01",
        level=2,
        category="spatial_reasoning",
        subcategory="spatial_proximity",
        prompt="渋谷駅に最も近いコンビニはどれですか？距離も推定してください",
        expected_keywords=["コンビニ", "近い", "距離", "m", "メートル"],
        difficulty="medium",
        description="最近傍POIの選択と距離推定",
        evaluation_points=["最近傍選択", "距離推定"],
        requires_reasoning=True,
        requires_coordinate=True
    ),
    TestCaseV2(
        id="L2-02",
        level=2,
        category="spatial_reasoning",
        subcategory="spatial_proximity",
        prompt="東宝シネマから徒歩圏内（500m以内）にあるカフェを教えてください",
        expected_keywords=["カフェ", "徒歩", "500m", "圏内"],
        difficulty="medium",
        description="距離制約付き検索",
        evaluation_points=["距離制約の理解", "範囲内POIの列挙"],
        requires_reasoning=True,
        constraints=["距離500m以内"]
    ),
    TestCaseV2(
        id="L2-03",
        level=2,
        category="spatial_reasoning",
        subcategory="spatial_proximity",
        prompt="渋谷駅と原宿駅の中間地点に近いカフェはありますか？",
        expected_keywords=["カフェ", "中間", "地点"],
        difficulty="medium",
        description="中間地点の概念理解",
        evaluation_points=["中間地点の概念理解", "近傍POI選択"],
        requires_reasoning=True
    ),
    TestCaseV2(
        id="L2-04",
        level=2,
        category="spatial_reasoning",
        subcategory="spatial_proximity",
        prompt="渋谷神南郵便局の周辺200m以内にある飲食店を教えてください",
        expected_keywords=["郵便局", "200m", "飲食店", "周辺"],
        difficulty="medium",
        description="特定POI起点の近傍検索",
        evaluation_points=["近傍検索", "距離制約"],
        requires_reasoning=True,
        constraints=["距離200m以内"]
    ),
    TestCaseV2(
        id="L2-05",
        level=2,
        category="spatial_reasoning",
        subcategory="spatial_proximity",
        prompt="渋谷駅から最も遠い映画館はどれですか？",
        expected_keywords=["映画館", "遠い", "シネマ"],
        difficulty="medium",
        description="最遠点の選択",
        evaluation_points=["最遠点選択", "距離比較"],
        requires_reasoning=True
    ),
    
    # spatial_density（5件）
    TestCaseV2(
        id="L2-06",
        level=2,
        category="spatial_reasoning",
        subcategory="spatial_density",
        prompt="渋谷駅周辺で最も飲食店が集中しているのはどのあたりですか？",
        expected_keywords=["飲食店", "集中", "エリア", "多い"],
        difficulty="medium",
        description="密度分析とエリア特定",
        evaluation_points=["密度概念の理解", "エリア特定"],
        requires_reasoning=True,
        requires_evidence=True
    ),
    TestCaseV2(
        id="L2-07",
        level=2,
        category="spatial_reasoning",
        subcategory="spatial_density",
        prompt="渋谷駅周辺のカフェとバー、どちらが多いですか？",
        expected_keywords=["カフェ", "バー", "多い", "数"],
        difficulty="medium",
        description="カテゴリ別カウント比較",
        evaluation_points=["カウント比較", "数値の提示"],
        requires_reasoning=True
    ),
    TestCaseV2(
        id="L2-08",
        level=2,
        category="spatial_reasoning",
        subcategory="spatial_density",
        prompt="渋谷駅周辺は「商業エリア」と「住宅エリア」のどちらの特性が強いですか？POI構成から推定してください",
        expected_keywords=["商業", "住宅", "特性", "POI"],
        difficulty="medium",
        description="エリア特性分析",
        evaluation_points=["エリア特性分析", "根拠提示"],
        requires_reasoning=True,
        requires_evidence=True
    ),
    TestCaseV2(
        id="L2-09",
        level=2,
        category="spatial_reasoning",
        subcategory="spatial_density",
        prompt="渋谷駅周辺で医療施設（病院、クリニック、薬局）の分布を教えてください",
        expected_keywords=["病院", "クリニック", "薬局", "医療", "分布"],
        difficulty="medium",
        description="カテゴリ集約と分布把握",
        evaluation_points=["カテゴリ集約", "分布把握"],
        requires_reasoning=True
    ),
    TestCaseV2(
        id="L2-10",
        level=2,
        category="spatial_reasoning",
        subcategory="spatial_density",
        prompt="渋谷駅周辺の宿泊施設の密度は高いですか？低いですか？理由も教えてください",
        expected_keywords=["ホテル", "宿泊", "密度", "高い", "低い"],
        difficulty="medium",
        description="密度評価と根拠提示",
        evaluation_points=["密度評価", "根拠提示"],
        requires_reasoning=True,
        requires_evidence=True
    ),
    
    # spatial_comparison（5件）
    TestCaseV2(
        id="L2-11",
        level=2,
        category="spatial_reasoning",
        subcategory="spatial_comparison",
        prompt="渋谷駅の東側と西側、どちらにカフェが多いですか？",
        expected_keywords=["カフェ", "東", "西", "多い"],
        difficulty="medium",
        description="方向別比較",
        evaluation_points=["方向別比較", "定量的判断"],
        requires_reasoning=True
    ),
    TestCaseV2(
        id="L2-12",
        level=2,
        category="spatial_reasoning",
        subcategory="spatial_comparison",
        prompt="渋谷駅周辺の映画館と劇場、どちらが多いですか？それぞれの数も教えてください",
        expected_keywords=["映画館", "劇場", "数", "多い"],
        difficulty="medium",
        description="定量比較と数値提示",
        evaluation_points=["定量比較", "数値提示"],
        requires_reasoning=True
    ),
    TestCaseV2(
        id="L2-13",
        level=2,
        category="spatial_reasoning",
        subcategory="spatial_comparison",
        prompt="渋谷駅周辺のコンビニとスーパー、生活利便性の観点からどちらが充実していますか？",
        expected_keywords=["コンビニ", "スーパー", "生活", "利便性", "充実"],
        difficulty="medium",
        description="評価を伴う比較",
        evaluation_points=["評価を伴う比較", "根拠提示"],
        requires_reasoning=True,
        requires_evidence=True
    ),
    TestCaseV2(
        id="L2-14",
        level=2,
        category="spatial_reasoning",
        subcategory="spatial_comparison",
        prompt="渋谷駅周辺の銀行と郵便局、金融サービスへのアクセスはどちらが良いですか？",
        expected_keywords=["銀行", "郵便局", "金融", "アクセス"],
        difficulty="medium",
        description="機能比較",
        evaluation_points=["機能比較", "根拠提示"],
        requires_reasoning=True,
        requires_evidence=True
    ),
    TestCaseV2(
        id="L2-15",
        level=2,
        category="spatial_reasoning",
        subcategory="spatial_comparison",
        prompt="渋谷駅周辺で最も多いPOIカテゴリは何ですか？上位3つを教えてください",
        expected_keywords=["カテゴリ", "多い", "上位", "ランキング"],
        difficulty="medium",
        description="ランキング作成",
        evaluation_points=["ランキング作成", "定量データ"],
        requires_reasoning=True
    ),
]


# =============================================================================
# Level 3: 制約充足（Constraint Satisfaction）- 10件
# =============================================================================

L3_TEST_CASES = [
    # constraint_single（5件）
    TestCaseV2(
        id="L3-01",
        level=3,
        category="constraint_satisfaction",
        subcategory="constraint_single",
        prompt="渋谷駅から徒歩5分以内（約400m）にあるカフェを教えてください",
        expected_keywords=["カフェ", "徒歩", "5分", "400m"],
        difficulty="medium",
        description="距離制約付き検索",
        evaluation_points=["距離制約の充足"],
        requires_reasoning=True,
        constraints=["距離400m以内"]
    ),
    TestCaseV2(
        id="L3-02",
        level=3,
        category="constraint_satisfaction",
        subcategory="constraint_single",
        prompt="電話番号がわかっている渋谷の映画館を教えてください",
        expected_keywords=["映画館", "電話", "番号"],
        difficulty="medium",
        description="属性制約付き検索",
        evaluation_points=["属性制約の充足"],
        requires_evidence=True,
        constraints=["電話番号あり"]
    ),
    TestCaseV2(
        id="L3-03",
        level=3,
        category="constraint_satisfaction",
        subcategory="constraint_single",
        prompt="ウェブサイトを持っている渋谷のレストランを教えてください",
        expected_keywords=["レストラン", "ウェブサイト", "サイト"],
        difficulty="medium",
        description="属性制約付き検索",
        evaluation_points=["属性制約の充足"],
        requires_evidence=True,
        constraints=["ウェブサイトあり"]
    ),
    TestCaseV2(
        id="L3-04",
        level=3,
        category="constraint_satisfaction",
        subcategory="constraint_single",
        prompt="「渋谷」という名前が含まれるホテルを教えてください",
        expected_keywords=["渋谷", "ホテル", "名前"],
        difficulty="medium",
        description="名称制約付き検索",
        evaluation_points=["名称制約の充足"],
        constraints=["名称に「渋谷」を含む"]
    ),
    TestCaseV2(
        id="L3-05",
        level=3,
        category="constraint_satisfaction",
        subcategory="constraint_single",
        prompt="渋谷駅周辺で24時間営業のコンビニはありますか？",
        expected_keywords=["コンビニ", "24時間", "営業"],
        difficulty="medium",
        description="営業時間制約付き検索",
        evaluation_points=["営業時間制約の充足"],
        constraints=["24時間営業"]
    ),
    
    # constraint_multi（5件）
    TestCaseV2(
        id="L3-06",
        level=3,
        category="constraint_satisfaction",
        subcategory="constraint_multi",
        prompt="渋谷駅から500m以内で、電話番号とウェブサイトの両方がわかるカフェを教えてください",
        expected_keywords=["カフェ", "500m", "電話", "ウェブサイト"],
        difficulty="hard",
        description="複数制約付き検索（距離+属性×2）",
        evaluation_points=["複数制約の同時充足"],
        requires_reasoning=True,
        requires_evidence=True,
        constraints=["距離500m以内", "電話番号あり", "ウェブサイトあり"]
    ),
    TestCaseV2(
        id="L3-07",
        level=3,
        category="constraint_satisfaction",
        subcategory="constraint_multi",
        prompt="渋谷駅周辺で、駅から近く（300m以内）、かつ映画館の近く（200m以内）にあるカフェはありますか？",
        expected_keywords=["カフェ", "駅", "300m", "映画館", "200m"],
        difficulty="hard",
        description="複数距離制約付き検索",
        evaluation_points=["複数距離制約の同時充足"],
        requires_reasoning=True,
        constraints=["駅から300m以内", "映画館から200m以内"]
    ),
    TestCaseV2(
        id="L3-08",
        level=3,
        category="constraint_satisfaction",
        subcategory="constraint_multi",
        prompt="渋谷駅周辺で、薬局が近く（200m以内）にあるクリニックを教えてください",
        expected_keywords=["薬局", "クリニック", "200m", "近く"],
        difficulty="hard",
        description="POI間近接制約検索",
        evaluation_points=["POI間近接の判定"],
        requires_reasoning=True,
        constraints=["薬局から200m以内"]
    ),
    TestCaseV2(
        id="L3-09",
        level=3,
        category="constraint_satisfaction",
        subcategory="constraint_multi",
        prompt="渋谷駅周辺で、コンビニが3軒以上集まっているエリアはどこですか？",
        expected_keywords=["コンビニ", "3軒", "集まっている", "エリア"],
        difficulty="hard",
        description="密度制約付き検索",
        evaluation_points=["密度制約の充足", "エリア特定"],
        requires_reasoning=True,
        constraints=["コンビニ3軒以上"]
    ),
    TestCaseV2(
        id="L3-10",
        level=3,
        category="constraint_satisfaction",
        subcategory="constraint_multi",
        prompt="渋谷駅から500m以内で、カフェではなくバーを探しています。候補を教えてください",
        expected_keywords=["バー", "500m", "カフェ", "ではなく"],
        difficulty="hard",
        description="肯定+否定制約付き検索",
        evaluation_points=["肯定・否定制約の同時充足"],
        requires_reasoning=True,
        constraints=["距離500m以内", "カフェを除外", "バーを含む"]
    ),
]


# =============================================================================
# Level 4: 意思決定支援（Decision Support）- 10件
# =============================================================================

L4_TEST_CASES = [
    # decision_location（5件）
    TestCaseV2(
        id="L4-01",
        level=4,
        category="decision_support",
        subcategory="decision_location",
        prompt="渋谷駅周辺で保育園を開設する場合、最適な場所はどこですか？公園の近さと交番の有無を考慮してください",
        expected_keywords=["保育園", "公園", "交番", "最適", "場所"],
        difficulty="hard",
        description="立地適性評価（保育園）",
        evaluation_points=["立地適性評価", "複数要因の考慮", "根拠提示"],
        requires_reasoning=True,
        requires_evidence=True
    ),
    TestCaseV2(
        id="L4-02",
        level=4,
        category="decision_support",
        subcategory="decision_location",
        prompt="渋谷駅周辺で高齢者向けデイサービスを開設するなら、どのエリアが適していますか？医療施設へのアクセスを重視してください",
        expected_keywords=["高齢者", "デイサービス", "医療", "アクセス", "適している"],
        difficulty="hard",
        description="立地適性評価（高齢者施設）",
        evaluation_points=["立地適性評価", "医療アクセスの考慮"],
        requires_reasoning=True,
        requires_evidence=True
    ),
    TestCaseV2(
        id="L4-03",
        level=4,
        category="decision_support",
        subcategory="decision_location",
        prompt="渋谷駅周辺で学習塾を開設する場合、駅からのアクセスとコンビニの近さを考慮して、候補地を提案してください",
        expected_keywords=["学習塾", "駅", "アクセス", "コンビニ", "候補"],
        difficulty="hard",
        description="立地適性評価（学習塾）",
        evaluation_points=["立地適性評価", "複数要因の考慮"],
        requires_reasoning=True,
        requires_evidence=True
    ),
    TestCaseV2(
        id="L4-04",
        level=4,
        category="decision_support",
        subcategory="decision_location",
        prompt="渋谷駅周辺で待ち合わせスポットとして最適な場所はどこですか？わかりやすさと周辺の飲食店を考慮してください",
        expected_keywords=["待ち合わせ", "最適", "わかりやすい", "飲食店"],
        difficulty="hard",
        description="場所推薦（待ち合わせ）",
        evaluation_points=["場所推薦", "複数要因の考慮"],
        requires_reasoning=True,
        requires_evidence=True
    ),
    TestCaseV2(
        id="L4-05",
        level=4,
        category="decision_support",
        subcategory="decision_location",
        prompt="渋谷駅周辺で観光客向けの案内所を設置するなら、どこが効果的ですか？観光スポットと駅からのアクセスを考慮してください",
        expected_keywords=["観光", "案内所", "効果的", "スポット", "アクセス"],
        difficulty="hard",
        description="立地適性評価（観光案内所）",
        evaluation_points=["立地適性評価", "観光要因の考慮"],
        requires_reasoning=True,
        requires_evidence=True
    ),
    
    # decision_business（5件）
    TestCaseV2(
        id="L4-06",
        level=4,
        category="decision_support",
        subcategory="decision_business",
        prompt="渋谷駅周辺で新規カフェの出店を検討しています。競合（既存カフェ）の数と、集客が見込めるPOI（駅、商業施設）を考慮して、出店の向き不向きを判断してください",
        expected_keywords=["カフェ", "出店", "競合", "集客", "判断"],
        difficulty="hard",
        description="出店判断（カフェ）",
        evaluation_points=["出店判断", "競合分析", "根拠提示"],
        requires_reasoning=True,
        requires_evidence=True
    ),
    TestCaseV2(
        id="L4-07",
        level=4,
        category="decision_support",
        subcategory="decision_business",
        prompt="渋谷駅周辺で新規コンビニの出店余地はありますか？既存コンビニの分布と密度から判断してください",
        expected_keywords=["コンビニ", "出店", "余地", "分布", "密度"],
        difficulty="hard",
        description="市場分析（コンビニ）",
        evaluation_points=["市場分析", "密度評価", "根拠提示"],
        requires_reasoning=True,
        requires_evidence=True
    ),
    TestCaseV2(
        id="L4-08",
        level=4,
        category="decision_support",
        subcategory="decision_business",
        prompt="渋谷駅周辺で新規ベーカリー（パン屋）を出店する場合、既存の競合と周辺のカフェ（協業可能性）を考慮して、出店戦略を提案してください",
        expected_keywords=["パン屋", "ベーカリー", "出店", "競合", "カフェ", "戦略"],
        difficulty="hard",
        description="出店戦略（ベーカリー）",
        evaluation_points=["出店戦略", "競合・協業分析"],
        requires_reasoning=True,
        requires_evidence=True
    ),
    TestCaseV2(
        id="L4-09",
        level=4,
        category="decision_support",
        subcategory="decision_business",
        prompt="渋谷駅周辺で深夜営業のバーを出店する場合、既存バーとの競合、駅からのアクセスを考慮して、適切なエリアを提案してください",
        expected_keywords=["バー", "深夜", "出店", "競合", "アクセス", "エリア"],
        difficulty="hard",
        description="出店判断（バー）",
        evaluation_points=["出店判断", "競合分析", "エリア提案"],
        requires_reasoning=True,
        requires_evidence=True
    ),
    TestCaseV2(
        id="L4-10",
        level=4,
        category="decision_support",
        subcategory="decision_business",
        prompt="渋谷駅周辺で薬局を出店する場合、既存薬局との競合と、医療施設（病院、クリニック）との近接性を考慮して、出店の可否を判断してください",
        expected_keywords=["薬局", "出店", "競合", "病院", "クリニック", "可否"],
        difficulty="hard",
        description="出店判断（薬局）",
        evaluation_points=["出店判断", "競合・シナジー分析"],
        requires_reasoning=True,
        requires_evidence=True
    ),
]


# =============================================================================
# Level 5: 高度推論（Advanced Reasoning）- 10件
# =============================================================================

L5_TEST_CASES = [
    # advanced_sensitivity（3件）
    TestCaseV2(
        id="L5-01",
        level=5,
        category="advanced_reasoning",
        subcategory="advanced_sensitivity",
        prompt="「渋谷駅周辺はカフェが多い」という結論は、検索半径を500mから300mに変えても成立しますか？両方の範囲でのカフェ数を比較して判断してください",
        expected_keywords=["カフェ", "500m", "300m", "比較", "成立"],
        difficulty="expert",
        description="感度分析（検索半径）",
        evaluation_points=["感度分析", "条件変更の影響評価"],
        requires_reasoning=True,
        requires_evidence=True
    ),
    TestCaseV2(
        id="L5-02",
        level=5,
        category="advanced_reasoning",
        subcategory="advanced_sensitivity",
        prompt="「渋谷駅周辺は飲食店が充実している」という評価は、カフェを除外した場合でも成立しますか？",
        expected_keywords=["飲食店", "充実", "カフェ", "除外", "成立"],
        difficulty="expert",
        description="感度分析（カテゴリ除外）",
        evaluation_points=["感度分析", "条件変更の影響評価"],
        requires_reasoning=True,
        requires_evidence=True
    ),
    TestCaseV2(
        id="L5-03",
        level=5,
        category="advanced_reasoning",
        subcategory="advanced_sensitivity",
        prompt="渋谷駅周辺のコンビニ密度について、「十分に多い」と言える最小半径はどのくらいですか？",
        expected_keywords=["コンビニ", "密度", "十分", "最小", "半径"],
        difficulty="expert",
        description="閾値分析",
        evaluation_points=["閾値分析", "定量的判断"],
        requires_reasoning=True,
        requires_evidence=True
    ),
    
    # advanced_comparison（4件）
    TestCaseV2(
        id="L5-04",
        level=5,
        category="advanced_reasoning",
        subcategory="advanced_comparison",
        prompt="高齢者向け住宅の候補地として、渋谷駅周辺と恵比寿駅周辺を比較してください。評価軸は：医療施設の数、薬局の数、公共施設（郵便局、交番）の有無としてください",
        expected_keywords=["高齢者", "渋谷", "恵比寿", "比較", "医療", "薬局", "公共"],
        difficulty="expert",
        description="多地点・多軸比較",
        evaluation_points=["多地点比較", "多軸評価", "総合判断"],
        requires_reasoning=True,
        requires_evidence=True
    ),
    TestCaseV2(
        id="L5-05",
        level=5,
        category="advanced_reasoning",
        subcategory="advanced_comparison",
        prompt="子育て世帯向けの居住地として、渋谷駅周辺を評価してください。公園、保育施設、医療施設、スーパーの観点から総合的に判断してください",
        expected_keywords=["子育て", "居住", "公園", "保育", "医療", "スーパー", "総合"],
        difficulty="expert",
        description="総合評価（子育て）",
        evaluation_points=["総合評価", "多軸判断"],
        requires_reasoning=True,
        requires_evidence=True
    ),
    TestCaseV2(
        id="L5-06",
        level=5,
        category="advanced_reasoning",
        subcategory="advanced_comparison",
        prompt="ビジネスパーソン向けの立地として、渋谷駅周辺を評価してください。カフェ（作業場所）、コンビニ（利便性）、金融機関（銀行、ATM）の観点から判断してください",
        expected_keywords=["ビジネス", "カフェ", "コンビニ", "金融", "銀行", "評価"],
        difficulty="expert",
        description="総合評価（ビジネス）",
        evaluation_points=["総合評価", "多軸判断"],
        requires_reasoning=True,
        requires_evidence=True
    ),
    TestCaseV2(
        id="L5-07",
        level=5,
        category="advanced_reasoning",
        subcategory="advanced_comparison",
        prompt="観光客向けのエリアとして、渋谷駅周辺を評価してください。観光スポット、飲食店、宿泊施設の観点から、強みと弱みを分析してください",
        expected_keywords=["観光", "飲食店", "宿泊", "強み", "弱み", "分析"],
        difficulty="expert",
        description="SWOT的分析（観光）",
        evaluation_points=["SWOT分析", "強み・弱みの特定"],
        requires_reasoning=True,
        requires_evidence=True
    ),
    
    # advanced_uncertainty（3件）
    TestCaseV2(
        id="L5-08",
        level=5,
        category="advanced_reasoning",
        subcategory="advanced_uncertainty",
        prompt="渋谷駅周辺で「雰囲気の良い」カフェを探しています。データから判断できる範囲で推薦し、判断の限界も説明してください",
        expected_keywords=["雰囲気", "カフェ", "推薦", "判断", "限界"],
        difficulty="expert",
        description="曖昧入力対応",
        evaluation_points=["曖昧さの認識", "適切な留保"],
        requires_reasoning=True
    ),
    TestCaseV2(
        id="L5-09",
        level=5,
        category="advanced_reasoning",
        subcategory="advanced_uncertainty",
        prompt="渋谷駅周辺で「静かな」レストランを探しています。データから推測できることと、できないことを区別して回答してください",
        expected_keywords=["静か", "レストラン", "推測", "できる", "できない"],
        difficulty="expert",
        description="不確実性の明示",
        evaluation_points=["不確実性の認識", "推測と事実の区別"],
        requires_reasoning=True
    ),
    TestCaseV2(
        id="L5-10",
        level=5,
        category="advanced_reasoning",
        subcategory="advanced_uncertainty",
        prompt="渋谷駅周辺のPOIデータに基づいて、このエリアの「治安」について推測できることはありますか？交番の有無などから判断し、データの限界も述べてください",
        expected_keywords=["治安", "交番", "推測", "データ", "限界"],
        difficulty="expert",
        description="データ限界の認識",
        evaluation_points=["データ限界の認識", "慎重な推論"],
        requires_reasoning=True
    ),
]


# =============================================================================
# 全テストケースの統合
# =============================================================================

TEST_CASES_V2: List[TestCaseV2] = (
    L1_TEST_CASES + 
    L2_TEST_CASES + 
    L3_TEST_CASES + 
    L4_TEST_CASES + 
    L5_TEST_CASES
)


# =============================================================================
# ユーティリティ関数
# =============================================================================

def get_test_cases_by_level(level: int) -> List[TestCaseV2]:
    """指定レベルのテストケースを取得"""
    return [tc for tc in TEST_CASES_V2 if tc.level == level]


def get_test_cases_by_category(category: str) -> List[TestCaseV2]:
    """指定カテゴリのテストケースを取得"""
    return [tc for tc in TEST_CASES_V2 if tc.category == category]


def get_test_cases_by_subcategory(subcategory: str) -> List[TestCaseV2]:
    """指定サブカテゴリのテストケースを取得"""
    return [tc for tc in TEST_CASES_V2 if tc.subcategory == subcategory]


def get_test_cases_by_difficulty(difficulty: str) -> List[TestCaseV2]:
    """指定難易度のテストケースを取得"""
    return [tc for tc in TEST_CASES_V2 if tc.difficulty == difficulty]


def get_test_case_by_id(test_id: str) -> Optional[TestCaseV2]:
    """IDでテストケースを取得"""
    for tc in TEST_CASES_V2:
        if tc.id == test_id:
            return tc
    return None


def get_test_case_stats_v2() -> Dict:
    """テストケースの統計情報を取得"""
    levels = {}
    categories = {}
    subcategories = {}
    difficulties = {}
    
    for tc in TEST_CASES_V2:
        levels[tc.level] = levels.get(tc.level, 0) + 1
        categories[tc.category] = categories.get(tc.category, 0) + 1
        subcategories[tc.subcategory] = subcategories.get(tc.subcategory, 0) + 1
        difficulties[tc.difficulty] = difficulties.get(tc.difficulty, 0) + 1
    
    return {
        "total": len(TEST_CASES_V2),
        "by_level": dict(sorted(levels.items())),
        "by_category": categories,
        "by_subcategory": subcategories,
        "by_difficulty": difficulties
    }


if __name__ == "__main__":
    # テストケース統計を表示
    stats = get_test_case_stats_v2()
    print(f"テストケース総数: {stats['total']}件")
    
    print("\nレベル別:")
    for level, count in stats["by_level"].items():
        level_name = {1: "基礎検索", 2: "空間推論", 3: "制約充足", 4: "意思決定支援", 5: "高度推論"}[level]
        print(f"  L{level} ({level_name}): {count}件")
    
    print("\n難易度別:")
    for diff, count in stats["by_difficulty"].items():
        print(f"  {diff}: {count}件")
    
    print("\nサブカテゴリ別:")
    for subcat, count in stats["by_subcategory"].items():
        print(f"  {subcat}: {count}件")
