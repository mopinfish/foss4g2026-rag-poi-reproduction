"""
geo_utils.py - 地理座標計算ユーティリティ

Phase 6: RAG改善のための座標計算・方向判定・エリアクラスタリング機能
Phase 9-B: 複数エリア・ランドマーク対応

作成日: 2026-01-22
更新日: 2026-02-18
プロジェクト: experiments-local-llm
"""

import math
import re
from typing import Tuple, List, Dict, Any, Optional
from dataclasses import dataclass


# =============================================================================
# 定数定義
# =============================================================================

# 複数駅の座標（Phase 9-B）
STATIONS = {
    "渋谷駅": {"name": "渋谷駅", "lat": 35.658034, "lon": 139.701636},
    "新宿駅": {"name": "新宿駅", "lat": 35.689607, "lon": 139.700571},
    "池袋駅": {"name": "池袋駅", "lat": 35.729503, "lon": 139.710999},
    "東京駅": {"name": "東京駅", "lat": 35.681236, "lon": 139.767125},
}

# 後方互換: SHIBUYA_STATION は STATIONS["渋谷駅"] と同一オブジェクト
SHIBUYA_STATION = STATIONS["渋谷駅"]

# エリアキーと駅名のマッピング
AREA_STATION_MAP = {
    "shibuya": "渋谷駅",
    "shinjuku": "新宿駅",
    "ikebukuro": "池袋駅",
    "tokyo": "東京駅",
}

# ランドマーク座標テーブル（Phase 9-B）
# 将来的にはGeocodingツール（Nominatim等）に置き換え予定
LANDMARKS = {
    # 渋谷エリア
    "渋谷109": {"lat": 35.659517, "lon": 139.698471, "area_key": "shibuya"},
    "ハチ公像": {"lat": 35.659020, "lon": 139.700464, "area_key": "shibuya"},
    "渋谷ヒカリエ": {"lat": 35.659098, "lon": 139.703628, "area_key": "shibuya"},
    "渋谷スクランブルスクエア": {"lat": 35.658580, "lon": 139.702095, "area_key": "shibuya"},
    # 新宿エリア
    "東京都庁": {"lat": 35.689634, "lon": 139.691577, "area_key": "shinjuku"},
    "新宿御苑": {"lat": 35.685175, "lon": 139.710052, "area_key": "shinjuku"},
    "歌舞伎町": {"lat": 35.694003, "lon": 139.703506, "area_key": "shinjuku"},
    "新宿アルタ": {"lat": 35.692854, "lon": 139.701238, "area_key": "shinjuku"},
    # 池袋エリア
    "サンシャインシティ": {"lat": 35.729185, "lon": 139.718611, "area_key": "ikebukuro"},
    "池袋西口公園": {"lat": 35.730070, "lon": 139.709747, "area_key": "ikebukuro"},
    "東武百貨店池袋店": {"lat": 35.729641, "lon": 139.710815, "area_key": "ikebukuro"},
    # 東京エリア
    "東京国際フォーラム": {"lat": 35.676987, "lon": 139.763489, "area_key": "tokyo"},
    "KITTE": {"lat": 35.679032, "lon": 139.765650, "area_key": "tokyo"},
    "丸ビル": {"lat": 35.681461, "lon": 139.763641, "area_key": "tokyo"},
    "皇居前広場": {"lat": 35.680959, "lon": 139.757280, "area_key": "tokyo"},
}

# 地球の半径（メートル）
EARTH_RADIUS_M = 6371000

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

# 簡略化方向（4方位）
SIMPLIFIED_DIRECTION = {
    "north": "north",
    "northeast": "east",
    "east": "east",
    "southeast": "east",
    "south": "south",
    "southwest": "west",
    "west": "west",
    "northwest": "north"
}


# =============================================================================
# データクラス
# =============================================================================

@dataclass
class GeoPoint:
    """地理座標を表すデータクラス"""
    lat: float
    lon: float
    name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "name": self.name
        }


@dataclass
class SpatialInfo:
    """空間情報を表すデータクラス"""
    distance_m: float
    direction: str
    direction_jp: str
    area_cluster: str
    distance_zone: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "distance_m": self.distance_m,
            "direction": self.direction,
            "direction_jp": self.direction_jp,
            "area_cluster": self.area_cluster,
            "distance_zone": self.distance_zone
        }


# =============================================================================
# 距離計算関数
# =============================================================================

