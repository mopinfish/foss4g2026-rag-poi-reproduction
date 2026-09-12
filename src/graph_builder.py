"""
graph_builder.py - POIナレッジグラフ構築モジュール

Phase 8: グラフRAG実験のためのグラフ構築機能
Phase 9-B: 基準駅の動的化（geo_utils.STATIONSを使用）

作成日: 2026-01-29
更新日: 2026-02-18
プロジェクト: experiments-local-llm
"""

import json
import math
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    nx = None

try:
    from .geo_utils import STATIONS, SHIBUYA_STATION
except ImportError:
    from geo_utils import STATIONS, SHIBUYA_STATION


# =============================================================================
# 定数定義
# =============================================================================

# 地球の半径（メートル）
EARTH_RADIUS_M = 6371000

# 距離ゾーンの閾値（メートル）
DISTANCE_ZONES = {
    "station": 50,      # 駅直近
    "near": 200,        # 近距離
    "mid": 500,         # 中距離
    "far": float("inf") # 遠距離
}

# NEAR_TOエッジの距離閾値（メートル）
NEAR_DISTANCE_THRESHOLD = 100

# 方向の定義（8方位）
DIRECTIONS = ["north", "northeast", "east", "southeast",
              "south", "southwest", "west", "northwest"]

# 方向の日本語マッピング
DIRECTION_JP = {
    "north": "北",
    "northeast": "北東",
    "east": "東",
    "southeast": "南東",
    "south": "南",
    "southwest": "南西",
    "west": "西",
    "northwest": "北西",
    "center": "中心"
}

# 補完関係の定義（カテゴリペア → 関係タイプ）
COMPLEMENTARY_RULES = {
    # 宿泊 × 飲食
    ("宿泊/ホテル", "飲食店/レストラン"): "DINING_NEAR_HOTEL",
    ("宿泊/ホテル", "飲食店/カフェ"): "DINING_NEAR_HOTEL",
    ("宿泊/ホテル", "飲食店/バー"): "DINING_NEAR_HOTEL",
    # エンタメ × 飲食
    ("娯楽/映画館", "飲食店/カフェ"): "ENTERTAINMENT_COMBO",
    ("娯楽/映画館", "飲食店/ファストフード"): "ENTERTAINMENT_COMBO",
    ("娯楽/劇場", "飲食店/レストラン"): "ENTERTAINMENT_COMBO",
    ("娯楽/劇場", "飲食店/バー"): "ENTERTAINMENT_COMBO",
    # 交通 × 商店/飲食
    ("交通/鉄道駅", "商店/コンビニ"): "TRANSIT_AMENITY",
    ("交通/鉄道駅", "飲食店/カフェ"): "TRANSIT_AMENITY",
    ("交通/鉄道駅", "飲食店/ファストフード"): "TRANSIT_AMENITY",
    # レジャー
    ("商店/書店", "飲食店/カフェ"): "LEISURE_COMBO",
    # 観光 × 飲食
    ("観光/名所", "飲食店/カフェ"): "TOURISM_COMBO",
    ("観光/名所", "飲食店/レストラン"): "TOURISM_COMBO",
    ("観光/博物館", "飲食店/カフェ"): "TOURISM_COMBO",
    # 金融サービス
    ("金融/銀行", "公共/郵便局"): "FINANCIAL_CLUSTER",
}

# 補完関係の距離閾値（メートル）
COMPLEMENTARY_DISTANCE_THRESHOLD = 200

# 競合関係の距離閾値（メートル）
COMPETITOR_DISTANCE_THRESHOLD = 150


# =============================================================================
# データクラス
# =============================================================================

@dataclass
class POINode:
    """POIノードを表すデータクラス"""
    id: str
    name: str
    name_en: str
    lat: float
    lon: float
    category: str
    subcategory: str
    area: str
    distance_from_station: float = 0.0
    direction: str = ""
    distance_zone: str = ""
    area_cluster: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "name_en": self.name_en,
            "lat": self.lat,
            "lon": self.lon,
            "category": self.category,
            "subcategory": self.subcategory,
            "area": self.area,
            "distance_from_station": self.distance_from_station,
            "direction": self.direction,
            "distance_zone": self.distance_zone,
            "area_cluster": self.area_cluster
        }


@dataclass
class CategoryNode:
    """カテゴリノードを表すデータクラス"""
    name: str
    name_jp: str
    poi_count: int = 0
    subcategories: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "name_jp": self.name_jp,
            "poi_count": self.poi_count,
            "subcategories": self.subcategories
        }


@dataclass
class AreaNode:
    """エリアノードを表すデータクラス"""
    name: str
    direction: str
    distance_zone: str
    poi_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "direction": self.direction,
            "distance_zone": self.distance_zone,
            "poi_count": self.poi_count
        }


