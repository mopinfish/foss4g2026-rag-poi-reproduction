"""
graph_rag_system.py - グラフRAGシステム

Phase 8: ナレッジグラフを活用したRAGシステム

作成日: 2026-01-29
プロジェクト: experiments-local-llm
"""

import json
import re
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    nx = None

# ローカルモジュール（パッケージ/スクリプト両対応）
try:
    from .graph_builder import (
        POIGraphBuilder,
        get_pois_by_category,
        get_pois_by_area,
        get_nearby_pois,
        get_pois_in_same_area,
        find_pois_with_both_categories,
        SHIBUYA_STATION,
        DIRECTION_JP
    )
    from .geo_utils import detect_target_area
except ImportError:
    from graph_builder import (
        POIGraphBuilder,
        get_pois_by_category,
        get_pois_by_area,
        get_nearby_pois,
        get_pois_in_same_area,
        find_pois_with_both_categories,
        SHIBUYA_STATION,
        DIRECTION_JP
    )
    from geo_utils import detect_target_area


# =============================================================================
# 定数定義
# =============================================================================

# カテゴリキーワードマッピング
CATEGORY_KEYWORDS = {
    "レストラン": "飲食店",
    "カフェ": "飲食店",
    "コーヒー": "飲食店",
    "喫茶店": "飲食店",
    "バー": "飲食店",
    "居酒屋": "飲食店",
    "ファストフード": "飲食店",
    "食事": "飲食店",
    "ご飯": "飲食店",
    "コンビニ": "商店",
    "スーパー": "商店",
    "本屋": "商店",
    "書店": "商店",
    "映画館": "娯楽",
    "劇場": "娯楽",
    "ホテル": "宿泊",
    "駅": "交通",
    "銀行": "金融",
    "ATM": "金融",
    "郵便局": "公共",
    "病院": "医療",
    "クリニック": "医療",
    "薬局": "医療",
    "公園": "レジャー",
}

# サブカテゴリキーワードマッピング
SUBCATEGORY_KEYWORDS = {
    "カフェ": "カフェ",
    "レストラン": "レストラン",
    "バー": "バー",
    "パブ": "パブ",
    "ファストフード": "ファストフード",
    "コンビニ": "コンビニ",
    "スーパー": "スーパー",
    "書店": "書店",
    "映画館": "映画館",
    "ホテル": "ホテル",
    "銀行": "銀行",
    "郵便局": "郵便局",
    "病院": "病院",
    "薬局": "薬局",
}

# 方向キーワード
DIRECTION_KEYWORDS = {
    "東": ["east", "northeast", "southeast"],
    "西": ["west", "northwest", "southwest"],
    "北": ["north", "northeast", "northwest"],
    "南": ["south", "southeast", "southwest"],
    "東側": ["east", "northeast", "southeast"],
    "西側": ["west", "northwest", "southwest"],
}

# 質問タイプキーワード
COMPARISON_KEYWORDS = ["比較", "どちら", "違い", "どっち", "vs", "対", "多い方"]
AGGREGATION_KEYWORDS = ["いくつ", "何件", "多い", "少ない", "数", "件数", "上位", "ランキング"]
PROXIMITY_KEYWORDS = ["最も近い", "一番近い", "最寄り", "近い順", "最短", "近く"]
RELATION_KEYWORDS = ["同じエリア", "近くにある", "周辺", "付近", "そば", "隣"]
MULTI_HOP_KEYWORDS = ["から", "を起点", "経由", "通って"]


# =============================================================================
# データクラス
# =============================================================================

