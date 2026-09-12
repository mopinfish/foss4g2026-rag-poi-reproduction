"""
structured_rag_system.py - 構造化RAGシステム

Phase 6: 座標計算、集計、比較機能を統合した高度なRAGシステム

作成日: 2026-01-22
プロジェクト: experiments-local-llm
"""

from typing import List, Dict, Any, Optional, Tuple
import re
import time
import torch

# ローカルモジュール（パッケージ/スクリプト両対応）
try:
    from .geo_utils import (
        enrich_all_pois,
        enrich_all_areas,
        filter_by_distance,
        filter_east_side,
        filter_west_side,
        distance_from_station,
        direction_from_station,
        SHIBUYA_STATION,
        detect_target_area,
        # Phase 6.2追加
        get_nearest_pois,
        get_farthest_pois,
        filter_by_radius,
        count_by_radius,
        compare_by_radius,
        analyze_radius_sensitivity,
        get_poi_distance_stats,
        generate_proximity_context,
        generate_sensitivity_context
    )
    from .aggregator import (
        count_by_category,
        count_by_direction,
        count_by_subcategory,
        get_top_categories,
        compare_categories,
        compare_east_west,
        analyze_category_by_direction,
        filter_by_category,
        generate_aggregation_context,
        generate_comparison_context
    )
except ImportError:
    from geo_utils import (
        enrich_all_pois,
        enrich_all_areas,
        filter_by_distance,
        filter_east_side,
        filter_west_side,
        distance_from_station,
        direction_from_station,
        SHIBUYA_STATION,
        detect_target_area,
        get_nearest_pois,
        get_farthest_pois,
        filter_by_radius,
        count_by_radius,
        compare_by_radius,
        analyze_radius_sensitivity,
        get_poi_distance_stats,
        generate_proximity_context,
        generate_sensitivity_context
    )
    from aggregator import (
        count_by_category,
        count_by_direction,
        count_by_subcategory,
        get_top_categories,
        compare_categories,
        compare_east_west,
        analyze_category_by_direction,
        filter_by_category,
        generate_aggregation_context,
        generate_comparison_context
    )


# =============================================================================
# 定数定義
# =============================================================================

# カテゴリキーワードマッピング
CATEGORY_KEYWORDS = {
    "レストラン": ["飲食店/レストラン"],
    "カフェ": ["飲食店/カフェ"],
    "コーヒー": ["飲食店/カフェ"],
    "スタバ": ["飲食店/カフェ"],
    "喫茶店": ["飲食店/カフェ"],
    "バー": ["飲食店/バー"],
    "居酒屋": ["飲食店/バー", "飲食店/パブ"],
    "ファストフード": ["飲食店/ファストフード"],
    "マクドナルド": ["飲食店/ファストフード"],
    "ハンバーガー": ["飲食店/ファストフード"],
    "コンビニ": ["商店/コンビニ"],
    "ローソン": ["商店/コンビニ"],
    "セブン": ["商店/コンビニ"],
    "ファミマ": ["商店/コンビニ"],
    "映画館": ["娯楽/映画館"],
    "シネマ": ["娯楽/映画館"],
    "劇場": ["娯楽/劇場"],
    "ホテル": ["宿泊/ホテル"],
    "旅館": ["宿泊/旅館"],
    "駅": ["交通/鉄道駅"],
    "銀行": ["金融/銀行"],
    "ATM": ["金融/銀行", "金融/ATM"],
    "郵便局": ["公共/郵便局"],
    "病院": ["医療/病院"],
    "クリニック": ["医療/クリニック"],
    "薬局": ["医療/薬局"],
    "ドラッグストア": ["医療/薬局"],
    "交番": ["公共/警察"],
    "警察": ["公共/警察"],
    "公園": ["レジャー/公園"],
    "スーパー": ["商店/スーパー"],
}

# 質問タイプ判定キーワード
COMPARISON_KEYWORDS = ["比較", "どちら", "違い", "どっち", "vs", "対"]
AGGREGATION_KEYWORDS = ["いくつ", "何件", "多い", "少ない", "数", "件数", "上位", "ランキング", "最も"]
DIRECTION_KEYWORDS = ["東", "西", "北", "南"]
DISTANCE_KEYWORDS = ["近く", "近い", "徒歩", "以内", "m", "メートル", "km", "キロ"]