@dataclass
class GraphStats:
    """グラフ統計情報"""
    num_poi_nodes: int = 0
    num_category_nodes: int = 0
    num_subcategory_nodes: int = 0
    num_area_nodes: int = 0
    num_landmark_nodes: int = 0
    num_brand_nodes: int = 0
    num_belongs_to_edges: int = 0
    num_located_in_edges: int = 0
    num_near_to_edges: int = 0
    num_same_area_edges: int = 0
    num_adjacent_to_edges: int = 0
    num_distance_from_edges: int = 0
    # 拡張エッジ
    num_same_brand_edges: int = 0
    num_complementary_edges: int = 0
    num_competitor_edges: int = 0
    num_same_cuisine_edges: int = 0
    num_same_hours_edges: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": {
                "poi": self.num_poi_nodes,
                "category": self.num_category_nodes,
                "subcategory": self.num_subcategory_nodes,
                "area": self.num_area_nodes,
                "landmark": self.num_landmark_nodes,
                "brand": self.num_brand_nodes,
                "total": (self.num_poi_nodes + self.num_category_nodes +
                         self.num_subcategory_nodes + self.num_area_nodes +
                         self.num_landmark_nodes + self.num_brand_nodes)
            },
            "edges": {
                "belongs_to": self.num_belongs_to_edges,
                "located_in": self.num_located_in_edges,
                "near_to": self.num_near_to_edges,
                "same_area": self.num_same_area_edges,
                "adjacent_to": self.num_adjacent_to_edges,
                "distance_from": self.num_distance_from_edges,
                "same_brand": self.num_same_brand_edges,
                "complementary": self.num_complementary_edges,
                "competitor": self.num_competitor_edges,
                "same_cuisine": self.num_same_cuisine_edges,
                "same_hours": self.num_same_hours_edges,
                "total": (self.num_belongs_to_edges + self.num_located_in_edges +
                         self.num_near_to_edges + self.num_same_area_edges +
                         self.num_adjacent_to_edges + self.num_distance_from_edges +
                         self.num_same_brand_edges + self.num_complementary_edges +
                         self.num_competitor_edges + self.num_same_cuisine_edges +
                         self.num_same_hours_edges)
            }
        }


# =============================================================================
# 距離・方向計算関数
# =============================================================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    2点間のHaversine距離を計算（メートル単位）

    Args:
        lat1, lon1: 地点1の緯度・経度
        lat2, lon2: 地点2の緯度・経度

    Returns:
        距離（メートル）
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_M * c


def calculate_direction(from_lat: float, from_lon: float,
                        to_lat: float, to_lon: float) -> str:
    """
    ある地点から別の地点への方向を8方位で判定

    Args:
        from_lat, from_lon: 基準地点の緯度・経度
        to_lat, to_lon: 対象地点の緯度・経度

    Returns:
        方向（8方位の英語名）
    """
    delta_lat = to_lat - from_lat
    delta_lon = to_lon - from_lon

    # 中心付近の場合
    if abs(delta_lat) < 0.0001 and abs(delta_lon) < 0.0001:
        return "center"

    # 角度計算（北を0度として時計回り）
    angle = math.degrees(math.atan2(delta_lon, delta_lat))
    if angle < 0:
        angle += 360

    # 8方位に変換
    directions = ["north", "northeast", "east", "southeast",
                  "south", "southwest", "west", "northwest"]
    index = round(angle / 45) % 8

    return directions[index]


def get_distance_zone(distance_m: float) -> str:
    """
    距離に基づいてゾーンを判定

    Args:
        distance_m: 距離（メートル）

    Returns:
        距離ゾーン名
    """
    if distance_m < DISTANCE_ZONES["station"]:
        return "station"
    elif distance_m < DISTANCE_ZONES["near"]:
        return "near"
    elif distance_m < DISTANCE_ZONES["mid"]:
        return "mid"
    else:
        return "far"


def get_adjacent_directions(direction: str) -> List[str]:
    """
    指定した方向に隣接する方向を取得

    Args:
        direction: 方向（8方位）

    Returns:
        隣接する方向のリスト
    """
    if direction == "center":
        return DIRECTIONS

    idx = DIRECTIONS.index(direction)
    prev_idx = (idx - 1) % 8
    next_idx = (idx + 1) % 8

    return [DIRECTIONS[prev_idx], direction, DIRECTIONS[next_idx]]


# =============================================================================
# POIグラフビルダークラス
# =============================================================================