@dataclass
class GraphQueryAnalysis:
    """グラフクエリ分析結果"""
    question_type: str = "simple"  # simple, comparison, aggregation, proximity, relation, multi_hop
    categories: List[str] = field(default_factory=list)
    subcategories: List[str] = field(default_factory=list)
    directions: List[str] = field(default_factory=list)
    areas: List[str] = field(default_factory=list)

    requires_graph_traversal: bool = False
    requires_category_filter: bool = False
    requires_area_filter: bool = False
    requires_proximity: bool = False
    requires_relation: bool = False
    requires_multi_hop: bool = False
    requires_aggregation: bool = False
    requires_comparison: bool = False

    distance_constraint: Optional[float] = None
    hop_count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_type": self.question_type,
            "categories": self.categories,
            "subcategories": self.subcategories,
            "directions": self.directions,
            "areas": self.areas,
            "requires_graph_traversal": self.requires_graph_traversal,
            "requires_category_filter": self.requires_category_filter,
            "requires_area_filter": self.requires_area_filter,
            "requires_proximity": self.requires_proximity,
            "requires_relation": self.requires_relation,
            "requires_multi_hop": self.requires_multi_hop,
            "requires_aggregation": self.requires_aggregation,
            "requires_comparison": self.requires_comparison,
            "distance_constraint": self.distance_constraint,
            "hop_count": self.hop_count
        }


@dataclass
class GraphQueryResult:
    """グラフクエリ結果"""
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    context: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "context": self.context,
            "metadata": self.metadata
        }


# =============================================================================
# 質問分析関数
# =============================================================================

def analyze_graph_query(question: str) -> GraphQueryAnalysis:
    """
    質問を分析してグラフクエリ戦略を決定

    Args:
        question: 質問文

    Returns:
        GraphQueryAnalysis オブジェクト
    """
    analysis = GraphQueryAnalysis()
    question_lower = question.lower()

    # カテゴリ抽出
    for keyword, category in CATEGORY_KEYWORDS.items():
        if keyword in question:
            if category not in analysis.categories:
                analysis.categories.append(category)
            analysis.requires_category_filter = True

    # サブカテゴリ抽出
    for keyword, subcategory in SUBCATEGORY_KEYWORDS.items():
        if keyword in question:
            if subcategory not in analysis.subcategories:
                analysis.subcategories.append(subcategory)

    # 方向抽出
    for keyword, directions in DIRECTION_KEYWORDS.items():
        if keyword in question:
            for d in directions:
                if d not in analysis.directions:
                    analysis.directions.append(d)
            analysis.requires_area_filter = True

    # 質問タイプ判定
    # 比較
    if any(kw in question for kw in COMPARISON_KEYWORDS):
        analysis.question_type = "comparison"
        analysis.requires_comparison = True
        analysis.requires_graph_traversal = True

    # 集計
    if any(kw in question for kw in AGGREGATION_KEYWORDS):
        analysis.question_type = "aggregation"
        analysis.requires_aggregation = True
        analysis.requires_graph_traversal = True

    # 近接性
    if any(kw in question for kw in PROXIMITY_KEYWORDS):
        analysis.question_type = "proximity"
        analysis.requires_proximity = True
        analysis.requires_graph_traversal = True

    # 関係性（同じエリア、周辺など）
    if any(kw in question for kw in RELATION_KEYWORDS):
        analysis.question_type = "relation"
        analysis.requires_relation = True
        analysis.requires_graph_traversal = True

    # マルチホップ
    if any(kw in question for kw in MULTI_HOP_KEYWORDS):
        analysis.question_type = "multi_hop"
        analysis.requires_multi_hop = True
        analysis.requires_graph_traversal = True
        analysis.hop_count = 2

    # 距離制約の抽出
    distance_match = re.search(r'(\d+)\s*(?:m|メートル)', question)
    if distance_match:
        analysis.distance_constraint = float(distance_match.group(1))

    # エリア特定
    if analysis.directions:
        zones = ["station", "near", "mid", "far"]
        for direction in analysis.directions:
            for zone in zones:
                area = f"{direction}_{zone}"
                if area not in analysis.areas:
                    analysis.areas.append(area)

    return analysis


# =============================================================================
# グラフRAGシステムクラス
# =============================================================================