# Phase 6.2追加: 近接性・感度分析キーワード
PROXIMITY_KEYWORDS = ["最も近い", "一番近い", "最寄り", "近い順", "最短"]
SENSITIVITY_KEYWORDS = ["変えても", "変更しても", "広げても", "狭めても", "範囲を", "半径を", "成立"]


# =============================================================================
# 質問分析クラス
# =============================================================================

class QuestionAnalysis:
    """質問分析結果を保持するクラス"""
    
    def __init__(self):
        self.question_type: str = "simple"  # simple, comparison, aggregation, spatial, proximity, sensitivity
        self.categories: List[str] = []
        self.subcategories: List[str] = []
        self.directions: List[str] = []
        self.constraints: List[Dict[str, Any]] = []
        self.requires_aggregation: bool = False
        self.requires_comparison: bool = False
        self.requires_spatial: bool = False
        self.requires_proximity: bool = False  # Phase 6.2追加: 最近傍検索
        self.requires_sensitivity: bool = False  # Phase 6.2追加: 感度分析
        self.distance_constraint: Optional[float] = None
        self.sensitivity_radii: Optional[Tuple[float, float]] = None  # Phase 6.2追加
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_type": self.question_type,
            "categories": self.categories,
            "subcategories": self.subcategories,
            "directions": self.directions,
            "constraints": self.constraints,
            "requires_aggregation": self.requires_aggregation,
            "requires_comparison": self.requires_comparison,
            "requires_spatial": self.requires_spatial,
            "requires_proximity": self.requires_proximity,
            "requires_sensitivity": self.requires_sensitivity,
            "distance_constraint": self.distance_constraint,
            "sensitivity_radii": self.sensitivity_radii
        }


def analyze_question(question: str) -> QuestionAnalysis:
    """
    質問を分析して検索戦略を決定
    
    Args:
        question: 質問文
    
    Returns:
        QuestionAnalysis オブジェクト
    """
    analysis = QuestionAnalysis()
    
    # カテゴリ抽出
    for keyword, categories in CATEGORY_KEYWORDS.items():
        if keyword in question:
            for cat in categories:
                if cat not in analysis.categories:
                    analysis.categories.append(cat)
                # サブカテゴリも抽出
                if "/" in cat:
                    subcat = cat.split("/")[-1]
                    if subcat not in analysis.subcategories:
                        analysis.subcategories.append(subcat)
    
    # 方向キーワード抽出
    if "東" in question:
        analysis.directions.append("east")
    if "西" in question:
        analysis.directions.append("west")
    if "北" in question:
        analysis.directions.append("north")
    if "南" in question:
        analysis.directions.append("south")
    
    # 比較キーワード検出
    if any(word in question for word in COMPARISON_KEYWORDS):
        analysis.requires_comparison = True
    
    # 集計キーワード検出
    if any(word in question for word in AGGREGATION_KEYWORDS):
        analysis.requires_aggregation = True
    
    # 空間キーワード検出
    if analysis.directions or any(word in question for word in DISTANCE_KEYWORDS):
        analysis.requires_spatial = True
    
    # 距離制約の抽出
    distance_patterns = [
        (r'(\d+)\s*(m|メートル)', 1),      # 500m, 500メートル
        (r'(\d+)\s*(km|キロ)', 1000),       # 1km, 1キロ
        (r'徒歩\s*(\d+)\s*分', 80),          # 徒歩5分 → 約80m/分
    ]
    
    for pattern, multiplier in distance_patterns:
        match = re.search(pattern, question)
        if match:
            value = int(match.group(1)) * multiplier
            analysis.distance_constraint = value
            analysis.constraints.append({
                "type": "distance",
                "value": value,
                "original": match.group(0)
            })
            break
    
    # 質問タイプの決定
    if analysis.requires_comparison:
        analysis.question_type = "comparison"
    elif analysis.requires_aggregation:
        analysis.question_type = "aggregation"
    elif analysis.requires_spatial:
        analysis.question_type = "spatial"
    else:
        analysis.question_type = "simple"
    
    # Phase 6.2追加: 近接性キーワード検出
    if any(word in question for word in PROXIMITY_KEYWORDS):
        analysis.requires_proximity = True
        analysis.question_type = "proximity"
    
    # Phase 6.2追加: 感度分析キーワード検出
    if any(word in question for word in SENSITIVITY_KEYWORDS):
        analysis.requires_sensitivity = True
        analysis.question_type = "sensitivity"
        
        # 感度分析用の半径ペアを抽出
        # 例: 「500mから300mに変えても」
        radius_pattern = r'(\d+)\s*(m|メートル).*?(\d+)\s*(m|メートル)'
        match = re.search(radius_pattern, question)
        if match:
            r1 = int(match.group(1))
            r2 = int(match.group(3))
            analysis.sensitivity_radii = (min(r1, r2), max(r1, r2))
        else:
            # デフォルト: 300m と 500m
            analysis.sensitivity_radii = (300, 500)
    
    return analysis