class POIGraphBuilder:
    """POIナレッジグラフを構築するクラス"""

    def __init__(self, near_distance_threshold: float = NEAR_DISTANCE_THRESHOLD,
                 max_near_neighbors: int = 20,
                 station: Optional[Dict[str, Any]] = None):
        """
        Args:
            near_distance_threshold: NEAR_TOエッジの距離閾値（メートル）
            max_near_neighbors: 各POIあたりの最大NEAR_TOエッジ数
            station: 基準駅の座標辞書（デフォルトは渋谷駅）
        """
        if not HAS_NETWORKX:
            raise ImportError("networkx is required. Install with: pip install networkx")

        self.graph = nx.DiGraph()
        self.near_distance_threshold = near_distance_threshold
        self.max_near_neighbors = max_near_neighbors
        self.station = station if station is not None else SHIBUYA_STATION

        # ノードコレクション
        self.poi_nodes: Dict[str, POINode] = {}
        self.category_nodes: Dict[str, CategoryNode] = {}
        self.subcategory_nodes: Dict[str, str] = {}  # subcategory -> category
        self.area_nodes: Dict[str, AreaNode] = {}

        # 統計情報
        self.stats = GraphStats()

    def load_pois_from_json(self, json_path: str) -> List[Dict[str, Any]]:
        """
        JSONファイルからPOIデータを読み込む

        Args:
            json_path: POI JSONファイルのパス

        Returns:
            POIデータのリスト
        """
        with open(json_path, "r", encoding="utf-8") as f:
            pois = json.load(f)
        return pois

    def _parse_category(self, category_str: str) -> Tuple[str, str]:
        """
        カテゴリ文字列をカテゴリとサブカテゴリに分割

        Args:
            category_str: カテゴリ文字列（例: "飲食店/カフェ"）

        Returns:
            (カテゴリ, サブカテゴリ) のタプル
        """
        if "/" in category_str:
            parts = category_str.split("/", 1)
            return parts[0], parts[1]
        return category_str, category_str

    def _create_poi_node(self, poi_data: Dict[str, Any]) -> POINode:
        """
        POIデータからPOIノードを作成

        Args:
            poi_data: POI辞書データ

        Returns:
            POINode
        """
        metadata = poi_data.get("metadata", poi_data)

        lat = metadata.get("lat", 0.0)
        lon = metadata.get("lon", 0.0)
        category_str = metadata.get("category", "その他/その他")
        category, subcategory = self._parse_category(category_str)

        # 基準駅からの距離・方向を計算
        distance = haversine_distance(
            self.station["lat"], self.station["lon"],
            lat, lon
        )
        direction = calculate_direction(
            self.station["lat"], self.station["lon"],
            lat, lon
        )
        distance_zone = get_distance_zone(distance)
        area_cluster = f"{direction}_{distance_zone}"

        return POINode(
            id=poi_data.get("id", metadata.get("osm_id", "")),
            name=metadata.get("name", ""),
            name_en=metadata.get("name_en", ""),
            lat=lat,
            lon=lon,
            category=category,
            subcategory=subcategory,
            area=metadata.get("area", ""),
            distance_from_station=distance,
            direction=direction,
            distance_zone=distance_zone,
            area_cluster=area_cluster
        )

    def build_graph(self, pois: List[Dict[str, Any]],
                   include_near_edges: bool = True,
                   include_same_area_edges: bool = True,
                   include_extended_edges: bool = True,
                   verbose: bool = True) -> nx.DiGraph:
        """
        POIデータからナレッジグラフを構築

        Args:
            pois: POIデータのリスト
            include_near_edges: NEAR_TOエッジを含めるか
            include_same_area_edges: SAME_AREAエッジを含めるか
            include_extended_edges: 拡張エッジ（ブランド、補完、競合等）を含めるか
            verbose: 進捗表示するか

        Returns:
            構築されたNetworkXグラフ
        """
        # POIデータを保存（拡張エッジ用）
        self._pois_data = pois

        if verbose:
            print(f"Building POI Knowledge Graph from {len(pois)} POIs...")

        # 1. ランドマークノード（渋谷駅）を追加
        self._add_landmark_node()

        # 2. POIノードを作成・追加
        for poi_data in pois:
            poi_node = self._create_poi_node(poi_data)
            self._add_poi_node(poi_node, poi_data)

        if verbose:
            print(f"  - Added {len(self.poi_nodes)} POI nodes")

        # 3. カテゴリ・サブカテゴリノードを追加
        self._add_category_nodes()
        if verbose:
            print(f"  - Added {len(self.category_nodes)} category nodes")
            print(f"  - Added {len(self.subcategory_nodes)} subcategory nodes")

        # 4. エリアノードを追加
        self._add_area_nodes()
        if verbose:
            print(f"  - Added {len(self.area_nodes)} area nodes")

        # 5. BELONGS_TOエッジを追加
        self._add_belongs_to_edges()
        if verbose:
            print(f"  - Added {self.stats.num_belongs_to_edges} BELONGS_TO edges")

        # 6. LOCATED_INエッジを追加
        self._add_located_in_edges()
        if verbose:
            print(f"  - Added {self.stats.num_located_in_edges} LOCATED_IN edges")

        # 7. DISTANCE_FROMエッジを追加
        self._add_distance_from_edges()
        if verbose:
            print(f"  - Added {self.stats.num_distance_from_edges} DISTANCE_FROM edges")

        # 8. ADJACENT_TOエッジを追加
        self._add_adjacent_to_edges()
        if verbose:
            print(f"  - Added {self.stats.num_adjacent_to_edges} ADJACENT_TO edges")

        # 9. NEAR_TOエッジを追加（オプション）
        if include_near_edges:
            self._add_near_to_edges(verbose=verbose)
            if verbose:
                print(f"  - Added {self.stats.num_near_to_edges} NEAR_TO edges")

        # 10. SAME_AREAエッジを追加（オプション）
        if include_same_area_edges:
            self._add_same_area_edges(verbose=verbose)
            if verbose:
                print(f"  - Added {self.stats.num_same_area_edges} SAME_AREA edges")

        # 11-15. 拡張エッジを追加（オプション）
        if include_extended_edges:
            if verbose:
                print("\n  [Extended Edges]")

            # 11. SAME_BRANDエッジ
            self._add_same_brand_edges(verbose=verbose)
            if verbose:
                print(f"  - Added {self.stats.num_same_brand_edges} SAME_BRAND edges")

            # 12. COMPLEMENTARY（補完関係）エッジ
            self._add_complementary_edges(verbose=verbose)
            if verbose:
                print(f"  - Added {self.stats.num_complementary_edges} COMPLEMENTARY edges")

            # 13. COMPETITOR（競合関係）エッジ
            self._add_competitor_edges(verbose=verbose)
            if verbose:
                print(f"  - Added {self.stats.num_competitor_edges} COMPETITOR edges")

            # 14. SAME_CUISINEエッジ
            self._add_same_cuisine_edges(verbose=verbose)
            if verbose:
                print(f"  - Added {self.stats.num_same_cuisine_edges} SAME_CUISINE edges")

            # 15. SAME_HOURS（営業時間類似）エッジ
            self._add_same_hours_edges(verbose=verbose)
            if verbose:
                print(f"  - Added {self.stats.num_same_hours_edges} SAME_HOURS edges")

        # 統計情報を更新
        self._update_stats()

        if verbose:
            stats = self.stats.to_dict()
            print(f"\nGraph Statistics:")
            print(f"  Total nodes: {stats['nodes']['total']}")
            print(f"  Total edges: {stats['edges']['total']}")

        return self.graph

    def _add_landmark_node(self):
        """ランドマークノード（基準駅）を追加"""
        # 駅名からノードIDを生成
        station_name = self.station.get("name", "station")
        node_id = f"landmark:{station_name}"
        self.graph.add_node(
            node_id,
            node_type="landmark",
            name=self.station["name"],
            lat=self.station["lat"],
            lon=self.station["lon"]
        )
        self._landmark_node_id = node_id
        self.stats.num_landmark_nodes = 1

    def _add_poi_node(self, poi_node: POINode, poi_data: Dict[str, Any] = None):
        """POIノードをグラフに追加"""
        node_id = f"poi:{poi_node.id}"
        self.poi_nodes[poi_node.id] = poi_node

        # 拡張メタデータを取得
        metadata = poi_data.get("metadata", poi_data) if poi_data else {}
        extended_attrs = {
            "brand": metadata.get("brand"),
            "cuisine": metadata.get("cuisine"),
            "opening_hours": metadata.get("opening_hours"),
            "is_24h": metadata.get("is_24h", False),
            "late_night": metadata.get("late_night", False),
            "early_morning": metadata.get("early_morning", False),
            "wheelchair": metadata.get("wheelchair"),
            "internet_access": metadata.get("internet_access"),
        }

        self.graph.add_node(
            node_id,
            node_type="poi",
            **poi_node.to_dict(),
            **extended_attrs
        )
        self.stats.num_poi_nodes += 1

    def _add_category_nodes(self):
        """カテゴリ・サブカテゴリノードを追加"""
        category_counts = defaultdict(int)
        category_subcats = defaultdict(set)

        for poi in self.poi_nodes.values():
            category_counts[poi.category] += 1
            category_subcats[poi.category].add(poi.subcategory)
            self.subcategory_nodes[poi.subcategory] = poi.category

        # カテゴリノード追加
        for category, count in category_counts.items():
            node_id = f"category:{category}"
            subcats = list(category_subcats[category])

            cat_node = CategoryNode(
                name=category,
                name_jp=category,
                poi_count=count,
                subcategories=subcats
            )
            self.category_nodes[category] = cat_node

            self.graph.add_node(
                node_id,
                node_type="category",
                **cat_node.to_dict()
            )
            self.stats.num_category_nodes += 1

        # サブカテゴリノード追加
        for subcategory, category in self.subcategory_nodes.items():
            if subcategory != category:  # カテゴリと同名でない場合のみ
                node_id = f"subcategory:{subcategory}"
                self.graph.add_node(
                    node_id,
                    node_type="subcategory",
                    name=subcategory,
                    parent_category=category
                )
                self.stats.num_subcategory_nodes += 1

                # PARENT_OFエッジを追加
                self.graph.add_edge(
                    f"category:{category}",
                    node_id,
                    edge_type="PARENT_OF"
                )

    def _add_area_nodes(self):
        """エリアノードを追加"""
        area_counts = defaultdict(int)

        for poi in self.poi_nodes.values():
            area_counts[poi.area_cluster] += 1

        for area_cluster, count in area_counts.items():
            if "_" in area_cluster:
                direction, distance_zone = area_cluster.rsplit("_", 1)
            else:
                direction = area_cluster
                distance_zone = "unknown"

            node_id = f"area:{area_cluster}"
            area_node = AreaNode(
                name=area_cluster,
                direction=direction,
                distance_zone=distance_zone,
                poi_count=count
            )
            self.area_nodes[area_cluster] = area_node

            self.graph.add_node(
                node_id,
                node_type="area",
                **area_node.to_dict()
            )
            self.stats.num_area_nodes += 1

    def _add_belongs_to_edges(self):
        """BELONGS_TOエッジを追加（POI → Category/Subcategory）"""
        for poi_id, poi in self.poi_nodes.items():
            poi_node_id = f"poi:{poi_id}"

            # カテゴリへのエッジ
            cat_node_id = f"category:{poi.category}"
            if self.graph.has_node(cat_node_id):
                self.graph.add_edge(
                    poi_node_id,
                    cat_node_id,
                    edge_type="BELONGS_TO"
                )
                self.stats.num_belongs_to_edges += 1

            # サブカテゴリへのエッジ（カテゴリと異なる場合）
            if poi.subcategory != poi.category:
                subcat_node_id = f"subcategory:{poi.subcategory}"
                if self.graph.has_node(subcat_node_id):
                    self.graph.add_edge(
                        poi_node_id,
                        subcat_node_id,
                        edge_type="BELONGS_TO"
                    )
                    self.stats.num_belongs_to_edges += 1

    def _add_located_in_edges(self):
        """LOCATED_INエッジを追加（POI → Area）"""
        for poi_id, poi in self.poi_nodes.items():
            poi_node_id = f"poi:{poi_id}"
            area_node_id = f"area:{poi.area_cluster}"

            if self.graph.has_node(area_node_id):
                self.graph.add_edge(
                    poi_node_id,
                    area_node_id,
                    edge_type="LOCATED_IN"
                )
                self.stats.num_located_in_edges += 1

    def _add_distance_from_edges(self):
        """DISTANCE_FROMエッジを追加（POI → Landmark）"""
        landmark_id = self._landmark_node_id

        for poi_id, poi in self.poi_nodes.items():
            poi_node_id = f"poi:{poi_id}"

            self.graph.add_edge(
                poi_node_id,
                landmark_id,
                edge_type="DISTANCE_FROM",
                distance_m=poi.distance_from_station,
                direction=poi.direction
            )
            self.stats.num_distance_from_edges += 1

    def _add_adjacent_to_edges(self):
        """ADJACENT_TOエッジを追加（Area → Area）"""
        area_list = list(self.area_nodes.keys())

        for area1 in area_list:
            area1_node = self.area_nodes[area1]
            adj_directions = get_adjacent_directions(area1_node.direction)

            for area2 in area_list:
                if area1 == area2:
                    continue

                area2_node = self.area_nodes[area2]

                # 隣接条件: 方向が隣接 AND 距離ゾーンが同じか隣接
                direction_adjacent = area2_node.direction in adj_directions

                zone_order = ["station", "near", "mid", "far"]
                try:
                    zone1_idx = zone_order.index(area1_node.distance_zone)
                    zone2_idx = zone_order.index(area2_node.distance_zone)
                    zone_adjacent = abs(zone1_idx - zone2_idx) <= 1
                except ValueError:
                    zone_adjacent = False

                if direction_adjacent and zone_adjacent:
                    area1_id = f"area:{area1}"
                    area2_id = f"area:{area2}"

                    if not self.graph.has_edge(area1_id, area2_id):
                        self.graph.add_edge(
                            area1_id,
                            area2_id,
                            edge_type="ADJACENT_TO"
                        )
                        self.stats.num_adjacent_to_edges += 1

    def _add_near_to_edges(self, verbose: bool = True):
        """NEAR_TOエッジを追加（POI → POI、距離閾値以内）"""
        poi_list = list(self.poi_nodes.items())
        n = len(poi_list)

        if verbose:
            print(f"  Computing NEAR_TO edges for {n} POIs...")

        for i, (poi1_id, poi1) in enumerate(poi_list):
            if verbose and (i + 1) % 200 == 0:
                print(f"    Progress: {i + 1}/{n}")

            # 近いPOIを距離順で収集
            near_pois = []

            for poi2_id, poi2 in poi_list:
                if poi1_id == poi2_id:
                    continue

                distance = haversine_distance(
                    poi1.lat, poi1.lon,
                    poi2.lat, poi2.lon
                )

                if distance <= self.near_distance_threshold:
                    near_pois.append((poi2_id, distance))

            # 距離順でソートして上位N件のみエッジを追加
            near_pois.sort(key=lambda x: x[1])

            for poi2_id, distance in near_pois[:self.max_near_neighbors]:
                self.graph.add_edge(
                    f"poi:{poi1_id}",
                    f"poi:{poi2_id}",
                    edge_type="NEAR_TO",
                    distance_m=distance
                )
                self.stats.num_near_to_edges += 1

    def _add_same_area_edges(self, verbose: bool = True):
        """SAME_AREAエッジを追加（同一エリアクラスタ内のPOI間）"""
        # エリアクラスタごとにPOIをグループ化
        area_pois = defaultdict(list)
        for poi_id, poi in self.poi_nodes.items():
            area_pois[poi.area_cluster].append(poi_id)

        if verbose:
            print(f"  Computing SAME_AREA edges for {len(area_pois)} areas...")

        for area, poi_ids in area_pois.items():
            # 同一エリア内のPOI間でエッジを張る（双方向ではなく片方向のみ）
            for i, poi1_id in enumerate(poi_ids):
                for poi2_id in poi_ids[i + 1:]:
                    self.graph.add_edge(
                        f"poi:{poi1_id}",
                        f"poi:{poi2_id}",
                        edge_type="SAME_AREA",
                        area=area
                    )
                    self.stats.num_same_area_edges += 1

    # =========================================================================
    # 拡張エッジ追加メソッド
    # =========================================================================

    def _add_same_brand_edges(self, verbose: bool = True):
        """SAME_BRANDエッジを追加（同一ブランド/チェーンのPOI間）"""
        # ブランドごとにPOIをグループ化
        brand_pois = defaultdict(list)

        for node_id in self.graph.nodes():
            if not node_id.startswith("poi:"):
                continue
            node_data = self.graph.nodes[node_id]
            brand = node_data.get("brand")
            if brand:
                brand_pois[brand].append(node_id)

        if verbose:
            brand_count = len([b for b, pois in brand_pois.items() if len(pois) > 1])
            print(f"  Computing SAME_BRAND edges for {brand_count} brands with multiple POIs...")

        for brand, poi_ids in brand_pois.items():
            if len(poi_ids) < 2:
                continue

            # 同一ブランドのPOI間でエッジを張る
            for i, poi1_id in enumerate(poi_ids):
                for poi2_id in poi_ids[i + 1:]:
                    self.graph.add_edge(
                        poi1_id,
                        poi2_id,
                        edge_type="SAME_BRAND",
                        brand=brand
                    )
                    self.stats.num_same_brand_edges += 1

    def _add_complementary_edges(self, verbose: bool = True):
        """COMPLEMENTARY（補完関係）エッジを追加"""
        if verbose:
            print(f"  Computing COMPLEMENTARY edges...")

        # カテゴリごとにPOIをグループ化
        category_pois = defaultdict(list)
        for poi_id, poi in self.poi_nodes.items():
            full_category = f"{poi.category}/{poi.subcategory}"
            category_pois[full_category].append((poi_id, poi))

        # 補完関係ルールに基づいてエッジを追加
        for (cat1, cat2), relation_type in COMPLEMENTARY_RULES.items():
            pois1 = category_pois.get(cat1, [])
            pois2 = category_pois.get(cat2, [])

            if not pois1 or not pois2:
                continue

            for poi1_id, poi1 in pois1:
                for poi2_id, poi2 in pois2:
                    distance = haversine_distance(
                        poi1.lat, poi1.lon,
                        poi2.lat, poi2.lon
                    )

                    if distance <= COMPLEMENTARY_DISTANCE_THRESHOLD:
                        self.graph.add_edge(
                            f"poi:{poi1_id}",
                            f"poi:{poi2_id}",
                            edge_type="COMPLEMENTARY",
                            relation_subtype=relation_type,
                            distance_m=distance
                        )
                        self.stats.num_complementary_edges += 1

    def _add_competitor_edges(self, verbose: bool = True):
        """COMPETITOR（競合関係）エッジを追加（同カテゴリの近接POI）"""
        if verbose:
            print(f"  Computing COMPETITOR edges...")

        # サブカテゴリごとにPOIをグループ化
        subcategory_pois = defaultdict(list)
        for poi_id, poi in self.poi_nodes.items():
            full_category = f"{poi.category}/{poi.subcategory}"
            subcategory_pois[full_category].append((poi_id, poi))

        for category, pois in subcategory_pois.items():
            if len(pois) < 2:
                continue

            # 同カテゴリ内で近接するPOI間に競合エッジを追加
            for i, (poi1_id, poi1) in enumerate(pois):
                for poi2_id, poi2 in pois[i + 1:]:
                    distance = haversine_distance(
                        poi1.lat, poi1.lon,
                        poi2.lat, poi2.lon
                    )

                    if distance <= COMPETITOR_DISTANCE_THRESHOLD:
                        self.graph.add_edge(
                            f"poi:{poi1_id}",
                            f"poi:{poi2_id}",
                            edge_type="COMPETITOR",
                            category=category,
                            distance_m=distance
                        )
                        self.stats.num_competitor_edges += 1

    def _add_same_cuisine_edges(self, verbose: bool = True):
        """SAME_CUISINEエッジを追加（同一料理ジャンルのPOI間）"""
        # 料理ジャンルごとにPOIをグループ化
        cuisine_pois = defaultdict(list)

        for node_id in self.graph.nodes():
            if not node_id.startswith("poi:"):
                continue
            node_data = self.graph.nodes[node_id]
            cuisine = node_data.get("cuisine")
            if cuisine:
                # カンマ区切りの場合は分割
                for c in cuisine.split(";"):
                    c = c.strip()
                    if c:
                        cuisine_pois[c].append(node_id)

        if verbose:
            cuisine_count = len([c for c, pois in cuisine_pois.items() if len(pois) > 1])
            print(f"  Computing SAME_CUISINE edges for {cuisine_count} cuisines with multiple POIs...")

        for cuisine, poi_ids in cuisine_pois.items():
            if len(poi_ids) < 2:
                continue

            # 同一料理ジャンルのPOI間でエッジを張る（上限あり）
            max_edges_per_cuisine = 50  # 組み合わせ爆発を防ぐ
            edge_count = 0

            for i, poi1_id in enumerate(poi_ids):
                if edge_count >= max_edges_per_cuisine:
                    break
                for poi2_id in poi_ids[i + 1:]:
                    if edge_count >= max_edges_per_cuisine:
                        break
                    self.graph.add_edge(
                        poi1_id,
                        poi2_id,
                        edge_type="SAME_CUISINE",
                        cuisine=cuisine
                    )
                    self.stats.num_same_cuisine_edges += 1
                    edge_count += 1

    def _add_same_hours_edges(self, verbose: bool = True):
        """SAME_HOURS（営業時間類似）エッジを追加"""
        # 営業時間パターンごとにPOIをグループ化
        hours_patterns = {
            "24h": [],
            "late_night": [],
            "early_morning": []
        }

        for node_id in self.graph.nodes():
            if not node_id.startswith("poi:"):
                continue
            node_data = self.graph.nodes[node_id]

            if node_data.get("is_24h"):
                hours_patterns["24h"].append(node_id)
            elif node_data.get("late_night"):
                hours_patterns["late_night"].append(node_id)
            elif node_data.get("early_morning"):
                hours_patterns["early_morning"].append(node_id)

        if verbose:
            print(f"  Computing SAME_HOURS edges (24h: {len(hours_patterns['24h'])}, "
                  f"late_night: {len(hours_patterns['late_night'])}, "
                  f"early_morning: {len(hours_patterns['early_morning'])})")

        for pattern, poi_ids in hours_patterns.items():
            if len(poi_ids) < 2:
                continue

            # 同一営業時間パターンのPOI間でエッジを張る（上限あり）
            max_edges_per_pattern = 100
            edge_count = 0

            for i, poi1_id in enumerate(poi_ids):
                if edge_count >= max_edges_per_pattern:
                    break
                for poi2_id in poi_ids[i + 1:]:
                    if edge_count >= max_edges_per_pattern:
                        break
                    self.graph.add_edge(
                        poi1_id,
                        poi2_id,
                        edge_type="SAME_HOURS",
                        hours_pattern=pattern
                    )
                    self.stats.num_same_hours_edges += 1
                    edge_count += 1

    def _update_stats(self):
        """統計情報を更新"""
        self.stats.num_poi_nodes = len(self.poi_nodes)
        self.stats.num_category_nodes = len(self.category_nodes)
        self.stats.num_area_nodes = len(self.area_nodes)

    def get_stats(self) -> Dict[str, Any]:
        """グラフ統計情報を取得"""
        return self.stats.to_dict()

    def get_graph(self) -> nx.DiGraph:
        """構築されたグラフを取得"""
        return self.graph

    def save_graph(self, path: str, format: str = "graphml"):
        """
        グラフをファイルに保存

        Args:
            path: 保存先パス
            format: 保存形式（graphml, gexf, json）
        """
        if format == "graphml":
            nx.write_graphml(self.graph, path)
        elif format == "gexf":
            nx.write_gexf(self.graph, path)
        elif format == "json":
            from networkx.readwrite import json_graph
            data = json_graph.node_link_data(self.graph)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

    @classmethod
    def load_graph(cls, path: str, format: str = "graphml") -> nx.DiGraph:
        """
        ファイルからグラフを読み込む

        Args:
            path: ファイルパス
            format: ファイル形式

        Returns:
            読み込んだグラフ
        """
        if format == "graphml":
            return nx.read_graphml(path)
        elif format == "gexf":
            return nx.read_gexf(path)
        elif format == "json":
            from networkx.readwrite import json_graph
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return json_graph.node_link_graph(data)
        else:
            raise ValueError(f"Unsupported format: {format}")