class GraphRAGSystem:
    """ナレッジグラフを活用したRAGシステム"""

    def __init__(self, graph_or_pois=None, poi_json_path: str = None,
                 areas_config: Optional[Dict[str, Any]] = None,
                 all_pois: Optional[List[Dict[str, Any]]] = None):
        """
        Args:
            graph_or_pois: 構築済みのNetworkXグラフ、またはPOIリスト（List[Dict]）
            poi_json_path: POI JSONファイルのパス（グラフ未構築時）
            areas_config: エリア設定辞書。指定時はエリア別グラフを構築。
            all_pois: 全POIリスト（areas_config使用時に必要）
        """
        if not HAS_NETWORKX:
            raise ImportError("networkx is required")

        self.areas_config = areas_config or {
            "shibuya": {"name": "渋谷駅周辺", "station": SHIBUYA_STATION}
        }
        self.graphs: Dict[str, nx.DiGraph] = {}
        self.indices_by_area: Dict[str, Dict] = {}

        # エリア別グラフ構築
        if areas_config and len(areas_config) > 1 and all_pois is not None:
            for area_key, area_info in areas_config.items():
                area_pois = [
                    p for p in all_pois
                    if (p.get("area_key") or p.get("metadata", {}).get("area_key")) == area_key
                ]
                station = area_info.get("station", SHIBUYA_STATION)
                builder = POIGraphBuilder(station=station)
                self.graphs[area_key] = builder.build_graph(area_pois, verbose=False)
            # デフォルトグラフは最初のエリア
            first_key = next(iter(self.graphs))
            self.graph = self.graphs[first_key]
        elif graph_or_pois is not None:
            if isinstance(graph_or_pois, nx.DiGraph):
                self.graph = graph_or_pois
            elif isinstance(graph_or_pois, list):
                self.graph = self._build_graph_from_pois(graph_or_pois)
            else:
                raise ValueError(f"Expected nx.DiGraph or list, got {type(graph_or_pois)}")
            self.graphs["shibuya"] = self.graph
        elif poi_json_path is not None:
            self.graph = self._build_graph(poi_json_path)
            self.graphs["shibuya"] = self.graph
        else:
            raise ValueError("Either graph_or_pois, poi_json_path, or (areas_config + all_pois) must be provided")

        # ノードインデックスの構築
        self._build_indices()

        # エリア別インデックスも構築
        if len(self.graphs) > 1:
            for area_key, graph in self.graphs.items():
                self.indices_by_area[area_key] = self._build_indices_for_graph(graph)

    def _build_graph(self, poi_json_path: str) -> nx.DiGraph:
        """POI JSONファイルパスからグラフを構築"""
        builder = POIGraphBuilder()
        pois = builder.load_pois_from_json(poi_json_path)
        return builder.build_graph(pois, verbose=False)

    def _build_graph_from_pois(self, pois: list) -> nx.DiGraph:
        """POIリストから直接グラフを構築"""
        builder = POIGraphBuilder()
        return builder.build_graph(pois, verbose=False)

    def _build_indices_for_graph(self, graph: nx.DiGraph) -> Dict:
        """特定グラフ用のインデックスを構築"""
        indices = {
            "poi_nodes": {},
            "category_nodes": {},
            "area_nodes": {},
            "subcategory_to_pois": defaultdict(list),
            "category_to_pois": defaultdict(list),
            "area_to_pois": defaultdict(list),
        }

        for node, data in graph.nodes(data=True):
            node_type = data.get("node_type", "")

            if node_type == "poi":
                indices["poi_nodes"][node] = data
                subcategory = data.get("subcategory", "")
                if subcategory:
                    indices["subcategory_to_pois"][subcategory].append(node)
                category = data.get("category", "")
                if category:
                    indices["category_to_pois"][category].append(node)
                area = data.get("area_cluster", "")
                if area:
                    indices["area_to_pois"][area].append(node)
            elif node_type == "category":
                indices["category_nodes"][node] = data
            elif node_type == "area":
                indices["area_nodes"][node] = data

        return indices

    def _build_indices(self):
        """高速検索用のインデックスを構築（デフォルトグラフ用）"""
        self.poi_nodes = {}
        self.category_nodes = {}
        self.area_nodes = {}
        self.subcategory_to_pois = defaultdict(list)
        self.category_to_pois = defaultdict(list)
        self.area_to_pois = defaultdict(list)

        for node, data in self.graph.nodes(data=True):
            node_type = data.get("node_type", "")

            if node_type == "poi":
                self.poi_nodes[node] = data

                subcategory = data.get("subcategory", "")
                if subcategory:
                    self.subcategory_to_pois[subcategory].append(node)

                category = data.get("category", "")
                if category:
                    self.category_to_pois[category].append(node)

                area = data.get("area_cluster", "")
                if area:
                    self.area_to_pois[area].append(node)

            elif node_type == "category":
                self.category_nodes[node] = data

            elif node_type == "area":
                self.area_nodes[node] = data

    def _select_graph_and_indices(self, question: str) -> Tuple:
        """質問文からエリアを特定し、適切なグラフとインデックスを選択"""
        if len(self.graphs) <= 1:
            return (self.graph, self.poi_nodes, self.category_nodes,
                    self.area_nodes, self.subcategory_to_pois,
                    self.category_to_pois, self.area_to_pois)

        target_area = detect_target_area(question, self.areas_config)

        if target_area and target_area in self.indices_by_area:
            idx = self.indices_by_area[target_area]
            return (self.graphs[target_area],
                    idx["poi_nodes"], idx["category_nodes"],
                    idx["area_nodes"], idx["subcategory_to_pois"],
                    idx["category_to_pois"], idx["area_to_pois"])

        # エリア不明の場合はデフォルトグラフ（全インデックスを統合）
        return (self.graph, self.poi_nodes, self.category_nodes,
                self.area_nodes, self.subcategory_to_pois,
                self.category_to_pois, self.area_to_pois)

    def query(self, question: str, top_k: int = 10) -> GraphQueryResult:
        """
        質問に対してグラフクエリを実行

        Args:
            question: 質問文
            top_k: 返すPOIの最大数

        Returns:
            GraphQueryResult
        """
        # Phase 9-B: エリア別グラフ選択
        if len(self.graphs) > 1:
            (selected_graph, poi_nodes, category_nodes, area_nodes,
             subcategory_to_pois, category_to_pois, area_to_pois) = \
                self._select_graph_and_indices(question)

            # 一時的にインスタンス変数を差し替え
            orig = (self.graph, self.poi_nodes, self.category_nodes,
                    self.area_nodes, self.subcategory_to_pois,
                    self.category_to_pois, self.area_to_pois)
            (self.graph, self.poi_nodes, self.category_nodes,
             self.area_nodes, self.subcategory_to_pois,
             self.category_to_pois, self.area_to_pois) = \
                (selected_graph, poi_nodes, category_nodes, area_nodes,
                 subcategory_to_pois, category_to_pois, area_to_pois)

        # 質問分析
        analysis = analyze_graph_query(question)

        # クエリ実行
        result = GraphQueryResult()
        result.metadata["analysis"] = analysis.to_dict()

        # 質問タイプに応じた処理
        if analysis.requires_relation:
            result = self._execute_relation_query(analysis, top_k)
        elif analysis.requires_multi_hop:
            result = self._execute_multi_hop_query(analysis, top_k)
        elif analysis.requires_proximity:
            result = self._execute_proximity_query(analysis, top_k)
        elif analysis.requires_comparison:
            result = self._execute_comparison_query(analysis, top_k)
        elif analysis.requires_aggregation:
            result = self._execute_aggregation_query(analysis, top_k)
        else:
            result = self._execute_simple_query(analysis, top_k)

        # コンテキスト生成
        result.context = self._generate_context(result, analysis)
        result.metadata["analysis"] = analysis.to_dict()

        # インスタンス変数を復元
        if len(self.graphs) > 1:
            (self.graph, self.poi_nodes, self.category_nodes,
             self.area_nodes, self.subcategory_to_pois,
             self.category_to_pois, self.area_to_pois) = orig

        return result

    def _execute_simple_query(self, analysis: GraphQueryAnalysis,
                              top_k: int) -> GraphQueryResult:
        """単純なフィルタクエリを実行"""
        result = GraphQueryResult()
        candidate_pois = set()

        # カテゴリフィルタ
        if analysis.subcategories:
            for subcat in analysis.subcategories:
                for poi in self.subcategory_to_pois.get(subcat, []):
                    candidate_pois.add(poi)
        elif analysis.categories:
            for cat in analysis.categories:
                for poi in self.category_to_pois.get(cat, []):
                    candidate_pois.add(poi)
        else:
            candidate_pois = set(self.poi_nodes.keys())

        # 方向/エリアフィルタ
        if analysis.directions:
            filtered_pois = set()
            for poi in candidate_pois:
                poi_data = self.poi_nodes.get(poi, {})
                poi_direction = poi_data.get("direction", "")
                if poi_direction in analysis.directions:
                    filtered_pois.add(poi)
            candidate_pois = filtered_pois

        # 距離制約フィルタ
        if analysis.distance_constraint:
            filtered_pois = set()
            for poi in candidate_pois:
                poi_data = self.poi_nodes.get(poi, {})
                distance = poi_data.get("distance_from_station", float("inf"))
                if distance <= analysis.distance_constraint:
                    filtered_pois.add(poi)
            candidate_pois = filtered_pois

        # 結果を距離順でソート
        sorted_pois = sorted(
            candidate_pois,
            key=lambda p: self.poi_nodes.get(p, {}).get("distance_from_station", float("inf"))
        )[:top_k]

        for poi in sorted_pois:
            result.nodes.append(self.poi_nodes[poi])

        return result

    def _execute_proximity_query(self, analysis: GraphQueryAnalysis,
                                 top_k: int) -> GraphQueryResult:
        """近接性クエリを実行（最寄り検索）"""
        result = GraphQueryResult()

        # カテゴリ指定がある場合はそのカテゴリで最寄りを検索
        if analysis.subcategories:
            for subcat in analysis.subcategories:
                pois = self.subcategory_to_pois.get(subcat, [])
                # 距離順でソート
                sorted_pois = sorted(
                    pois,
                    key=lambda p: self.poi_nodes.get(p, {}).get("distance_from_station", float("inf"))
                )[:top_k]

                for poi in sorted_pois:
                    result.nodes.append(self.poi_nodes[poi])

        elif analysis.categories:
            for cat in analysis.categories:
                pois = self.category_to_pois.get(cat, [])
                sorted_pois = sorted(
                    pois,
                    key=lambda p: self.poi_nodes.get(p, {}).get("distance_from_station", float("inf"))
                )[:top_k]

                for poi in sorted_pois:
                    result.nodes.append(self.poi_nodes[poi])

        result.metadata["query_type"] = "proximity"
        return result

    def _execute_relation_query(self, analysis: GraphQueryAnalysis,
                                top_k: int) -> GraphQueryResult:
        """関係性クエリを実行（同じエリア、周辺など）"""
        result = GraphQueryResult()

        # 2つのカテゴリが同じエリアにある場所を探す
        if len(analysis.categories) >= 2 or len(analysis.subcategories) >= 2:
            cat1 = analysis.categories[0] if analysis.categories else None
            cat2 = analysis.categories[1] if len(analysis.categories) > 1 else None

            if cat1 and cat2:
                relations = find_pois_with_both_categories(self.graph, cat1, cat2)

                for rel in relations[:top_k]:
                    result.nodes.append({
                        "poi1": rel["poi1"],
                        "poi1_name": rel["poi1_name"],
                        "poi2": rel["poi2"],
                        "poi2_name": rel["poi2_name"],
                        "area": rel["area"],
                        "relation": "SAME_AREA"
                    })
                    result.edges.append({
                        "source": rel["poi1"],
                        "target": rel["poi2"],
                        "type": "SAME_AREA"
                    })

        # 単一カテゴリで同一エリア内のPOIを探す
        elif analysis.categories or analysis.subcategories:
            target_pois = set()

            if analysis.subcategories:
                for subcat in analysis.subcategories:
                    target_pois.update(self.subcategory_to_pois.get(subcat, []))
            else:
                for cat in analysis.categories:
                    target_pois.update(self.category_to_pois.get(cat, []))

            # エリアごとにグループ化
            area_groups = defaultdict(list)
            for poi in target_pois:
                area = self.poi_nodes.get(poi, {}).get("area_cluster", "")
                if area:
                    area_groups[area].append(poi)

            # POI数の多いエリアから順に
            sorted_areas = sorted(area_groups.items(), key=lambda x: -len(x[1]))

            count = 0
            for area, pois in sorted_areas:
                if count >= top_k:
                    break
                for poi in pois:
                    if count >= top_k:
                        break
                    result.nodes.append(self.poi_nodes[poi])
                    count += 1

        result.metadata["query_type"] = "relation"
        return result

    def _execute_multi_hop_query(self, analysis: GraphQueryAnalysis,
                                 top_k: int) -> GraphQueryResult:
        """マルチホップクエリを実行"""
        result = GraphQueryResult()

        # 例: 「カフェを起点に、そこから50m以内にある書店」
        # Step 1: 最初のカテゴリのPOIを取得
        if len(analysis.subcategories) >= 2:
            start_subcat = analysis.subcategories[0]
            end_subcat = analysis.subcategories[1]

            start_pois = self.subcategory_to_pois.get(start_subcat, [])

            # Step 2: 各起点POIから近隣の終点カテゴリPOIを探索
            for start_poi in start_pois[:top_k]:
                nearby = get_nearby_pois(
                    self.graph,
                    start_poi,
                    max_distance=analysis.distance_constraint or 100
                )

                for end_poi, distance in nearby:
                    end_data = self.poi_nodes.get(end_poi, {})
                    if end_data.get("subcategory") == end_subcat:
                        result.nodes.append({
                            "start_poi": start_poi,
                            "start_name": self.poi_nodes.get(start_poi, {}).get("name", ""),
                            "end_poi": end_poi,
                            "end_name": end_data.get("name", ""),
                            "distance": distance
                        })
                        result.edges.append({
                            "source": start_poi,
                            "target": end_poi,
                            "type": "NEAR_TO",
                            "distance": distance
                        })

        result.metadata["query_type"] = "multi_hop"
        return result

    def _execute_comparison_query(self, analysis: GraphQueryAnalysis,
                                  top_k: int) -> GraphQueryResult:
        """比較クエリを実行"""
        result = GraphQueryResult()

        # 東西比較
        if "east" in analysis.directions or "west" in analysis.directions:
            east_pois = []
            west_pois = []

            target_pois = set()
            if analysis.subcategories:
                for subcat in analysis.subcategories:
                    target_pois.update(self.subcategory_to_pois.get(subcat, []))
            elif analysis.categories:
                for cat in analysis.categories:
                    target_pois.update(self.category_to_pois.get(cat, []))
            else:
                target_pois = set(self.poi_nodes.keys())

            for poi in target_pois:
                poi_data = self.poi_nodes.get(poi, {})
                direction = poi_data.get("direction", "")
                if direction in ["east", "northeast", "southeast"]:
                    east_pois.append(poi)
                elif direction in ["west", "northwest", "southwest"]:
                    west_pois.append(poi)

            result.nodes.append({
                "comparison_type": "east_west",
                "east_count": len(east_pois),
                "west_count": len(west_pois),
                "category": analysis.categories[0] if analysis.categories else "all"
            })

            result.metadata["east_pois"] = len(east_pois)
            result.metadata["west_pois"] = len(west_pois)

        # カテゴリ間比較
        elif len(analysis.categories) >= 2:
            cat1, cat2 = analysis.categories[0], analysis.categories[1]
            count1 = len(self.category_to_pois.get(cat1, []))
            count2 = len(self.category_to_pois.get(cat2, []))

            result.nodes.append({
                "comparison_type": "category",
                "category1": cat1,
                "count1": count1,
                "category2": cat2,
                "count2": count2
            })

        result.metadata["query_type"] = "comparison"
        return result

    def _execute_aggregation_query(self, analysis: GraphQueryAnalysis,
                                   top_k: int) -> GraphQueryResult:
        """集計クエリを実行"""
        result = GraphQueryResult()

        if analysis.categories or analysis.subcategories:
            # 特定カテゴリの集計
            for cat in analysis.categories:
                pois = self.category_to_pois.get(cat, [])

                # 方向別集計
                direction_counts = defaultdict(int)
                for poi in pois:
                    direction = self.poi_nodes.get(poi, {}).get("direction", "unknown")
                    direction_counts[direction] += 1

                result.nodes.append({
                    "category": cat,
                    "total_count": len(pois),
                    "by_direction": dict(direction_counts)
                })
        else:
            # 全カテゴリの集計
            category_counts = {}
            for cat, pois in self.category_to_pois.items():
                category_counts[cat] = len(pois)

            # 上位カテゴリ
            sorted_cats = sorted(category_counts.items(), key=lambda x: -x[1])[:top_k]

            for cat, count in sorted_cats:
                result.nodes.append({
                    "category": cat,
                    "count": count
                })

        result.metadata["query_type"] = "aggregation"
        return result

    def _generate_context(self, result: GraphQueryResult,
                          analysis: GraphQueryAnalysis) -> str:
        """クエリ結果からLLM用コンテキストを生成"""
        context_parts = []

        if analysis.question_type == "proximity":
            context_parts.append("【最寄りPOI情報】")
            for i, node in enumerate(result.nodes[:5], 1):
                name = node.get("name", "不明")
                distance = node.get("distance_from_station", 0)
                direction = DIRECTION_JP.get(node.get("direction", ""), "不明")
                subcategory = node.get("subcategory", "")
                context_parts.append(
                    f"{i}. {name} ({subcategory}) - 駅から{direction}へ{distance:.0f}m"
                )

        elif analysis.question_type == "relation":
            context_parts.append("【同一エリア内のPOI関係】")
            for node in result.nodes[:5]:
                if "poi1_name" in node:
                    context_parts.append(
                        f"- {node['poi1_name']} と {node['poi2_name']} は同じエリア（{node.get('area', '')}）にあります"
                    )
                else:
                    name = node.get("name", "不明")
                    area = node.get("area_cluster", "")
                    context_parts.append(f"- {name} ({area})")

        elif analysis.question_type == "multi_hop":
            context_parts.append("【経路上のPOI】")
            for node in result.nodes[:5]:
                if "start_name" in node:
                    context_parts.append(
                        f"- {node['start_name']} から {node['distance']:.0f}m の位置に {node['end_name']} があります"
                    )

        elif analysis.question_type == "comparison":
            context_parts.append("【比較結果】")
            for node in result.nodes:
                if node.get("comparison_type") == "east_west":
                    cat = node.get("category", "全カテゴリ")
                    context_parts.append(f"- {cat}: 東側 {node['east_count']}件、西側 {node['west_count']}件")
                elif node.get("comparison_type") == "category":
                    context_parts.append(
                        f"- {node['category1']}: {node['count1']}件 vs {node['category2']}: {node['count2']}件"
                    )

        elif analysis.question_type == "aggregation":
            context_parts.append("【集計結果】")
            for node in result.nodes[:10]:
                if "by_direction" in node:
                    cat = node.get("category", "")
                    total = node.get("total_count", 0)
                    context_parts.append(f"- {cat}: 合計{total}件")
                    for direction, count in node.get("by_direction", {}).items():
                        jp_dir = DIRECTION_JP.get(direction, direction)
                        context_parts.append(f"  - {jp_dir}: {count}件")
                else:
                    cat = node.get("category", "")
                    count = node.get("count", 0)
                    context_parts.append(f"- {cat}: {count}件")

        else:
            # 単純クエリ
            context_parts.append("【検索結果】")
            for i, node in enumerate(result.nodes[:5], 1):
                name = node.get("name", "不明")
                subcategory = node.get("subcategory", "")
                distance = node.get("distance_from_station", 0)
                direction = DIRECTION_JP.get(node.get("direction", ""), "")
                context_parts.append(
                    f"{i}. {name} ({subcategory}) - {direction} {distance:.0f}m"
                )

        return "\n".join(context_parts)

    def get_subgraph(self, center_node: str, hops: int = 1) -> nx.DiGraph:
        """
        指定ノードを中心としたサブグラフを取得

        Args:
            center_node: 中心ノードID
            hops: ホップ数

        Returns:
            サブグラフ
        """
        if not self.graph.has_node(center_node):
            return nx.DiGraph()

        nodes = {center_node}
        frontier = {center_node}

        for _ in range(hops):
            next_frontier = set()
            for node in frontier:
                for _, target in self.graph.out_edges(node):
                    next_frontier.add(target)
                for source, _ in self.graph.in_edges(node):
                    next_frontier.add(source)
            nodes.update(next_frontier)
            frontier = next_frontier

        return self.graph.subgraph(nodes).copy()

    def get_graph_stats(self) -> Dict[str, Any]:
        """グラフ統計情報を取得"""
        stats = {
            "num_poi_nodes": len(self.poi_nodes),
            "num_category_nodes": len(self.category_nodes),
            "num_area_nodes": len(self.area_nodes),
            "num_edges": self.graph.number_of_edges(),
            "categories": list(self.category_to_pois.keys()),
            "subcategories": list(self.subcategory_to_pois.keys()),
            "num_area_graphs": len(self.graphs),
        }
        if len(self.graphs) > 1:
            stats["area_graph_stats"] = {}
            for area_key, graph in self.graphs.items():
                stats["area_graph_stats"][area_key] = {
                    "nodes": graph.number_of_nodes(),
                    "edges": graph.number_of_edges(),
                }
        return stats