# =============================================================================
# 構造化RAGシステムクラス
# =============================================================================

class StructuredRAGSystem:
    """
    構造化RAGシステム
    
    座標計算、集計、比較機能を持つ高度なRAGシステム
    ベクトル検索に加えて、メタデータベースの検索・集計を実行
    """
    
    def __init__(
        self,
        model,
        tokenizer,
        vectorstore,
        all_pois: List[Dict[str, Any]],
        areas_config: Optional[Dict[str, Any]] = None,
        debug: bool = False
    ):
        """
        RAGシステムを初期化

        Args:
            model: Hugging Face Transformersモデル
            tokenizer: トークナイザー
            vectorstore: LangChain ChromaDBベクトルストア
            all_pois: 全POIデータ（集計用）
            areas_config: エリア設定辞書。None時は渋谷単一エリア（後方互換）
            debug: デバッグ出力を有効にする
        """
        self.model = model
        self.tokenizer = tokenizer
        self.vectorstore = vectorstore
        self.debug = debug
        self.areas_config = areas_config or {
            "shibuya": {"name": "渋谷駅周辺", "station": SHIBUYA_STATION}
        }

        # エリア別にPOIを空間情報付与
        if areas_config and len(areas_config) > 1:
            self.all_pois = enrich_all_areas(all_pois, areas_config)
        else:
            self.all_pois = enrich_all_pois(all_pois)

        # エリア別POIインデックス
        self.pois_by_area: Dict[str, List[Dict[str, Any]]] = {}
        for poi in self.all_pois:
            area_key = (poi.get("area_key")
                        or poi.get("metadata", {}).get("area_key", "shibuya"))
            self.pois_by_area.setdefault(area_key, []).append(poi)

        if self.debug:
            print(f"✅ StructuredRAGSystem初期化完了")
            print(f"   POI数: {len(self.all_pois)}件")
            print(f"   エリア数: {len(self.pois_by_area)}")
            for area_key, area_pois in self.pois_by_area.items():
                print(f"     {area_key}: {len(area_pois)}件")
            print(f"   空間情報付与: 完了")

        # システムプロンプト（広域対応）
        if areas_config and len(areas_config) > 1:
            area_names = "、".join(
                info.get("name", key) for key, info in self.areas_config.items()
            )
            self.system_prompt = f"""あなたは東京都内の主要駅周辺エリア（{area_names}）の地理情報に詳しいアシスタントです。
提供されたデータに基づいて、以下の構造で回答してください。

# 回答の構造
1. **結論**: 質問への直接的な回答を最初に述べる
2. **根拠**: データから得られた具体的な証拠を引用する
3. **補足**: 注意点や不確実な点があれば述べる

# 回答ルール
- 推論過程を明示する: 「したがって」「比較すると」「分析すると」「なぜなら」等の論理接続詞を使い、結論に至る過程を示す
- 根拠を具体的に引用する: POI名、座標(緯度, 経度)、距離(m)、件数を提供データから引用し、「データから」「検索結果に基づき」等で出典を明記する
- 数値は単位付きで示す: 距離はm、件数は件、座標は(35.xxx, 139.xxx)の形式で記載する
- 比較表現を使う: 「より多い」「最も近い」「〜倍」等の比較表現で差異を明確にする
- 不確実性を正直に示す: データで確認できない点は「ただし」「データの限界として」「可能性があります」「データからは確認できません」等で明記する
- 情報がない場合は「提供データからは確認できません」と正直に回答する"""
        else:
            self.system_prompt = """あなたは渋谷エリアの地理情報に詳しいアシスタントです。
提供されたデータに基づいて、以下の構造で回答してください。

# 回答の構造
1. **結論**: 質問への直接的な回答を最初に述べる
2. **根拠**: データから得られた具体的な証拠を引用する
3. **補足**: 注意点や不確実な点があれば述べる

# 回答ルール
- 推論過程を明示する: 「したがって」「比較すると」「分析すると」「なぜなら」等の論理接続詞を使い、結論に至る過程を示す
- 根拠を具体的に引用する: POI名、座標(緯度, 経度)、距離(m)、件数を提供データから引用し、「データから」「検索結果に基づき」等で出典を明記する
- 数値は単位付きで示す: 距離はm、件数は件、座標は(35.xxx, 139.xxx)の形式で記載する
- 比較表現を使う: 「より多い」「最も近い」「〜倍」等の比較表現で差異を明確にする
- 不確実性を正直に示す: データで確認できない点は「ただし」「データの限界として」「可能性があります」「データからは確認できません」等で明記する
- 情報がない場合は「提供データからは確認できません」と正直に回答する"""
    
    def _generate_response(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.1
    ) -> str:
        """
        LLMでレスポンスを生成
        
        Args:
            prompt: 入力プロンプト
            max_new_tokens: 最大生成トークン数
            temperature: サンプリング温度
            
        Returns:
            生成されたテキスト
        """
        # チャット形式でプロンプト構築
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # chat_template適用
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # トークナイズ
        inputs = self.tokenizer(text, return_tensors="pt").to("cuda")
        
        # 生成
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # デコード
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # アシスタント応答部分を抽出
        if "assistant" in response.lower():
            parts = response.split("assistant")
            if len(parts) > 1:
                response = parts[-1].strip()
        
        return response
    
    def _execute_vector_search(
        self,
        question: str,
        analysis: QuestionAnalysis,
        k: int = 5,
        station: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        ベクトル検索を実行

        Args:
            question: 質問文
            analysis: 質問分析結果
            k: 取得件数
            station: 基準駅情報（None時はSHIBUYA_STATION）

        Returns:
            検索結果リスト
        """
        station = station or SHIBUYA_STATION

        # カテゴリフィルタリングが可能な場合は多めに取得してフィルタ
        if analysis.categories:
            results = self.vectorstore.similarity_search(question, k=k * 2)
            filtered = [
                r for r in results
                if r.metadata.get("category") in analysis.categories
            ][:k]

            if filtered:
                results = filtered
            else:
                results = results[:k]
        else:
            results = self.vectorstore.similarity_search(question, k=k)

        # 結果を辞書形式に変換し、空間情報を追加
        search_results = []
        for r in results:
            poi = {
                "name": r.metadata.get("name", "不明"),
                "category": r.metadata.get("category", "不明"),
                "lat": r.metadata.get("lat"),
                "lon": r.metadata.get("lon"),
                "content": r.page_content,
                "metadata": r.metadata
            }

            # 空間情報を追加（エリア別stationを使用）
            if poi.get("lat") and poi.get("lon"):
                poi["distance_from_station"] = distance_from_station(
                    poi["lat"], poi["lon"], station=station
                )
                poi["direction_from_station"] = direction_from_station(
                    poi["lat"], poi["lon"], station=station
                )

            search_results.append(poi)

        return search_results
    
    def _execute_aggregation(
        self,
        question: str,
        analysis: QuestionAnalysis
    ) -> Dict[str, Any]:
        """
        集計処理を実行
        
        Args:
            question: 質問文
            analysis: 質問分析結果
        
        Returns:
            集計結果
        """
        result = {
            "type": None,
            "data": None,
            "context": ""
        }
        
        # ランキングが必要な場合
        if any(word in question for word in ["上位", "ランキング", "最も多い"]):
            top_cats = get_top_categories(self.all_pois, top_n=10)
            result["type"] = "ranking"
            result["data"] = [c.to_dict() for c in top_cats]
            result["context"] = generate_aggregation_context(self.all_pois, "ranking")
        
        # 特定カテゴリの方向別分析
        elif analysis.categories and analysis.directions:
            cat = analysis.subcategories[0] if analysis.subcategories else analysis.categories[0].split("/")[-1]
            analysis_result = analyze_category_by_direction(self.all_pois, cat)
            result["type"] = "category_direction"
            result["data"] = analysis_result
            result["context"] = generate_aggregation_context(self.all_pois, "category", cat)
        
        # カテゴリ別の集計
        elif analysis.categories:
            cat = analysis.subcategories[0] if analysis.subcategories else analysis.categories[0].split("/")[-1]
            filtered = filter_by_category(self.all_pois, cat)
            result["type"] = "category_count"
            result["data"] = {
                "category": cat,
                "count": len(filtered),
                "examples": [p.get("name") for p in filtered[:5]]
            }
            result["context"] = f"【{cat}の集計】\n総数: {len(filtered)}件"
        
        # 全体の集計
        else:
            result["type"] = "full"
            result["data"] = count_by_category(self.all_pois)
            result["context"] = generate_aggregation_context(self.all_pois, "full")
        
        return result
    
    def _execute_comparison(
        self,
        question: str,
        analysis: QuestionAnalysis
    ) -> Dict[str, Any]:
        """
        比較処理を実行
        
        Args:
            question: 質問文
            analysis: 質問分析結果
        
        Returns:
            比較結果
        """
        result = {
            "type": None,
            "data": None,
            "context": ""
        }
        
        # 東西比較
        if "東" in question and "西" in question:
            category = None
            if analysis.subcategories:
                category = analysis.subcategories[0]
            elif analysis.categories:
                category = analysis.categories[0].split("/")[-1]
            
            comparison = compare_east_west(self.all_pois, category)
            result["type"] = "east_west"
            result["data"] = comparison.to_dict()
            result["context"] = generate_comparison_context(
                self.all_pois, "east_west", {"category": category}
            )
        
        # カテゴリ間比較
        elif len(analysis.subcategories) >= 2:
            cat1, cat2 = analysis.subcategories[:2]
            comparison = compare_categories(self.all_pois, cat1, cat2)
            result["type"] = "categories"
            result["data"] = comparison.to_dict()
            result["context"] = generate_comparison_context(
                self.all_pois, "categories", {"category1": cat1, "category2": cat2}
            )
        
        return result
    
    def _execute_spatial_filter(
        self,
        question: str,
        analysis: QuestionAnalysis
    ) -> Dict[str, Any]:
        """
        空間フィルタリングを実行
        
        Args:
            question: 質問文
            analysis: 質問分析結果
        
        Returns:
            フィルタリング結果
        """
        result = {
            "type": None,
            "data": None,
            "context": "",
            "filtered_pois": []
        }
        
        filtered = self.all_pois
        
        # 距離フィルタ
        if analysis.distance_constraint:
            filtered = filter_by_distance(filtered, analysis.distance_constraint)
            result["type"] = "distance"
        
        # 方向フィルタ
        if "east" in analysis.directions:
            filtered = filter_east_side(filtered)
            result["type"] = "direction"
        elif "west" in analysis.directions:
            filtered = filter_west_side(filtered)
            result["type"] = "direction"
        
        # カテゴリフィルタ
        if analysis.subcategories:
            filtered = filter_by_category(filtered, analysis.subcategories[0])
        elif analysis.categories:
            cat = analysis.categories[0].split("/")[-1]
            filtered = filter_by_category(filtered, cat)
        
        result["filtered_pois"] = filtered
        result["data"] = {
            "count": len(filtered),
            "examples": [p.get("name") for p in filtered[:10]]
        }
        result["context"] = f"条件に合うPOI: {len(filtered)}件"
        
        return result
    
    def _execute_proximity_search(
        self,
        question: str,
        analysis: QuestionAnalysis
    ) -> Dict[str, Any]:
        """
        Phase 6.2追加: 近接性検索を実行
        
        Args:
            question: 質問文
            analysis: 質問分析結果
        
        Returns:
            近接性検索結果
        """
        result = {
            "type": "proximity",
            "data": None,
            "context": "",
            "nearest_pois": []
        }
        
        # カテゴリを特定
        category = None
        if analysis.subcategories:
            category = analysis.subcategories[0]
        elif analysis.categories:
            category = analysis.categories[0].split("/")[-1]
        
        # 最近傍POIを取得
        top_n = 5
        nearest = get_nearest_pois(self.all_pois, category=category, top_n=top_n)
        
        result["nearest_pois"] = nearest
        result["data"] = {
            "category": category,
            "count": len(nearest),
            "nearest": [
                {
                    "name": p.get("name"),
                    "distance": p.get("distance_from_station"),
                    "direction": p.get("direction_from_station_jp")
                }
                for p in nearest
            ]
        }
        
        # コンテキスト生成
        result["context"] = generate_proximity_context(self.all_pois, category, top_n)
        
        return result
    
    def _execute_sensitivity_analysis(
        self,
        question: str,
        analysis: QuestionAnalysis
    ) -> Dict[str, Any]:
        """
        Phase 6.2追加: 感度分析を実行
        
        Args:
            question: 質問文
            analysis: 質問分析結果
        
        Returns:
            感度分析結果
        """
        result = {
            "type": "sensitivity",
            "data": None,
            "context": ""
        }
        
        # カテゴリを特定
        category = None
        if analysis.subcategories:
            category = analysis.subcategories[0]
        elif analysis.categories:
            category = analysis.categories[0].split("/")[-1]
        
        # 半径ペアを取得
        if analysis.sensitivity_radii:
            radius1, radius2 = analysis.sensitivity_radii
        else:
            radius1, radius2 = 300, 500
        
        # 半径比較
        comparison = compare_by_radius(self.all_pois, radius1, radius2, category)
        
        # 詳細な感度分析
        sensitivity = analyze_radius_sensitivity(
            self.all_pois, 
            category, 
            radii=[100, 200, 300, 500, 800, 1000]
        )
        
        result["data"] = {
            "comparison": comparison.to_dict(),
            "sensitivity": sensitivity,
            "conclusion": self._generate_sensitivity_conclusion(comparison, category)
        }
        
        # コンテキスト生成
        result["context"] = generate_sensitivity_context(
            self.all_pois, category, radius1, radius2
        )
        
        return result
    
    def _generate_sensitivity_conclusion(
        self,
        comparison,
        category: Optional[str]
    ) -> str:
        """感度分析の結論を生成"""
        cat_str = f"「{category}」" if category else "POI"
        
        if comparison.count1 == 0:
            return f"小さい半径では{cat_str}が存在しないため、結論は成立しません。"
        
        if comparison.ratio >= 1.5:
            return f"{cat_str}は駅周辺より郊外に多く分布しており、半径を変えると結論が大きく変わる可能性があります。"
        elif comparison.ratio >= 1.2:
            return f"半径を変えると件数は変化しますが、{cat_str}が多いという結論は概ね維持されます。"
        else:
            return f"{cat_str}は駅周辺に集中しており、半径を変えても結論は大きく変わりません。"
    
    def _build_context(
        self,
        search_results: List[Dict[str, Any]],
        aggregation: Optional[Dict[str, Any]],
        comparison: Optional[Dict[str, Any]],
        spatial: Optional[Dict[str, Any]],
        proximity: Optional[Dict[str, Any]] = None,
        sensitivity: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        LLM用のコンテキストを構築
        
        Args:
            search_results: ベクトル検索結果
            aggregation: 集計結果
            comparison: 比較結果
            spatial: 空間フィルタリング結果
            proximity: 近接性検索結果（Phase 6.2）
            sensitivity: 感度分析結果（Phase 6.2）
        
        Returns:
            コンテキストテキスト
        """
        context_parts = []
        
        # Phase 6.2: 近接性検索結果（最優先）
        if proximity and proximity.get("context"):
            context_parts.append(proximity["context"])
        
        # Phase 6.2: 感度分析結果
        if sensitivity and sensitivity.get("context"):
            context_parts.append(sensitivity["context"])
            if sensitivity.get("data", {}).get("conclusion"):
                context_parts.append(f"\n【結論】\n{sensitivity['data']['conclusion']}")
        
        # ベクトル検索結果
        if search_results and not proximity:  # 近接性検索がない場合のみ
            context_parts.append("【検索結果】")
            for r in search_results[:5]:
                context_parts.append(r["content"])
        
        # 集計結果
        if aggregation and aggregation.get("context"):
            context_parts.append("\n" + aggregation["context"])
        
        # 比較結果
        if comparison and comparison.get("context"):
            context_parts.append("\n" + comparison["context"])
        
        # 空間フィルタリング結果
        if spatial and spatial.get("filtered_pois"):
            context_parts.append(f"\n【空間フィルタ結果】")
            context_parts.append(f"条件に合うPOI: {len(spatial['filtered_pois'])}件")
            for p in spatial["filtered_pois"][:5]:
                distance = p.get("distance_from_station", 0)
                direction = p.get("direction_from_station", "不明")
                context_parts.append(f"  - {p.get('name')}: {distance:.0f}m ({direction})")
        
        return "\n".join(context_parts)
    
    def _get_target_pois_and_station(
        self,
        question: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any], Optional[str]]:
        """
        質問文からエリアを特定し、対象POIと基準駅を返す

        Args:
            question: 質問文

        Returns:
            (target_pois, target_station, target_area_key)
        """
        target_area = detect_target_area(question, self.areas_config)

        if target_area and target_area in self.pois_by_area:
            target_pois = self.pois_by_area[target_area]
            target_station = self.areas_config[target_area].get("station", SHIBUYA_STATION)
        else:
            target_pois = self.all_pois
            target_station = SHIBUYA_STATION

        if self.debug:
            print(f"エリア特定: {target_area or '全エリア'} → POI数: {len(target_pois)}")

        return target_pois, target_station, target_area

    def query_with_structured_rag(
        self,
        question: str,
        k: int = 5
    ) -> Dict[str, Any]:
        """
        構造化RAGを使用して質問に回答

        Args:
            question: 質問文
            k: ベクトル検索の取得件数

        Returns:
            回答と付随情報の辞書
        """
        start_time = time.time()

        # Phase 9-B: エリア特定
        target_pois, target_station, target_area = self._get_target_pois_and_station(question)

        # 質問分析
        analysis = analyze_question(question)

        if self.debug:
            print(f"質問分析結果: {analysis.to_dict()}")

        # ベクトル検索（エリア別stationを使用）
        search_results = self._execute_vector_search(question, analysis, k, station=target_station)

        # 以下の処理はtarget_poisを使用するために一時的にself.all_poisを差し替え
        original_pois = self.all_pois
        self.all_pois = target_pois

        # 集計処理
        aggregation = None
        if analysis.requires_aggregation:
            aggregation = self._execute_aggregation(question, analysis)

        # 比較処理
        comparison = None
        if analysis.requires_comparison:
            comparison = self._execute_comparison(question, analysis)

        # 空間フィルタリング
        spatial = None
        if analysis.requires_spatial and (analysis.distance_constraint or analysis.directions):
            spatial = self._execute_spatial_filter(question, analysis)

        # Phase 6.2: 近接性検索
        proximity = None
        if analysis.requires_proximity:
            proximity = self._execute_proximity_search(question, analysis)

        # Phase 6.2: 感度分析
        sensitivity = None
        if analysis.requires_sensitivity:
            sensitivity = self._execute_sensitivity_analysis(question, analysis)

        # self.all_poisを復元
        self.all_pois = original_pois

        # コンテキスト構築
        context = self._build_context(
            search_results, aggregation, comparison, spatial,
            proximity, sensitivity
        )

        # プロンプト構築
        prompt = f"""以下の提供データを参考にして、質問に回答してください。

{context}

【質問】
{question}

以下の構造で回答してください:
【結論】質問への直接的な回答
【根拠】データから引用した具体的なPOI名、距離(m)、件数等の証拠
【補足】データの限界や注意点（該当する場合）"""

        # 回答生成
        answer = self._generate_response(prompt)

        elapsed_time = time.time() - start_time

        return {
            "answer": answer,
            "analysis": analysis.to_dict(),
            "search_results": search_results,
            "aggregation": aggregation,
            "comparison": comparison,
            "spatial": spatial,
            "context": context,
            "target_area": target_area,
            "time_ms": int(elapsed_time * 1000)
        }

    def query(self, question: str) -> Dict[str, Any]:
        """
        質問に回答（評価用エイリアスメソッド）

        query_with_structured_rag()のエイリアス。
        評価スクリプトとの互換性のために提供。

        Args:
            question: 質問文

        Returns:
            回答と付随情報の辞書
        """
        return self.query_with_structured_rag(question)

    def query_without_rag(self, question: str) -> Dict[str, Any]:
        """
        RAGを使用せずに質問に回答（比較用）
        
        Args:
            question: 質問文
            
        Returns:
            回答と付随情報の辞書
        """
        start_time = time.time()
        
        prompt = f"""以下の質問に回答してください。

【質問】
{question}

【回答】"""
        
        answer = self._generate_response(prompt)
        
        elapsed_time = time.time() - start_time
        
        return {
            "answer": answer,
            "sources": [],
            "time_ms": int(elapsed_time * 1000)
        }
    
    def get_context(self, question: str, k: int = 5) -> str:
        """
        質問に対するコンテキストのみを取得（LLM生成なし）

        統合比較評価用に外部LLMで回答生成する場合に使用。

        Args:
            question: 質問文
            k: ベクトル検索の取得件数

        Returns:
            コンテキストテキスト
        """
        # Phase 9-B: エリア特定
        target_pois, target_station, target_area = self._get_target_pois_and_station(question)

        # 質問分析
        analysis = analyze_question(question)

        # ベクトル検索
        search_results = self._execute_vector_search(question, analysis, k, station=target_station)

        # target_poisを使用するために一時的にself.all_poisを差し替え
        original_pois = self.all_pois
        self.all_pois = target_pois

        # 集計処理
        aggregation = None
        if analysis.requires_aggregation:
            aggregation = self._execute_aggregation(question, analysis)

        # 比較処理
        comparison = None
        if analysis.requires_comparison:
            comparison = self._execute_comparison(question, analysis)

        # 空間フィルタリング
        spatial = None
        if analysis.requires_spatial and (analysis.distance_constraint or analysis.directions):
            spatial = self._execute_spatial_filter(question, analysis)

        # 近接性検索
        proximity = None
        if analysis.requires_proximity:
            proximity = self._execute_proximity_search(question, analysis)

        # 感度分析
        sensitivity = None
        if analysis.requires_sensitivity:
            sensitivity = self._execute_sensitivity_analysis(question, analysis)

        # self.all_poisを復元
        self.all_pois = original_pois

        # コンテキスト構築
        context = self._build_context(
            search_results, aggregation, comparison, spatial,
            proximity, sensitivity
        )

        return context

    def compare(self, question: str, verbose: bool = True) -> Dict[str, Any]:
        """
        構造化RAGあり/なしの回答を比較
        
        Args:
            question: 質問文
            verbose: 詳細出力
        
        Returns:
            比較結果の辞書
        """
        # RAGあり
        rag_result = self.query_with_structured_rag(question)
        
        # RAGなし
        no_rag_result = self.query_without_rag(question)
        
        if verbose:
            print("=" * 60)
            print(f"質問: {question}")
            print("=" * 60)
            print(f"\n【構造化RAGあり】({rag_result['time_ms']}ms)")
            print(f"分析タイプ: {rag_result['analysis']['question_type']}")
            print(f"回答:\n{rag_result['answer'][:500]}...")
            print(f"\n【RAGなし】({no_rag_result['time_ms']}ms)")
            print(f"回答:\n{no_rag_result['answer'][:500]}...")
        
        return {
            "question": question,
            "rag_result": rag_result,
            "no_rag_result": no_rag_result
        }