# =============================================================================
# グラフクエリ関数
# =============================================================================

def get_pois_by_category(graph: nx.DiGraph, category: str) -> List[str]:
    """
    指定カテゴリに属するPOIを取得

    Args:
        graph: POIグラフ
        category: カテゴリ名

    Returns:
        POIノードIDのリスト
    """
    category_node = f"category:{category}"
    if not graph.has_node(category_node):
        return []

    # BELONGS_TOエッジでカテゴリを指しているPOIを取得
    pois = []
    for node in graph.predecessors(category_node):
        if graph.nodes[node].get("node_type") == "poi":
            pois.append(node)

    return pois


def get_pois_by_area(graph: nx.DiGraph, area: str) -> List[str]:
    """
    指定エリアに位置するPOIを取得

    Args:
        graph: POIグラフ
        area: エリア名（例: "east_near"）

    Returns:
        POIノードIDのリスト
    """
    area_node = f"area:{area}"
    if not graph.has_node(area_node):
        return []

    # LOCATED_INエッジでエリアを指しているPOIを取得
    pois = []
    for node in graph.predecessors(area_node):
        if graph.nodes[node].get("node_type") == "poi":
            pois.append(node)

    return pois


def get_nearby_pois(graph: nx.DiGraph, poi_id: str, max_distance: float = None) -> List[Tuple[str, float]]:
    """
    指定POIの近隣POIを取得

    Args:
        graph: POIグラフ
        poi_id: POIノードID（"poi:xxx"形式）
        max_distance: 最大距離（メートル）、Noneの場合は全てのNEAR_TOエッジ

    Returns:
        (POIノードID, 距離) のタプルリスト
    """
    if not graph.has_node(poi_id):
        return []

    nearby = []
    for _, target, data in graph.out_edges(poi_id, data=True):
        if data.get("edge_type") == "NEAR_TO":
            distance = data.get("distance_m", 0)
            if max_distance is None or distance <= max_distance:
                nearby.append((target, distance))

    return sorted(nearby, key=lambda x: x[1])