# =============================================================================
# ハイブリッドRAGシステム（グラフ + ベクトル検索）
# =============================================================================

class HybridGraphRAGSystem:
    """グラフ検索とベクトル検索を統合したハイブリッドRAGシステム"""

    def __init__(self, graph_rag: GraphRAGSystem,
                 vector_retriever=None):
        """
        Args:
            graph_rag: GraphRAGSystemインスタンス
            vector_retriever: ベクトル検索用のretriever（オプション）
        """
        self.graph_rag = graph_rag
        self.vector_retriever = vector_retriever

    def query(self, question: str, top_k: int = 10,
              graph_weight: float = 0.5) -> Dict[str, Any]:
        """
        ハイブリッドクエリを実行

        Args:
            question: 質問文
            top_k: 返す結果の最大数
            graph_weight: グラフ結果の重み（0-1）

        Returns:
            統合された結果
        """
        # グラフクエリ実行
        graph_result = self.graph_rag.query(question, top_k=top_k)

        # ベクトル検索実行（retrieverがある場合）
        vector_results = []
        if self.vector_retriever is not None:
            try:
                vector_docs = self.vector_retriever.get_relevant_documents(question)
                vector_results = [doc.page_content for doc in vector_docs[:top_k]]
            except Exception as e:
                print(f"Vector search failed: {e}")

        # コンテキスト統合
        combined_context = self._merge_contexts(
            graph_result.context,
            vector_results,
            graph_weight
        )

        return {
            "context": combined_context,
            "graph_result": graph_result.to_dict(),
            "vector_results": vector_results,
            "metadata": {
                "graph_weight": graph_weight,
                "analysis": graph_result.metadata.get("analysis", {})
            }
        }

    def _merge_contexts(self, graph_context: str,
                        vector_results: List[str],
                        graph_weight: float) -> str:
        """グラフコンテキストとベクトル検索結果をマージ"""
        parts = []

        if graph_weight > 0 and graph_context:
            parts.append("=== グラフ検索結果 ===")
            parts.append(graph_context)

        if graph_weight < 1 and vector_results:
            parts.append("\n=== ベクトル検索結果 ===")
            for i, result in enumerate(vector_results[:5], 1):
                parts.append(f"{i}. {result[:200]}...")

        return "\n".join(parts)