# =============================================================================
# ファクトリ関数
# =============================================================================

def create_structured_rag_system(
    model,
    tokenizer,
    vectorstore,
    poi_documents: List[Dict[str, Any]],
    areas_config: Optional[Dict[str, Any]] = None,
    debug: bool = False
) -> StructuredRAGSystem:
    """
    StructuredRAGSystemのファクトリ関数

    Args:
        model: Hugging Face Transformersモデル
        tokenizer: トークナイザー
        vectorstore: LangChain ChromaDBベクトルストア
        poi_documents: POIドキュメントのリスト
        areas_config: エリア設定辞書（None時は渋谷単一エリア）
        debug: デバッグモード

    Returns:
        StructuredRAGSystemインスタンス
    """
    # POIデータの抽出（metadataがある場合）
    all_pois = []
    for doc in poi_documents:
        if isinstance(doc, dict):
            poi = doc.copy()
        else:
            # LangChain Documentの場合
            poi = doc.metadata.copy() if hasattr(doc, 'metadata') else {}
            if hasattr(doc, 'page_content'):
                poi['content'] = doc.page_content
        all_pois.append(poi)

    return StructuredRAGSystem(
        model=model,
        tokenizer=tokenizer,
        vectorstore=vectorstore,
        all_pois=all_pois,
        areas_config=areas_config,
        debug=debug
    )