def get_pois_in_same_area(graph: nx.DiGraph, poi_id: str) -> List[str]:
    """
    指定POIと同じエリアにあるPOIを取得

    Args:
        graph: POIグラフ
        poi_id: POIノードID

    Returns:
        POIノードIDのリスト
    """
    if not graph.has_node(poi_id):
        return []

    same_area = []
    for _, target, data in graph.out_edges(poi_id, data=True):
        if data.get("edge_type") == "SAME_AREA":
            same_area.append(target)

    # 逆方向のエッジも確認
    for source, _, data in graph.in_edges(poi_id, data=True):
        if data.get("edge_type") == "SAME_AREA":
            same_area.append(source)

    return list(set(same_area))


def find_pois_with_both_categories(graph: nx.DiGraph,
                                   category1: str,
                                   category2: str,
                                   same_area: bool = True) -> List[Dict[str, Any]]:
    """
    2つのカテゴリのPOIが共存するエリアを探索

    Args:
        graph: POIグラフ
        category1: カテゴリ1
        category2: カテゴリ2
        same_area: 同一エリア内で探すか

    Returns:
        共存情報のリスト
    """
    pois1 = get_pois_by_category(graph, category1)
    pois2 = get_pois_by_category(graph, category2)

    results = []

    if same_area:
        # エリアごとにグループ化
        for poi1 in pois1:
            # POI1のエリアを取得
            area = None
            for _, target, data in graph.out_edges(poi1, data=True):
                if data.get("edge_type") == "LOCATED_IN":
                    area = target
                    break

            if area:
                # 同じエリアにあるカテゴリ2のPOIを探す
                for poi2 in pois2:
                    for _, target, data in graph.out_edges(poi2, data=True):
                        if data.get("edge_type") == "LOCATED_IN" and target == area:
                            results.append({
                                "poi1": poi1,
                                "poi1_name": graph.nodes[poi1].get("name"),
                                "poi2": poi2,
                                "poi2_name": graph.nodes[poi2].get("name"),
                                "area": area
                            })
                            break

    return results


# =============================================================================
# メイン実行
# =============================================================================

if __name__ == "__main__":
    import sys

    # デフォルトのPOIファイルパス
    poi_file = "poi_documents.json"
    if len(sys.argv) > 1:
        poi_file = sys.argv[1]

    print(f"Loading POIs from: {poi_file}")

    # グラフ構築
    builder = POIGraphBuilder()
    pois = builder.load_pois_from_json(poi_file)
    graph = builder.build_graph(pois)

    # 統計表示
    stats = builder.get_stats()
    print(f"\nFinal Statistics:")
    print(f"  Nodes: {stats['nodes']}")
    print(f"  Edges: {stats['edges']}")

    # サンプルクエリ
    print("\n--- Sample Queries ---")

    # カテゴリ別POI数
    for category in ["飲食店", "商店", "交通"]:
        pois = get_pois_by_category(graph, category)
        print(f"  {category}: {len(pois)} POIs")