# =============================================================================
# ユーティリティ関数
# =============================================================================

def create_graph_rag_system(poi_json_path: str) -> GraphRAGSystem:
    """
    POI JSONからGraphRAGSystemを作成するヘルパー関数

    Args:
        poi_json_path: POI JSONファイルのパス

    Returns:
        GraphRAGSystem インスタンス
    """
    builder = POIGraphBuilder()
    pois = builder.load_pois_from_json(poi_json_path)
    graph = builder.build_graph(pois, verbose=True)
    return GraphRAGSystem(graph=graph)


# =============================================================================
# メイン実行
# =============================================================================

if __name__ == "__main__":
    import sys

    poi_file = "poi_documents.json"
    if len(sys.argv) > 1:
        poi_file = sys.argv[1]

    print(f"Creating GraphRAG system from: {poi_file}")
    system = create_graph_rag_system(poi_file)

    # テストクエリ
    test_questions = [
        "渋谷駅に最も近いカフェはどこですか？",
        "東側と西側でレストランが多いのはどちらですか？",
        "カフェと銀行が同じエリアにある場所を教えてください",
        "渋谷駅の東側にあるコンビニの数は？",
    ]

    print("\n" + "=" * 60)
    print("Test Queries")
    print("=" * 60)

    for q in test_questions:
        print(f"\nQ: {q}")
        result = system.query(q)
        print(f"Context:\n{result.context}")
        print("-" * 40)