def haversine_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float
) -> float:
    """
    2点間の距離をHaversine公式で計算（メートル単位）
    
    Args:
        lat1, lon1: 点1の緯度・経度
        lat2, lon2: 点2の緯度・経度
    
    Returns:
        距離（メートル）
    
    Example:
        >>> haversine_distance(35.658034, 139.701636, 35.6595, 139.7004)
        179.23  # 約179m
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2) ** 2 + 
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return EARTH_RADIUS_M * c


def distance_from_station(
    lat: float, lon: float,
    station: Dict[str, float] = None
) -> float:
    """
    指定した駅からの距離を計算
    
    Args:
        lat, lon: 対象地点の緯度・経度
        station: 基準駅の座標辞書（デフォルトは渋谷駅）
    
    Returns:
        距離（メートル）
    """
    if station is None:
        station = SHIBUYA_STATION
    
    return haversine_distance(
        station["lat"], station["lon"],
        lat, lon
    )


def get_distance_zone(distance_m: float) -> str:
    """
    距離に基づいてゾーンを判定
    
    Args:
        distance_m: 距離（メートル）
    
    Returns:
        ゾーン名（"station", "near", "mid", "far"）
    """
    if distance_m < 200:
        return "station"
    elif distance_m < 500:
        return "near"
    elif distance_m < 800:
        return "mid"
    else:
        return "far"


# =============================================================================
# 方向判定関数
# =============================================================================

def get_direction(
    base_lat: float, base_lon: float,
    target_lat: float, target_lon: float
) -> str:
    """
    基準点から見た対象点の方向を判定（8方位）
    
    Args:
        base_lat, base_lon: 基準点の緯度・経度
        target_lat, target_lon: 対象点の緯度・経度
    
    Returns:
        方向（"north", "south", "east", "west", 
              "northeast", "northwest", "southeast", "southwest"）
    
    Example:
        >>> get_direction(35.658034, 139.701636, 35.660, 139.705)
        'northeast'
    """
    delta_lat = target_lat - base_lat
    delta_lon = target_lon - base_lon
    
    # 非常に近い場合は中心
    if abs(delta_lat) < 0.0001 and abs(delta_lon) < 0.0001:
        return "center"
    
    # 角度を計算（北を0度、時計回りで正）
    angle = math.degrees(math.atan2(delta_lon, delta_lat))
    
    # 8方位の判定
    if -22.5 <= angle < 22.5:
        return "north"
    elif 22.5 <= angle < 67.5:
        return "northeast"
    elif 67.5 <= angle < 112.5:
        return "east"
    elif 112.5 <= angle < 157.5:
        return "southeast"
    elif angle >= 157.5 or angle < -157.5:
        return "south"
    elif -157.5 <= angle < -112.5:
        return "southwest"
    elif -112.5 <= angle < -67.5:
        return "west"
    else:
        return "northwest"


def direction_from_station(
    lat: float, lon: float,
    station: Dict[str, float] = None
) -> str:
    """
    指定した駅から見た方向を判定
    
    Args:
        lat, lon: 対象地点の緯度・経度
        station: 基準駅の座標辞書（デフォルトは渋谷駅）
    
    Returns:
        方向（8方位）
    """
    if station is None:
        station = SHIBUYA_STATION
    
    return get_direction(
        station["lat"], station["lon"],
        lat, lon
    )


def get_direction_jp(direction: str) -> str:
    """
    方向を日本語に変換
    
    Args:
        direction: 英語の方向
    
    Returns:
        日本語の方向
    """
    return DIRECTION_JP.get(direction, direction)


def simplify_direction(direction: str) -> str:
    """
    8方位を4方位に簡略化
    
    Args:
        direction: 8方位の方向
    
    Returns:
        4方位の方向
    """
    return SIMPLIFIED_DIRECTION.get(direction, direction)


def is_east_side(direction: str) -> bool:
    """東側かどうかを判定"""
    return direction in ["east", "northeast", "southeast"]


def is_west_side(direction: str) -> bool:
    """西側かどうかを判定"""
    return direction in ["west", "northwest", "southwest"]


def is_north_side(direction: str) -> bool:
    """北側かどうかを判定"""
    return direction in ["north", "northeast", "northwest"]


def is_south_side(direction: str) -> bool:
    """南側かどうかを判定"""
    return direction in ["south", "southeast", "southwest"]


# =============================================================================
# エリアクラスタリング関数
# =============================================================================

def get_area_cluster(
    lat: float, lon: float,
    station: Dict[str, float] = None
) -> str:
    """
    座標からエリアクラスタを判定
    
    Args:
        lat, lon: 対象地点の緯度・経度
        station: 基準駅の座標辞書（デフォルトは渋谷駅）
    
    Returns:
        エリアクラスタ名（例: "east_near", "west_station"）
    
    Example:
        >>> get_area_cluster(35.660, 139.705)
        'east_near'
    """
    if station is None:
        station = SHIBUYA_STATION
    
    direction = direction_from_station(lat, lon, station)
    distance = distance_from_station(lat, lon, station)
    distance_zone = get_distance_zone(distance)
    
    # 方向を簡略化（4方位）
    simple_direction = simplify_direction(direction)
    
    # 中心の場合は特別扱い
    if direction == "center":
        return "station_center"
    
    return f"{simple_direction}_{distance_zone}"


# =============================================================================
# 空間情報計算関数
# =============================================================================

def compute_spatial_info(
    lat: float, lon: float,
    station: Dict[str, float] = None
) -> SpatialInfo:
    """
    POIの空間情報を一括計算
    
    Args:
        lat, lon: 対象地点の緯度・経度
        station: 基準駅の座標辞書（デフォルトは渋谷駅）
    
    Returns:
        SpatialInfoオブジェクト
    """
    if station is None:
        station = SHIBUYA_STATION
    
    distance = distance_from_station(lat, lon, station)
    direction = direction_from_station(lat, lon, station)
    
    return SpatialInfo(
        distance_m=round(distance, 2),
        direction=direction,
        direction_jp=get_direction_jp(direction),
        area_cluster=get_area_cluster(lat, lon, station),
        distance_zone=get_distance_zone(distance)
    )


def enrich_poi_with_spatial_info(
    poi: Dict[str, Any],
    station: Dict[str, float] = None
) -> Dict[str, Any]:
    """
    POIデータに空間情報を追加

    Args:
        poi: POIデータ辞書（lat, lonを含む。metadata内にある場合も対応）
        station: 基準駅の座標辞書

    Returns:
        空間情報を追加したPOIデータ
    """
    # lat/lonをトップレベルまたはmetadataから取得
    lat = poi.get("lat") or poi.get("metadata", {}).get("lat")
    lon = poi.get("lon") or poi.get("metadata", {}).get("lon")

    if lat is None or lon is None:
        return poi

    spatial_info = compute_spatial_info(lat, lon, station)

    enriched = poi.copy()
    enriched["distance_from_station"] = spatial_info.distance_m
    enriched["direction_from_station"] = spatial_info.direction
    enriched["direction_from_station_jp"] = spatial_info.direction_jp
    enriched["area_cluster"] = spatial_info.area_cluster
    enriched["distance_zone"] = spatial_info.distance_zone

    return enriched


def enrich_all_pois(
    pois: List[Dict[str, Any]],
    station: Dict[str, float] = None
) -> List[Dict[str, Any]]:
    """
    全POIデータに空間情報を追加
    
    Args:
        pois: POIデータのリスト
        station: 基準駅の座標辞書
    
    Returns:
        空間情報を追加したPOIデータのリスト
    """
    return [enrich_poi_with_spatial_info(poi, station) for poi in pois]


# =============================================================================
# フィルタリング関数
# =============================================================================

def filter_by_distance(
    pois: List[Dict[str, Any]],
    max_distance_m: float,
    station: Dict[str, float] = None
) -> List[Dict[str, Any]]:
    """
    距離でPOIをフィルタリング
    
    Args:
        pois: POIデータのリスト
        max_distance_m: 最大距離（メートル）
        station: 基準駅の座標辞書
    
    Returns:
        フィルタリングされたPOIリスト
    """
    if station is None:
        station = SHIBUYA_STATION
    
    result = []
    for poi in pois:
        if poi.get("lat") and poi.get("lon"):
            distance = distance_from_station(poi["lat"], poi["lon"], station)
            if distance <= max_distance_m:
                result.append(poi)
    
    return result


def filter_by_direction(
    pois: List[Dict[str, Any]],
    directions: List[str],
    station: Dict[str, float] = None
) -> List[Dict[str, Any]]:
    """
    方向でPOIをフィルタリング
    
    Args:
        pois: POIデータのリスト
        directions: 含める方向のリスト（例: ["east", "northeast"]）
        station: 基準駅の座標辞書
    
    Returns:
        フィルタリングされたPOIリスト
    """
    if station is None:
        station = SHIBUYA_STATION
    
    result = []
    for poi in pois:
        if poi.get("lat") and poi.get("lon"):
            direction = direction_from_station(poi["lat"], poi["lon"], station)
            if direction in directions:
                result.append(poi)
    
    return result


def filter_east_side(
    pois: List[Dict[str, Any]],
    station: Dict[str, float] = None
) -> List[Dict[str, Any]]:
    """東側のPOIをフィルタリング"""
    return filter_by_direction(pois, ["east", "northeast", "southeast"], station)


def filter_west_side(
    pois: List[Dict[str, Any]],
    station: Dict[str, float] = None
) -> List[Dict[str, Any]]:
    """西側のPOIをフィルタリング"""
    return filter_by_direction(pois, ["west", "northwest", "southwest"], station)


def filter_by_area_cluster(
    pois: List[Dict[str, Any]],
    clusters: List[str]
) -> List[Dict[str, Any]]:
    """
    エリアクラスタでPOIをフィルタリング
    
    Args:
        pois: 空間情報を持つPOIデータのリスト
        clusters: 含めるクラスタのリスト（例: ["east_near", "east_station"]）
    
    Returns:
        フィルタリングされたPOIリスト
    """
    return [poi for poi in pois if poi.get("area_cluster") in clusters]


# =============================================================================
# Phase 6.2: 最近傍検索・半径フィルタ・感度分析
# =============================================================================

def get_nearest_pois(
    pois: List[Dict[str, Any]],
    category: Optional[str] = None,
    top_n: int = 3,
    station: Dict[str, float] = None
) -> List[Dict[str, Any]]:
    """
    駅に最も近いPOIを取得（距離順ソート）
    
    Args:
        pois: POIデータのリスト（空間情報付き推奨）
        category: フィルタするカテゴリ（部分一致、Noneで全カテゴリ）
        top_n: 取得する件数
        station: 基準駅の座標辞書
    
    Returns:
        距離順にソートされたPOIリスト（最大top_n件）
    
    Example:
        >>> nearest_cafes = get_nearest_pois(pois, category="カフェ", top_n=3)
        >>> print(nearest_cafes[0]["name"], nearest_cafes[0]["distance_from_station"])
    """
    if station is None:
        station = SHIBUYA_STATION
    
    # カテゴリフィルタ
    if category:
        filtered = [p for p in pois if category in p.get("category", "")]
    else:
        filtered = pois
    
    # 距離情報を追加（なければ計算）
    pois_with_distance = []
    for poi in filtered:
        if poi.get("lat") and poi.get("lon"):
            if "distance_from_station" not in poi:
                distance = distance_from_station(poi["lat"], poi["lon"], station)
                poi_copy = poi.copy()
                poi_copy["distance_from_station"] = round(distance, 2)
                pois_with_distance.append(poi_copy)
            else:
                pois_with_distance.append(poi)
    
    # 距離でソート
    sorted_pois = sorted(
        pois_with_distance,
        key=lambda p: p.get("distance_from_station", float('inf'))
    )
    
    return sorted_pois[:top_n]


def get_farthest_pois(
    pois: List[Dict[str, Any]],
    category: Optional[str] = None,
    top_n: int = 3,
    station: Dict[str, float] = None
) -> List[Dict[str, Any]]:
    """
    駅から最も遠いPOIを取得（距離逆順ソート）
    
    Args:
        pois: POIデータのリスト
        category: フィルタするカテゴリ（部分一致）
        top_n: 取得する件数
        station: 基準駅の座標辞書
    
    Returns:
        距離逆順にソートされたPOIリスト（最大top_n件）
    """
    if station is None:
        station = SHIBUYA_STATION
    
    # カテゴリフィルタ
    if category:
        filtered = [p for p in pois if category in p.get("category", "")]
    else:
        filtered = pois
    
    # 距離情報を追加
    pois_with_distance = []
    for poi in filtered:
        if poi.get("lat") and poi.get("lon"):
            if "distance_from_station" not in poi:
                distance = distance_from_station(poi["lat"], poi["lon"], station)
                poi_copy = poi.copy()
                poi_copy["distance_from_station"] = round(distance, 2)
                pois_with_distance.append(poi_copy)
            else:
                pois_with_distance.append(poi)
    
    # 距離逆順でソート
    sorted_pois = sorted(
        pois_with_distance,
        key=lambda p: p.get("distance_from_station", 0),
        reverse=True
    )
    
    return sorted_pois[:top_n]


def filter_by_radius(
    pois: List[Dict[str, Any]],
    radius_m: float,
    category: Optional[str] = None,
    station: Dict[str, float] = None
) -> List[Dict[str, Any]]:
    """
    指定半径内のPOIをフィルタリング
    
    Args:
        pois: POIデータのリスト
        radius_m: 半径（メートル）
        category: フィルタするカテゴリ（部分一致、Noneで全カテゴリ）
        station: 基準駅の座標辞書
    
    Returns:
        半径内のPOIリスト
    
    Example:
        >>> cafes_500m = filter_by_radius(pois, 500, category="カフェ")
        >>> print(f"500m以内のカフェ: {len(cafes_500m)}件")
    """
    if station is None:
        station = SHIBUYA_STATION
    
    result = []
    for poi in pois:
        # カテゴリフィルタ
        if category and category not in poi.get("category", ""):
            continue
        
        # 距離フィルタ
        if poi.get("lat") and poi.get("lon"):
            if "distance_from_station" in poi:
                distance = poi["distance_from_station"]
            else:
                distance = distance_from_station(poi["lat"], poi["lon"], station)
            
            if distance <= radius_m:
                result.append(poi)
    
    return result


def count_by_radius(
    pois: List[Dict[str, Any]],
    radius_m: float,
    category: Optional[str] = None,
    station: Dict[str, float] = None
) -> int:
    """
    指定半径内のPOI件数をカウント
    
    Args:
        pois: POIデータのリスト
        radius_m: 半径（メートル）
        category: フィルタするカテゴリ
        station: 基準駅の座標辞書
    
    Returns:
        半径内のPOI件数
    """
    return len(filter_by_radius(pois, radius_m, category, station))


@dataclass
class RadiusComparisonResult:
    """半径比較結果を表すデータクラス"""
    radius1_m: float
    radius2_m: float
    count1: int
    count2: int
    category: Optional[str]
    difference: int
    ratio: float  # count2 / count1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "radius1_m": self.radius1_m,
            "radius2_m": self.radius2_m,
            "count1": self.count1,
            "count2": self.count2,
            "category": self.category,
            "difference": self.difference,
            "ratio": self.ratio
        }
    
    def to_japanese(self) -> str:
        """日本語での説明文を生成"""
        cat_str = f"「{self.category}」" if self.category else "POI"
        
        if self.count1 == 0:
            return f"半径{self.radius1_m}m以内に{cat_str}はありません"
        
        change = self.count2 - self.count1
        if change > 0:
            return (f"半径{self.radius1_m}m: {self.count1}件 → "
                   f"半径{self.radius2_m}m: {self.count2}件 "
                   f"（+{change}件、{self.ratio:.1f}倍）")
        elif change < 0:
            return (f"半径{self.radius1_m}m: {self.count1}件 → "
                   f"半径{self.radius2_m}m: {self.count2}件 "
                   f"（{change}件、{self.ratio:.1f}倍）")
        else:
            return (f"半径{self.radius1_m}m・{self.radius2_m}m: "
                   f"ともに{self.count1}件（変化なし）")


def compare_by_radius(
    pois: List[Dict[str, Any]],
    radius1_m: float,
    radius2_m: float,
    category: Optional[str] = None,
    station: Dict[str, float] = None
) -> RadiusComparisonResult:
    """
    異なる半径での件数を比較（感度分析用）
    
    Args:
        pois: POIデータのリスト
        radius1_m: 半径1（メートル）
        radius2_m: 半径2（メートル）
        category: フィルタするカテゴリ
        station: 基準駅の座標辞書
    
    Returns:
        RadiusComparisonResult
    
    Example:
        >>> result = compare_by_radius(pois, 300, 500, category="カフェ")
        >>> print(result.to_japanese())
        '半径300m: 45件 → 半径500m: 89件 (+44件、1.98倍)'
    """
    if station is None:
        station = SHIBUYA_STATION
    
    count1 = count_by_radius(pois, radius1_m, category, station)
    count2 = count_by_radius(pois, radius2_m, category, station)
    
    ratio = count2 / count1 if count1 > 0 else 0
    
    return RadiusComparisonResult(
        radius1_m=radius1_m,
        radius2_m=radius2_m,
        count1=count1,
        count2=count2,
        category=category,
        difference=count2 - count1,
        ratio=round(ratio, 2)
    )


def analyze_radius_sensitivity(
    pois: List[Dict[str, Any]],
    category: Optional[str] = None,
    radii: List[float] = None,
    station: Dict[str, float] = None
) -> Dict[str, Any]:
    """
    複数の半径での件数変化を分析（感度分析）
    
    Args:
        pois: POIデータのリスト
        category: フィルタするカテゴリ
        radii: 分析する半径のリスト（デフォルト: [100, 200, 300, 500, 800, 1000]）
        station: 基準駅の座標辞書
    
    Returns:
        半径ごとの件数と分析結果
    
    Example:
        >>> result = analyze_radius_sensitivity(pois, category="カフェ")
        >>> for r, c in result["counts"].items():
        ...     print(f"{r}m: {c}件")
    """
    if station is None:
        station = SHIBUYA_STATION
    
    if radii is None:
        radii = [100, 200, 300, 500, 800, 1000]
    
    counts = {}
    for radius in sorted(radii):
        counts[radius] = count_by_radius(pois, radius, category, station)
    
    # 変化率の計算
    changes = []
    sorted_radii = sorted(radii)
    for i in range(1, len(sorted_radii)):
        r1, r2 = sorted_radii[i-1], sorted_radii[i]
        c1, c2 = counts[r1], counts[r2]
        if c1 > 0:
            change_rate = (c2 - c1) / c1 * 100
        else:
            change_rate = float('inf') if c2 > 0 else 0
        changes.append({
            "from_radius": r1,
            "to_radius": r2,
            "from_count": c1,
            "to_count": c2,
            "change": c2 - c1,
            "change_rate": round(change_rate, 1)
        })
    
    return {
        "category": category,
        "counts": counts,
        "changes": changes,
        "total_at_max_radius": counts[max(radii)],
        "radii_analyzed": sorted_radii
    }


def get_poi_distance_stats(
    pois: List[Dict[str, Any]],
    category: Optional[str] = None,
    station: Dict[str, float] = None
) -> Dict[str, float]:
    """
    POIの距離統計を計算
    
    Args:
        pois: POIデータのリスト
        category: フィルタするカテゴリ
        station: 基準駅の座標辞書
    
    Returns:
        統計情報（min, max, avg, median）
    """
    if station is None:
        station = SHIBUYA_STATION
    
    # カテゴリフィルタ
    if category:
        filtered = [p for p in pois if category in p.get("category", "")]
    else:
        filtered = pois
    
    # 距離を収集
    distances = []
    for poi in filtered:
        if poi.get("lat") and poi.get("lon"):
            if "distance_from_station" in poi:
                distances.append(poi["distance_from_station"])
            else:
                distances.append(distance_from_station(poi["lat"], poi["lon"], station))
    
    if not distances:
        return {"count": 0, "min": 0, "max": 0, "avg": 0, "median": 0}
    
    distances_sorted = sorted(distances)
    n = len(distances_sorted)
    
    return {
        "count": n,
        "min": round(distances_sorted[0], 1),
        "max": round(distances_sorted[-1], 1),
        "avg": round(sum(distances) / n, 1),
        "median": round(distances_sorted[n // 2], 1)
    }


def generate_proximity_context(
    pois: List[Dict[str, Any]],
    category: str,
    top_n: int = 3,
    station: Dict[str, float] = None
) -> str:
    """
    最近傍POI情報をLLMコンテキスト用に整形
    
    Args:
        pois: POIデータのリスト
        category: 対象カテゴリ
        top_n: 取得件数
        station: 基準駅の座標辞書
    
    Returns:
        整形されたコンテキスト文字列
    """
    nearest = get_nearest_pois(pois, category, top_n, station)
    
    if not nearest:
        return f"「{category}」に該当するPOIが見つかりませんでした。"
    
    lines = [f"【{category}の最寄りPOI（上位{len(nearest)}件）】"]
    for i, poi in enumerate(nearest, 1):
        name = poi.get("name", "不明")
        dist = poi.get("distance_from_station", "?")
        direction = poi.get("direction_from_station_jp", "")
        lines.append(f"  {i}. {name}")
        lines.append(f"     距離: {dist}m（{direction}方向）")
    
    # 統計情報も追加
    stats = get_poi_distance_stats(pois, category, station)
    lines.append(f"\n【{category}の距離統計】")
    lines.append(f"  総数: {stats['count']}件")
    lines.append(f"  最短: {stats['min']}m / 最長: {stats['max']}m")
    lines.append(f"  平均: {stats['avg']}m / 中央値: {stats['median']}m")
    
    return "\n".join(lines)


def generate_sensitivity_context(
    pois: List[Dict[str, Any]],
    category: str,
    radius1: float,
    radius2: float,
    station: Dict[str, float] = None
) -> str:
    """
    感度分析結果をLLMコンテキスト用に整形
    
    Args:
        pois: POIデータのリスト
        category: 対象カテゴリ
        radius1: 比較半径1
        radius2: 比較半径2
        station: 基準駅の座標辞書
    
    Returns:
        整形されたコンテキスト文字列
    """
    comparison = compare_by_radius(pois, radius1, radius2, category, station)
    sensitivity = analyze_radius_sensitivity(pois, category, [radius1, radius2], station)
    
    lines = [f"【{category}の半径別件数比較】"]
    lines.append(comparison.to_japanese())
    
    # 追加分析
    if comparison.count1 > 0:
        lines.append(f"\n【分析】")
        if comparison.ratio >= 1.5:
            lines.append(f"  半径を{radius1}m→{radius2}mに広げると{comparison.ratio:.1f}倍に増加します。")
            lines.append(f"  {radius1}m以内では{category}が少なく、周辺に分布しています。")
        elif comparison.ratio >= 1.2:
            lines.append(f"  半径を広げると{comparison.difference}件増加しますが、")
            lines.append(f"  {radius1}m以内にも十分な件数があります。")
        else:
            lines.append(f"  半径を変えても大きな変化はありません。")
            lines.append(f"  {category}は駅周辺に集中しています。")
    
    return "\n".join(lines)


# =============================================================================
# Phase 9-B: 駅・ランドマーク解決関数
# =============================================================================

def resolve_station(name_or_key: str) -> Optional[Dict[str, Any]]:
    """
    駅名またはエリアキーから駅座標情報を解決する

    Args:
        name_or_key: 駅名（例: "渋谷駅"）またはエリアキー（例: "shibuya"）

    Returns:
        {"name": str, "lat": float, "lon": float} or None
    """
    # 駅名での完全一致
    if name_or_key in STATIONS:
        return STATIONS[name_or_key]

    # エリアキーでの解決
    station_name = AREA_STATION_MAP.get(name_or_key)
    if station_name:
        return STATIONS[station_name]

    # 部分一致（"渋谷" → "渋谷駅"）
    for sname, sinfo in STATIONS.items():
        if name_or_key in sname or sname.replace("駅", "") in name_or_key:
            return sinfo

    return None


def resolve_landmark(name: str) -> Optional[Dict[str, Any]]:
    """
    ランドマーク名から座標情報を解決する

    Args:
        name: ランドマーク名

    Returns:
        {"lat": float, "lon": float, "area_key": str} or None
    """
    # 完全一致
    if name in LANDMARKS:
        return LANDMARKS[name]

    # 部分一致（曖昧さを減らすため、一致候補が1件の場合のみ返す）
    candidates = []
    for lm_name, lm_info in LANDMARKS.items():
        if lm_name in name or name in lm_name:
            candidates.append(lm_info)

    if len(candidates) == 1:
        return candidates[0]

    return None


# =============================================================================
# Phase 9-B: エリア特定関数
# =============================================================================

# エリア特定用キーワード（駅名・地名）
_AREA_KEYWORDS = {
    "shibuya": ["渋谷駅", "渋谷"],
    "shinjuku": ["新宿駅", "新宿"],
    "ikebukuro": ["池袋駅", "池袋"],
    "tokyo": ["東京駅"],  # "東京" 単体は広すぎるので除外
}

# 「東京駅」を先に確認し、残った「東京」が他エリアの一部でないことを保証する
# ための優先順序付きパターン
_AREA_KEYWORD_PATTERNS = None  # 遅延初期化


def _build_area_keyword_patterns():
    """エリアキーワードの正規表現パターンを構築（遅延初期化）"""
    global _AREA_KEYWORD_PATTERNS
    if _AREA_KEYWORD_PATTERNS is not None:
        return _AREA_KEYWORD_PATTERNS

    patterns = []
    for area_key, keywords in _AREA_KEYWORDS.items():
        # 長いキーワードを先にマッチさせる（「東京駅」>「東京」）
        for kw in sorted(keywords, key=len, reverse=True):
            patterns.append((area_key, kw))
    _AREA_KEYWORD_PATTERNS = patterns
    return patterns


def detect_target_area(question: str, areas_config: Optional[Dict] = None) -> Optional[str]:
    """
    質問文からターゲットエリアを特定する

    Args:
        question: 質問文
        areas_config: エリア設定辞書（osm_poi_fetcher.AREASと同形式）。
                      Noneの場合はデフォルトの4エリアを使用。

    Returns:
        エリアキー（例: "shibuya"）。複数エリアまたは特定不可の場合はNone。
    """
    # ランドマークからのエリア特定を優先
    for lm_name, lm_info in LANDMARKS.items():
        if lm_name in question:
            return lm_info["area_key"]

    # キーワードマッチング
    patterns = _build_area_keyword_patterns()
    matched_areas = set()

    for area_key, keyword in patterns:
        if keyword in question:
            matched_areas.add(area_key)

    # 単一エリアの場合のみ返す
    if len(matched_areas) == 1:
        return matched_areas.pop()

    return None


def detect_cross_area_query(question: str, areas_config: Optional[Dict] = None) -> List[str]:
    """
    質問文からクロスエリアクエリかどうかを判定し、関連エリアを返す

    Args:
        question: 質問文
        areas_config: エリア設定辞書

    Returns:
        関連エリアキーのリスト。クロスエリアでない場合は空リスト。
    """
    patterns = _build_area_keyword_patterns()
    matched_areas = set()

    # ランドマークからのエリア特定
    for lm_name, lm_info in LANDMARKS.items():
        if lm_name in question:
            matched_areas.add(lm_info["area_key"])

    # キーワードマッチング
    for area_key, keyword in patterns:
        if keyword in question:
            matched_areas.add(area_key)

    # 2つ以上のエリアがマッチした場合のみクロスエリア
    if len(matched_areas) >= 2:
        return sorted(matched_areas)

    # 「全エリア」「4エリア」などの表現を検出
    if re.search(r"(全エリア|全ての?エリア|4エリア|各エリア|すべての?エリア)", question):
        return sorted(AREA_STATION_MAP.keys())

    return []


# =============================================================================
# Phase 9-B: 広域POIエンリッチメント
# =============================================================================

def enrich_pois_for_area(
    pois: List[Dict[str, Any]],
    area_key: str,
    areas_config: Optional[Dict] = None
) -> List[Dict[str, Any]]:
    """
    特定エリアのPOIにそのエリアの基準駅からの空間情報を付与する

    Args:
        pois: POIデータのリスト
        area_key: エリアキー（例: "shibuya"）
        areas_config: エリア設定辞書。Noneの場合はデフォルトの駅座標を使用。

    Returns:
        空間情報を追加したPOIデータのリスト
    """
    # 基準駅を特定
    if areas_config and area_key in areas_config:
        station = areas_config[area_key]["station"]
    else:
        station_name = AREA_STATION_MAP.get(area_key)
        station = STATIONS.get(station_name) if station_name else None

    if station is None:
        station = SHIBUYA_STATION

    return enrich_all_pois(pois, station)


def enrich_all_areas(
    pois: List[Dict[str, Any]],
    areas_config: Optional[Dict] = None
) -> List[Dict[str, Any]]:
    """
    全POIデータにエリアごとの基準駅からの空間情報を付与する

    各POIの area_key メタデータに基づいて、そのエリアの基準駅からの
    距離・方角を計算する。area_key がないPOIは渋谷駅を基準に計算。

    Args:
        pois: POIデータのリスト（area_key メタデータ推奨）
        areas_config: エリア設定辞書

    Returns:
        空間情報を追加したPOIデータのリスト
    """
    result = []
    for poi in pois:
        # POIのエリアキーを取得（メタデータまたはトップレベル）
        area_key = (
            poi.get("area_key")
            or poi.get("metadata", {}).get("area_key")
        )

        # 基準駅を特定
        station = None
        if area_key:
            if areas_config and area_key in areas_config:
                station = areas_config[area_key]["station"]
            else:
                station_name = AREA_STATION_MAP.get(area_key)
                if station_name:
                    station = STATIONS[station_name]

        result.append(enrich_poi_with_spatial_info(poi, station))

    return result


# =============================================================================
# テスト・デバッグ用関数
# =============================================================================

def test_geo_utils():
    """
    geo_utilsモジュールの動作確認
    """
    print("=" * 60)
    print("geo_utils.py 動作確認")
    print("=" * 60)

    # テスト用の座標（渋谷駅周辺）
    test_points = [
        {"name": "東口方面", "lat": 35.659, "lon": 139.705},
        {"name": "西口方面", "lat": 35.658, "lon": 139.698},
        {"name": "北方面", "lat": 35.662, "lon": 139.701},
        {"name": "南方面", "lat": 35.654, "lon": 139.701},
        {"name": "駅近く", "lat": 35.6582, "lon": 139.7018},
    ]

    print(f"\n基準点: {SHIBUYA_STATION['name']}")
    print(f"座標: ({SHIBUYA_STATION['lat']}, {SHIBUYA_STATION['lon']})")

    print("\n--- 各地点の空間情報 ---")
    for point in test_points:
        info = compute_spatial_info(point["lat"], point["lon"])
        print(f"\n{point['name']}:")
        print(f"  距離: {info.distance_m:.1f}m")
        print(f"  方向: {info.direction} ({info.direction_jp})")
        print(f"  エリア: {info.area_cluster}")
        print(f"  ゾーン: {info.distance_zone}")

    # 東西判定テスト
    print("\n--- 東西判定テスト ---")
    for point in test_points:
        direction = direction_from_station(point["lat"], point["lon"])
        east = "東側" if is_east_side(direction) else ""
        west = "西側" if is_west_side(direction) else ""
        print(f"{point['name']}: {direction} → {east}{west}")

    # Phase 9-B: 後方互換テスト
    print("\n--- Phase 9-B: 後方互換テスト ---")
    assert SHIBUYA_STATION is STATIONS["渋谷駅"], "SHIBUYA_STATION は STATIONS['渋谷駅'] と同一オブジェクトでない"
    print("  ✅ SHIBUYA_STATION is STATIONS['渋谷駅']")

    # Phase 9-B: 駅解決テスト
    print("\n--- Phase 9-B: 駅解決テスト ---")
    assert resolve_station("渋谷駅") == STATIONS["渋谷駅"]
    assert resolve_station("shibuya") == STATIONS["渋谷駅"]
    assert resolve_station("shinjuku") == STATIONS["新宿駅"]
    assert resolve_station("存在しない") is None
    print("  ✅ resolve_station() 正常動作")

    # Phase 9-B: ランドマーク解決テスト
    print("\n--- Phase 9-B: ランドマーク解決テスト ---")
    assert resolve_landmark("渋谷109") is not None
    assert resolve_landmark("渋谷109")["area_key"] == "shibuya"
    assert resolve_landmark("サンシャインシティ")["area_key"] == "ikebukuro"
    assert resolve_landmark("存在しないランドマーク") is None
    print("  ✅ resolve_landmark() 正常動作")

    # Phase 9-B: エリア特定テスト
    print("\n--- Phase 9-B: エリア特定テスト ---")
    assert detect_target_area("渋谷駅周辺のカフェ") == "shibuya"
    assert detect_target_area("新宿駅に最も近いコンビニ") == "shinjuku"
    assert detect_target_area("サンシャインシティの近くのレストラン") == "ikebukuro"
    assert detect_target_area("渋谷と新宿でカフェが多いのは？") is None  # 複数エリア
    assert detect_target_area("おすすめのカフェは？") is None  # エリア不明
    print("  ✅ detect_target_area() 正常動作")

    # Phase 9-B: クロスエリア検出テスト
    print("\n--- Phase 9-B: クロスエリア検出テスト ---")
    cross = detect_cross_area_query("渋谷と新宿でカフェが多いのは？")
    assert "shibuya" in cross and "shinjuku" in cross
    assert detect_cross_area_query("おすすめのカフェは？") == []
    all_areas = detect_cross_area_query("全エリアのカフェ数は？")
    assert len(all_areas) == 4
    print("  ✅ detect_cross_area_query() 正常動作")

    print("\n✅ geo_utils.py 動作確認完了")


if __name__ == "__main__":
    test_geo_utils()
