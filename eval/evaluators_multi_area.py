#!/usr/bin/env python3
"""
evaluators_multi_area.py - Phase 9-B: 複数エリア対応評価モジュール

評価指標:
- keyword_hit_rate: キーワードヒット率（0.0-1.0）
- success: keyword_hit_rate >= 0.5
- area_detection_correct: エリア特定の正確性
- language_issue: 中国語混入検出

チェックポイント機能:
- 10件ごとにJSON保存
- 再開時はスキップ

system_fn仕様:
- Callable[[str], Dict]
- 入力: 質問文(str)
- 出力: {"answer": str, "detected_area": Optional[str]}
"""

import gc
import json
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable, Dict, List, Optional

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


# =============================================================================
# 評価結果データクラス
# =============================================================================

@dataclass
class MultiAreaEvalResult:
    """複数エリア対応評価結果"""
    test_id: str
    system_name: str
    target_area: Optional[str]
    query_type: str
    subcategory: str
    level: int
    answer: str
    time_sec: float
    keyword_hit_rate: float
    success: bool                    # keyword_hit_rate >= 0.5
    area_detected: Optional[str]
    area_detection_correct: bool
    error: Optional[str] = None
    language_issue: bool = False
    # 多次元評価スコア（Phase 9相当）
    reasoning_score: float = 0.0       # 0-5 推論の正確性
    evidence_score: float = 0.0        # 0-5 根拠の明示度
    constraint_score: float = 0.0      # 0-5 制約充足度
    uncertainty_score: float = 0.0     # 0-5 不確実性への言及
    has_coordinate: bool = False       # 座標情報の有無
    has_poi_name: bool = False         # POI名の含有
    composite_score: float = 0.0       # 0-100 レベル別複合スコア

    def to_dict(self) -> dict:
        """辞書に変換"""
        return asdict(self)


# =============================================================================
# 評価クラス
# =============================================================================

class MultiAreaEvaluator:
    """複数エリア対応評価クラス"""

    def __init__(self, areas_config: Optional[Dict] = None, all_pois: Optional[List] = None):
        """
        Args:
            areas_config: エリア設定辞書（osm_poi_fetcher.AREASパターン）
            all_pois: 全POIリスト（多次元評価のPOI名チェックに使用）
        """
        self.areas_config = areas_config or {}
        self.all_pois = all_pois or []

    def evaluate_keyword_hit_rate(self, answer: str, keywords: List[str]) -> float:
        """キーワードヒット率を計算 (0.0-1.0)

        Case-insensitive matching を行い、ヒット数 / 全キーワード数 を返す。
        """
        if not answer or not keywords:
            return 0.0

        answer_lower = answer.lower()
        hit_count = sum(1 for kw in keywords if kw.lower() in answer_lower)
        return hit_count / len(keywords)

    def detect_language_issue(self, answer: str) -> bool:
        """中国語混入を検出する

        中国語特有の文法パターン（語気助詞、代名詞、構文パターンなど）を
        正規表現でチェックし、いずれかにマッチすれば True を返す。
        """
        if not answer:
            return False

        # Chinese-specific patterns
        # NOTE: 「的」は日本語でも頻出（具体的、一般的 etc.）のため除外。
        #       「非常」も日本語で使われるため除外。
        #       代わりに中国語固有の構文・語彙に絞る。
        chinese_patterns = [
            r'[\u4e00-\u9fff]{2,}[了吗呢吧]',  # Chinese sentence-ending particles (的 excluded)
            r'这[个是里]',    # 这个, 这是, 这里
            r'那[个是里]',    # 那个, 那是, 那里
            r'我们|他们|她们',  # Chinese pronouns
            r'没有',         # 没有
            r'什么',         # 什么
            r'怎么',         # 怎么
            r'因此',         # 因此 (Chinese conjunction)
            r'无法',         # 无法
            r'关于',         # 关于
            r'工具',         # 工具 (Chinese for "tool", Agentic RAG residual)
            r'根据',         # 根据
        ]

        for pattern in chinese_patterns:
            if re.search(pattern, answer):
                return True

        return False

    # =================================================================
    # 多次元評価メソッド（evaluators_v2.py からポーティング）
    # =================================================================

    def _has_coordinate(self, answer: str) -> bool:
        """座標情報が含まれるかチェック"""
        if not answer:
            return False
        patterns = [
            r'35\.\d{3,}',
            r'139\.\d{3,}',
            r'緯度\s*[:：]?\s*\d+\.\d+',
            r'経度\s*[:：]?\s*\d+\.\d+',
        ]
        for pattern in patterns:
            if re.search(pattern, answer, re.IGNORECASE):
                return True
        return False

    def _has_poi_name(self, answer: str) -> bool:
        """POI名が含まれるかチェック（self.all_pois を使用）"""
        if not answer or not self.all_pois:
            return False
        for poi in self.all_pois:
            if isinstance(poi, dict):
                name = poi.get("metadata", {}).get("name", "") or poi.get("name", "")
            else:
                name = getattr(poi, "name", "")
            if name and len(name) > 2 and name in answer:
                return True
        return False

    def _evaluate_reasoning(self, answer: str) -> float:
        """推論の正確性を評価（0-5スコア）"""
        if not answer:
            return 0.0
        score = 0.0
        reasoning_indicators = [
            "なぜなら", "理由は", "考えられる", "推測", "判断",
            "したがって", "よって", "ため", "から", "ので",
            "比較すると", "分析すると", "評価すると",
            "多い", "少ない", "近い", "遠い", "集中", "分散",
        ]
        indicator_count = sum(1 for ind in reasoning_indicators if ind in answer)
        if indicator_count >= 5:
            score = 3.0
        elif indicator_count >= 3:
            score = 2.0
        elif indicator_count >= 1:
            score = 1.0
        if re.search(r'\d+\s*(件|軒|店|か所|箇所|m|メートル|分)', answer):
            score += 1.0
        comparison_patterns = [
            r'より(多|少|近|遠)',
            r'(最も|一番)(多|少|近|遠)',
            r'(高|低|大|小)い',
        ]
        for pattern in comparison_patterns:
            if re.search(pattern, answer):
                score += 0.5
                break
        return min(score, 5.0)

    def _evaluate_evidence(self, answer: str) -> float:
        """根拠の明示度を評価（0-5スコア、self.all_pois を使用）"""
        if not answer:
            return 0.0
        score = 0.0
        poi_name_count = 0
        if self.all_pois:
            for poi in self.all_pois:
                if isinstance(poi, dict):
                    name = poi.get("metadata", {}).get("name", "") or poi.get("name", "")
                else:
                    name = getattr(poi, "name", "")
                if name and len(name) > 2 and name in answer:
                    poi_name_count += 1
        if poi_name_count >= 5:
            score = 4.0
        elif poi_name_count >= 3:
            score = 3.0
        elif poi_name_count >= 1:
            score = 2.0
        if self._has_coordinate(answer):
            score += 0.5
        if re.search(r'(約|およそ)?\d+\s*(件|軒|店|か所)', answer):
            score += 0.5
        citation_patterns = [
            r'データ(から|によると|に基づ)',
            r'情報(から|によると|に基づ)',
            r'検索結果',
            r'POI',
        ]
        for pattern in citation_patterns:
            if re.search(pattern, answer):
                score += 0.5
                break
        return min(score, 5.0)

    def _evaluate_constraint(self, answer: str, constraints: Optional[List[str]] = None) -> float:
        """制約充足度を評価（0-5スコア）"""
        if not answer:
            return 0.0
        if not constraints:
            return 3.0  # 制約なしの場合は中立スコア
        satisfied_count = 0
        for constraint in constraints:
            if "m以内" in constraint or "メートル以内" in constraint:
                distance_match = re.search(r'(\d+)\s*m', constraint)
                if distance_match:
                    distance = distance_match.group(1)
                    if distance in answer or "近い" in answer or "近く" in answer:
                        satisfied_count += 1
            elif "電話番号あり" in constraint:
                if re.search(r'電話|TEL|\d{2,4}-\d{2,4}-\d{4}', answer, re.IGNORECASE):
                    satisfied_count += 1
            elif "ウェブサイトあり" in constraint:
                if re.search(r'(ウェブサイト|サイト|URL|http|www)', answer, re.IGNORECASE):
                    satisfied_count += 1
            elif "24時間営業" in constraint:
                if "24時間" in answer or "終日" in answer:
                    satisfied_count += 1
            elif "Wi-Fiあり" in constraint:
                if re.search(r'(Wi-?Fi|wifi|ワイファイ)', answer, re.IGNORECASE):
                    satisfied_count += 1
            elif "深夜営業" in constraint:
                if "深夜" in answer or "夜間" in answer or re.search(r'(2[2-4]|[0-4])時', answer):
                    satisfied_count += 1
            elif "を含む" in constraint or "を除外" in constraint:
                keyword = constraint.replace("を含む", "").replace("を除外", "").strip()
                if keyword in answer:
                    satisfied_count += 0.5
            else:
                # 汎用: 制約キーワードが回答に含まれるか
                if any(word in answer for word in constraint.split() if len(word) > 1):
                    satisfied_count += 0.5
        if len(constraints) > 0:
            ratio = satisfied_count / len(constraints)
            score = ratio * 5.0
        else:
            score = 3.0
        return min(score, 5.0)

    def _evaluate_uncertainty(self, answer: str) -> float:
        """不確実性への言及を評価（0-5スコア）"""
        if not answer:
            return 0.0
        score = 0.0
        uncertainty_indicators = [
            "可能性があ", "かもしれ", "推測", "推定",
            "不明", "わかりません", "確認できません",
            "データの限界", "情報がない", "情報が不足",
            "確実ではない", "断定できない",
            "おそらく", "恐らく", "思われ",
            "注意", "留意", "ご注意",
        ]
        distinction_indicators = [
            "データからは", "情報からは",
            "推測できる", "推測できない",
            "判断できる", "判断できない",
            "一方で", "ただし", "しかし",
        ]
        uncertainty_count = sum(1 for ind in uncertainty_indicators if ind in answer)
        distinction_count = sum(1 for ind in distinction_indicators if ind in answer)
        if uncertainty_count >= 3 and distinction_count >= 2:
            score = 5.0
        elif uncertainty_count >= 2 and distinction_count >= 1:
            score = 4.0
        elif uncertainty_count >= 2:
            score = 3.0
        elif uncertainty_count >= 1:
            score = 2.0
        elif distinction_count >= 1:
            score = 1.5
        return min(score, 5.0)

    def _calculate_composite(
        self,
        level: int,
        keyword_hits: int,
        keyword_total: int,
        has_coord: bool,
        has_name: bool,
        reasoning: float,
        evidence: float,
        constraint: float,
        uncertainty: float,
    ) -> float:
        """レベル別の複合スコアを計算（0-100）"""
        keyword_score = (keyword_hits / keyword_total * 100) if keyword_total > 0 else 0
        coord_score = 100 if has_coord else 0
        name_score = 100 if has_name else 0
        reasoning_norm = reasoning * 20  # 0-5 → 0-100
        evidence_norm = evidence * 20
        constraint_norm = constraint * 20
        uncertainty_norm = uncertainty * 20

        if level == 1:
            score = keyword_score * 0.4 + coord_score * 0.3 + name_score * 0.3
        elif level == 2:
            score = keyword_score * 0.3 + coord_score * 0.2 + reasoning_norm * 0.5
        elif level == 3:
            score = keyword_score * 0.2 + name_score * 0.2 + constraint_norm * 0.4 + evidence_norm * 0.2
        elif level == 4:
            score = reasoning_norm * 0.3 + evidence_norm * 0.3 + constraint_norm * 0.2 + uncertainty_norm * 0.2
        elif level == 5:
            score = reasoning_norm * 0.4 + evidence_norm * 0.3 + uncertainty_norm * 0.3
        else:
            score = keyword_score * 0.4 + coord_score * 0.3 + name_score * 0.3
        return round(score, 1)

    def _compute_multi_scores(self, answer: str, level: int,
                              keyword_hit_rate: float, constraints: Optional[List[str]] = None) -> dict:
        """回答テキストから多次元スコアを一括計算して辞書で返す"""
        has_coord = self._has_coordinate(answer)
        has_name = self._has_poi_name(answer)
        reasoning = self._evaluate_reasoning(answer)
        evidence = self._evaluate_evidence(answer)
        constraint = self._evaluate_constraint(answer, constraints)
        uncertainty = self._evaluate_uncertainty(answer)

        # keyword_hits / keyword_total を hit_rate から復元（composite計算用）
        # 正確なhit/total情報がないため、hit_rate×100で代用
        composite = self._calculate_composite(
            level=level,
            keyword_hits=round(keyword_hit_rate * 100),
            keyword_total=100,
            has_coord=has_coord,
            has_name=has_name,
            reasoning=reasoning,
            evidence=evidence,
            constraint=constraint,
            uncertainty=uncertainty,
        )
        return {
            "has_coordinate": has_coord,
            "has_poi_name": has_name,
            "reasoning_score": round(reasoning, 2),
            "evidence_score": round(evidence, 2),
            "constraint_score": round(constraint, 2),
            "uncertainty_score": round(uncertainty, 2),
            "composite_score": composite,
        }

    def evaluate_single_case(
        self,
        system_name: str,
        system_fn: Callable[[str], Dict],
        test_case,  # MultiAreaTestCase
    ) -> MultiAreaEvalResult:
        """1テストケースを評価

        Args:
            system_name: システム識別名
            system_fn: Callable[[str], Dict] - {"answer": str, "detected_area": Optional[str]}
            test_case: MultiAreaTestCase インスタンス

        Returns:
            MultiAreaEvalResult
        """
        start = time.time()
        try:
            result = system_fn(test_case.prompt)
            elapsed = time.time() - start
            answer = result.get("answer", "")
            detected_area = result.get("detected_area")

            keyword_hit_rate = self.evaluate_keyword_hit_rate(
                answer, test_case.expected_keywords
            )
            language_issue = self.detect_language_issue(answer)

            # Area detection correctness
            area_detection_correct = True
            if test_case.target_area is not None:
                area_detection_correct = (detected_area == test_case.target_area)

            # 多次元スコア計算
            constraints = getattr(test_case, 'constraints', None)
            multi = self._compute_multi_scores(
                answer, test_case.level, keyword_hit_rate, constraints
            )

            return MultiAreaEvalResult(
                test_id=test_case.id,
                system_name=system_name,
                target_area=test_case.target_area,
                query_type=test_case.query_type,
                subcategory=test_case.subcategory,
                level=test_case.level,
                answer=answer,
                time_sec=round(elapsed, 2),
                keyword_hit_rate=round(keyword_hit_rate, 4),
                success=keyword_hit_rate >= 0.5,
                area_detected=detected_area,
                area_detection_correct=area_detection_correct,
                language_issue=language_issue,
                **multi,
            )
        except Exception as e:
            elapsed = time.time() - start
            return MultiAreaEvalResult(
                test_id=test_case.id,
                system_name=system_name,
                target_area=test_case.target_area,
                query_type=test_case.query_type,
                subcategory=test_case.subcategory,
                level=test_case.level,
                answer="",
                time_sec=round(elapsed, 2),
                keyword_hit_rate=0.0,
                success=False,
                area_detected=None,
                area_detection_correct=False,
                error=str(e),
            )

    def evaluate_all(
        self,
        system_name: str,
        system_fn: Callable[[str], Dict],
        test_cases: List,
        checkpoint_file: Optional[str] = None,
    ) -> List[MultiAreaEvalResult]:
        """全テストケースを評価（チェックポイント付き）

        - 10件ごとにcheckpoint_fileにJSON保存
        - 再開時は既に完了したtest_idをスキップ
        """
        results: List[MultiAreaEvalResult] = []
        completed_ids: set = set()

        # Load checkpoint if exists
        if checkpoint_file:
            cp_path = Path(checkpoint_file)
            if cp_path.exists():
                with open(cp_path, encoding="utf-8") as f:
                    saved = json.load(f)
                for item in saved:
                    result = MultiAreaEvalResult(**item)
                    results.append(result)
                    completed_ids.add(result.test_id)
                print(f"チェックポイントから{len(completed_ids)}件復元しました")

        for i, tc in enumerate(test_cases):
            if tc.id in completed_ids:
                continue

            prompt_preview = tc.prompt[:40]
            print(f"  [{i+1}/{len(test_cases)}] {tc.id}: {prompt_preview}...")
            result = self.evaluate_single_case(system_name, system_fn, tc)
            results.append(result)

            # クエリごとのVRAM/RAM解放（CUDA OOM防止）
            gc.collect()
            if HAS_TORCH and torch.cuda.is_available():
                torch.cuda.empty_cache()

            # Checkpoint every 10 cases
            if checkpoint_file and len(results) % 10 == 0:
                self._save_checkpoint(checkpoint_file, results)
                if HAS_TORCH and torch.cuda.is_available():
                    vram_gb = torch.cuda.memory_allocated() / 1024**3
                    print(f"    [checkpoint] {len(results)} done, VRAM: {vram_gb:.2f} GB")

        # Final save
        if checkpoint_file:
            self._save_checkpoint(checkpoint_file, results)

        return results

    def _save_checkpoint(
        self, filepath: str, results: List[MultiAreaEvalResult]
    ) -> None:
        """チェックポイントをJSON保存"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                [r.to_dict() for r in results], f, ensure_ascii=False, indent=2
            )

    def generate_summary(self, results: List[MultiAreaEvalResult]) -> Dict:
        """評価結果のサマリーを生成

        Returns dict with keys:
        - overall: {success_rate, avg_keyword_hit_rate, avg_time_sec, total, error_count, language_issue_count}
        - by_area: {area_key: {success_rate, avg_keyword_hit_rate, count, avg_time_sec}}
        - by_level: {level: {success_rate, avg_keyword_hit_rate, count}}
        - by_query_type: {query_type: {success_rate, count}}
        - by_subcategory: {subcategory: {success_rate, avg_keyword_hit_rate, count}}
        - area_detection: {total, correct, accuracy}
        - cross_area: {success_rate, count, avg_time_sec}
        """
        if not results:
            return {}

        total = len(results)

        # --- overall ---
        success_count = sum(1 for r in results if r.success)
        error_count = sum(1 for r in results if r.error is not None)
        language_issue_count = sum(1 for r in results if r.language_issue)
        avg_khr = sum(r.keyword_hit_rate for r in results) / total
        avg_time = sum(r.time_sec for r in results) / total

        # 多次元スコア集計
        avg_composite = sum(r.composite_score for r in results) / total
        avg_reasoning = sum(r.reasoning_score for r in results) / total
        avg_evidence = sum(r.evidence_score for r in results) / total
        composite_success_count = sum(1 for r in results if r.composite_score >= 60)

        overall = {
            "success_rate": round(success_count / total, 4),
            "avg_keyword_hit_rate": round(avg_khr, 4),
            "avg_time_sec": round(avg_time, 2),
            "total": total,
            "error_count": error_count,
            "language_issue_count": language_issue_count,
            "avg_composite_score": round(avg_composite, 1),
            "avg_reasoning_score": round(avg_reasoning, 2),
            "avg_evidence_score": round(avg_evidence, 2),
            "composite_success_rate": round(composite_success_count / total, 4),
        }

        # --- by_area ---
        by_area: Dict[str, Dict] = {}
        area_groups: Dict[str, List[MultiAreaEvalResult]] = {}
        for r in results:
            area_key = r.target_area or "cross_area"
            area_groups.setdefault(area_key, []).append(r)

        for area_key, group in area_groups.items():
            count = len(group)
            s_rate = sum(1 for r in group if r.success) / count
            a_khr = sum(r.keyword_hit_rate for r in group) / count
            a_time = sum(r.time_sec for r in group) / count
            a_comp = sum(r.composite_score for r in group) / count
            by_area[area_key] = {
                "success_rate": round(s_rate, 4),
                "avg_keyword_hit_rate": round(a_khr, 4),
                "count": count,
                "avg_time_sec": round(a_time, 2),
                "avg_composite_score": round(a_comp, 1),
            }

        # --- by_level ---
        by_level: Dict[int, Dict] = {}
        level_groups: Dict[int, List[MultiAreaEvalResult]] = {}
        for r in results:
            level_groups.setdefault(r.level, []).append(r)

        for level, group in sorted(level_groups.items()):
            count = len(group)
            s_rate = sum(1 for r in group if r.success) / count
            a_khr = sum(r.keyword_hit_rate for r in group) / count
            l_comp = sum(r.composite_score for r in group) / count
            by_level[level] = {
                "success_rate": round(s_rate, 4),
                "avg_keyword_hit_rate": round(a_khr, 4),
                "count": count,
                "avg_composite_score": round(l_comp, 1),
            }

        # --- by_query_type ---
        by_query_type: Dict[str, Dict] = {}
        qt_groups: Dict[str, List[MultiAreaEvalResult]] = {}
        for r in results:
            qt_groups.setdefault(r.query_type, []).append(r)

        for qt, group in qt_groups.items():
            count = len(group)
            s_rate = sum(1 for r in group if r.success) / count
            by_query_type[qt] = {
                "success_rate": round(s_rate, 4),
                "count": count,
            }

        # --- by_subcategory ---
        by_subcategory: Dict[str, Dict] = {}
        subcat_groups: Dict[str, List[MultiAreaEvalResult]] = {}
        for r in results:
            subcat_groups.setdefault(r.subcategory, []).append(r)

        for subcat, group in subcat_groups.items():
            count = len(group)
            s_rate = sum(1 for r in group if r.success) / count
            a_khr = sum(r.keyword_hit_rate for r in group) / count
            by_subcategory[subcat] = {
                "success_rate": round(s_rate, 4),
                "avg_keyword_hit_rate": round(a_khr, 4),
                "count": count,
            }

        # --- area_detection ---
        results_with_area = [r for r in results if r.target_area is not None]
        ad_total = len(results_with_area)
        ad_correct = sum(1 for r in results_with_area if r.area_detection_correct)
        area_detection = {
            "total": ad_total,
            "correct": ad_correct,
            "accuracy": round(ad_correct / ad_total, 4) if ad_total > 0 else 0.0,
        }

        # --- cross_area ---
        cross_results = [r for r in results if r.query_type == "cross_area"]
        if cross_results:
            ca_count = len(cross_results)
            ca_success = sum(1 for r in cross_results if r.success) / ca_count
            ca_time = sum(r.time_sec for r in cross_results) / ca_count
            cross_area = {
                "success_rate": round(ca_success, 4),
                "count": ca_count,
                "avg_time_sec": round(ca_time, 2),
            }
        else:
            cross_area = {
                "success_rate": 0.0,
                "count": 0,
                "avg_time_sec": 0.0,
            }

        return {
            "overall": overall,
            "by_area": by_area,
            "by_level": by_level,
            "by_query_type": by_query_type,
            "by_subcategory": by_subcategory,
            "area_detection": area_detection,
            "cross_area": cross_area,
        }

    def compare_systems(
        self, all_results: Dict[str, List[MultiAreaEvalResult]]
    ) -> Dict:
        """複数システムの比較分析

        Args:
            all_results: {system_name: [MultiAreaEvalResult, ...]}

        Returns dict with:
        - summaries: {system_name: summary_dict}
        - rankings: sorted list of (system_name, overall_success_rate)
        - area_consistency: {system_name: score_variance_across_areas}
        """
        summaries: Dict[str, Dict] = {}
        rankings_data: List[tuple] = []

        for system_name, results in all_results.items():
            summary = self.generate_summary(results)
            summaries[system_name] = summary
            overall_sr = summary.get("overall", {}).get("success_rate", 0.0)
            rankings_data.append((system_name, overall_sr))

        # Sort rankings by success_rate descending
        rankings = sorted(rankings_data, key=lambda x: x[1], reverse=True)

        # Area consistency: variance of success_rate across areas
        area_consistency: Dict[str, float] = {}
        for system_name, results in all_results.items():
            summary = summaries[system_name]
            by_area = summary.get("by_area", {})
            if len(by_area) >= 2:
                rates = [v["success_rate"] for v in by_area.values()]
                mean_rate = sum(rates) / len(rates)
                variance = sum((r - mean_rate) ** 2 for r in rates) / len(rates)
                area_consistency[system_name] = round(variance, 6)
            else:
                area_consistency[system_name] = 0.0

        return {
            "summaries": summaries,
            "rankings": rankings,
            "area_consistency": area_consistency,
        }

    def recalculate_scores(
        self,
        results: List[MultiAreaEvalResult],
        test_cases: List,
    ) -> List[MultiAreaEvalResult]:
        """既存の結果に多次元スコアを事後計算して付与

        チェックポイントから復元した結果の answer テキストから
        多次元スコアを再計算する。test_cases は test_id でルックアップ。

        Args:
            results: 既存のMultiAreaEvalResultリスト
            test_cases: MultiAreaTestCaseリスト（constraints/level取得用）

        Returns:
            多次元スコアが付与された新しいMultiAreaEvalResultリスト
        """
        tc_map = {}
        for tc in test_cases:
            tc_map[tc.id] = tc

        updated = []
        for r in results:
            tc = tc_map.get(r.test_id)
            constraints = getattr(tc, 'constraints', None) if tc else None
            multi = self._compute_multi_scores(
                r.answer, r.level, r.keyword_hit_rate, constraints
            )
            # dataclassの新しいインスタンスを作成（元のフィールドを維持）
            d = r.to_dict()
            d.update(multi)
            updated.append(MultiAreaEvalResult(**d))
        return updated


# =============================================================================
# セルフテスト
# =============================================================================

if __name__ == "__main__":
    print("evaluators_multi_area.py セルフテスト")
    print("=" * 60)

    evaluator = MultiAreaEvaluator()

    # ------------------------------------------------------------------
    # 1. evaluate_keyword_hit_rate テスト
    # ------------------------------------------------------------------
    print("\n[1] evaluate_keyword_hit_rate テスト")
    rate = evaluator.evaluate_keyword_hit_rate(
        "渋谷駅周辺にはスターバックスやドトールがあります。",
        ["スターバックス", "ドトール", "タリーズ"],
    )
    print(f"  ヒット率: {rate:.4f} (期待: 0.6667)")
    assert abs(rate - 2 / 3) < 0.001, f"Expected ~0.6667, got {rate}"

    rate_empty = evaluator.evaluate_keyword_hit_rate("", ["a", "b"])
    assert rate_empty == 0.0, "Empty answer should return 0.0"

    rate_no_kw = evaluator.evaluate_keyword_hit_rate("hello", [])
    assert rate_no_kw == 0.0, "Empty keywords should return 0.0"
    print("  OK")

    # ------------------------------------------------------------------
    # 2. detect_language_issue テスト
    # ------------------------------------------------------------------
    print("\n[2] detect_language_issue テスト")
    assert evaluator.detect_language_issue("这是一个很好的地方") is True, \
        "Chinese text should be detected"
    assert evaluator.detect_language_issue("渋谷駅の近くにカフェがあります") is False, \
        "Japanese text should not be flagged"
    assert evaluator.detect_language_issue("我们可以去那个地方") is True, \
        "Chinese pronouns should be detected"
    assert evaluator.detect_language_issue("") is False, \
        "Empty string should return False"
    # 偽陽性テスト: 日本語の「具体的」「非常に」はフラグしない
    assert evaluator.detect_language_issue("具体的な座標は北緯35度です") is False, \
        "Japanese 具体的 should not be flagged"
    assert evaluator.detect_language_issue("非常に近くに位置しています") is False, \
        "Japanese 非常に should not be flagged"
    # 真の中国語混入テスト
    assert evaluator.detect_language_issue("因此，无法根据提供的信息回答") is True, \
        "Chinese 因此/无法/根据 should be detected"
    assert evaluator.detect_language_issue("工具を使用して確認しました") is True, \
        "Chinese 工具 (tool) should be detected"
    print("  OK")

    # ------------------------------------------------------------------
    # 3. generate_summary テスト (ダミーデータ)
    # ------------------------------------------------------------------
    print("\n[3] generate_summary テスト")

    dummy_results = [
        MultiAreaEvalResult(
            test_id="MA-SBY-L1-01",
            system_name="system_a",
            target_area="shibuya",
            query_type="single_area",
            subcategory="basic_location",
            level=1,
            answer="渋谷駅周辺にスターバックスがあります",
            time_sec=1.5,
            keyword_hit_rate=0.8,
            success=True,
            area_detected="shibuya",
            area_detection_correct=True,
        ),
        MultiAreaEvalResult(
            test_id="MA-SBY-L2-01",
            system_name="system_a",
            target_area="shibuya",
            query_type="single_area",
            subcategory="proximity",
            level=2,
            answer="最も近いコンビニはローソンです",
            time_sec=2.1,
            keyword_hit_rate=0.6,
            success=True,
            area_detected="shibuya",
            area_detection_correct=True,
        ),
        MultiAreaEvalResult(
            test_id="MA-SJK-L1-01",
            system_name="system_a",
            target_area="shinjuku",
            query_type="single_area",
            subcategory="basic_location",
            level=1,
            answer="新宿駅の東口にカフェがあります",
            time_sec=1.8,
            keyword_hit_rate=0.5,
            success=True,
            area_detected="shinjuku",
            area_detection_correct=True,
        ),
        MultiAreaEvalResult(
            test_id="MA-SJK-L3-01",
            system_name="system_a",
            target_area="shinjuku",
            query_type="single_area",
            subcategory="aggregation",
            level=3,
            answer="カフェは全部で5件です",
            time_sec=3.0,
            keyword_hit_rate=0.3,
            success=False,
            area_detected="ikebukuro",
            area_detection_correct=False,
        ),
        MultiAreaEvalResult(
            test_id="MA-CROSS-L2-01",
            system_name="system_a",
            target_area=None,
            query_type="cross_area",
            subcategory="comparison",
            level=2,
            answer="渋谷と新宿を比較すると新宿の方がカフェが多い",
            time_sec=4.5,
            keyword_hit_rate=0.7,
            success=True,
            area_detected=None,
            area_detection_correct=True,
        ),
        MultiAreaEvalResult(
            test_id="MA-IKB-L1-01",
            system_name="system_a",
            target_area="ikebukuro",
            query_type="single_area",
            subcategory="basic_location",
            level=1,
            answer="池袋駅周辺にレストランがあります",
            time_sec=1.2,
            keyword_hit_rate=1.0,
            success=True,
            area_detected="ikebukuro",
            area_detection_correct=True,
        ),
        MultiAreaEvalResult(
            test_id="MA-IKB-L2-01",
            system_name="system_a",
            target_area="ikebukuro",
            query_type="single_area",
            subcategory="proximity",
            level=2,
            answer="",
            time_sec=0.5,
            keyword_hit_rate=0.0,
            success=False,
            area_detected=None,
            area_detection_correct=False,
            error="Timeout",
        ),
        MultiAreaEvalResult(
            test_id="MA-CROSS-L3-01",
            system_name="system_a",
            target_area=None,
            query_type="cross_area",
            subcategory="comparison",
            level=3,
            answer="这是渋谷和新宿的比较结果",
            time_sec=5.0,
            keyword_hit_rate=0.4,
            success=False,
            area_detected=None,
            area_detection_correct=True,
            language_issue=True,
        ),
    ]

    summary = evaluator.generate_summary(dummy_results)

    print(f"  overall: {summary['overall']}")
    print(f"  by_area keys: {list(summary['by_area'].keys())}")
    print(f"  by_level keys: {list(summary['by_level'].keys())}")
    print(f"  by_query_type keys: {list(summary['by_query_type'].keys())}")
    print(f"  by_subcategory keys: {list(summary['by_subcategory'].keys())}")
    print(f"  area_detection: {summary['area_detection']}")
    print(f"  cross_area: {summary['cross_area']}")

    assert summary["overall"]["total"] == 8
    assert summary["overall"]["error_count"] == 1
    assert summary["overall"]["language_issue_count"] == 1
    assert summary["overall"]["success_rate"] == round(5 / 8, 4)
    assert "avg_composite_score" in summary["overall"]
    assert "composite_success_rate" in summary["overall"]
    assert "avg_reasoning_score" in summary["overall"]
    assert "avg_evidence_score" in summary["overall"]
    assert "shibuya" in summary["by_area"]
    assert "shinjuku" in summary["by_area"]
    assert "ikebukuro" in summary["by_area"]
    assert "cross_area" in summary["by_area"]
    assert 1 in summary["by_level"]
    assert 2 in summary["by_level"]
    assert 3 in summary["by_level"]
    assert "avg_composite_score" in summary["by_level"][1]
    assert "avg_composite_score" in summary["by_area"]["shibuya"]
    assert summary["area_detection"]["total"] == 6  # results with target_area != None
    assert summary["cross_area"]["count"] == 2
    print("  OK")

    # ------------------------------------------------------------------
    # 4. compare_systems テスト (ダミーデータ)
    # ------------------------------------------------------------------
    print("\n[4] compare_systems テスト")

    # system_b: slightly different results
    dummy_results_b = [
        MultiAreaEvalResult(
            test_id="MA-SBY-L1-01",
            system_name="system_b",
            target_area="shibuya",
            query_type="single_area",
            subcategory="basic_location",
            level=1,
            answer="渋谷エリアのスポット情報",
            time_sec=2.0,
            keyword_hit_rate=0.4,
            success=False,
            area_detected="shibuya",
            area_detection_correct=True,
        ),
        MultiAreaEvalResult(
            test_id="MA-SJK-L1-01",
            system_name="system_b",
            target_area="shinjuku",
            query_type="single_area",
            subcategory="basic_location",
            level=1,
            answer="新宿駅周辺の店舗情報",
            time_sec=1.5,
            keyword_hit_rate=0.9,
            success=True,
            area_detected="shinjuku",
            area_detection_correct=True,
        ),
        MultiAreaEvalResult(
            test_id="MA-CROSS-L2-01",
            system_name="system_b",
            target_area=None,
            query_type="cross_area",
            subcategory="comparison",
            level=2,
            answer="比較結果です",
            time_sec=3.0,
            keyword_hit_rate=0.5,
            success=True,
            area_detected=None,
            area_detection_correct=True,
        ),
    ]

    comparison = evaluator.compare_systems({
        "system_a": dummy_results,
        "system_b": dummy_results_b,
    })

    print(f"  rankings: {comparison['rankings']}")
    print(f"  area_consistency: {comparison['area_consistency']}")
    assert len(comparison["summaries"]) == 2
    assert len(comparison["rankings"]) == 2
    # system_a has 5/8 = 0.625, system_b has 2/3 ~ 0.6667
    assert comparison["rankings"][0][0] == "system_b", \
        f"Expected system_b first, got {comparison['rankings'][0][0]}"
    assert "system_a" in comparison["area_consistency"]
    assert "system_b" in comparison["area_consistency"]
    print("  OK")

    # ------------------------------------------------------------------
    # 5. evaluate_single_case テスト (ダミー system_fn)
    # ------------------------------------------------------------------
    print("\n[5] evaluate_single_case テスト")

    @dataclass
    class _DummyTestCase:
        id: str = "MA-TEST-01"
        prompt: str = "渋谷駅周辺のカフェを教えてください"
        expected_keywords: List[str] = None
        target_area: Optional[str] = "shibuya"
        query_type: str = "single_area"
        subcategory: str = "basic_location"
        level: int = 1

        def __post_init__(self):
            if self.expected_keywords is None:
                self.expected_keywords = ["カフェ", "渋谷"]

    def dummy_system_fn(question: str) -> Dict:
        return {
            "answer": "渋谷駅近くにはスターバックスなどのカフェがあります。",
            "detected_area": "shibuya",
        }

    tc = _DummyTestCase()
    eval_result = evaluator.evaluate_single_case("dummy_system", dummy_system_fn, tc)
    print(f"  test_id: {eval_result.test_id}")
    print(f"  keyword_hit_rate: {eval_result.keyword_hit_rate}")
    print(f"  success: {eval_result.success}")
    print(f"  area_detection_correct: {eval_result.area_detection_correct}")
    print(f"  language_issue: {eval_result.language_issue}")
    print(f"  composite_score: {eval_result.composite_score}")
    print(f"  reasoning_score: {eval_result.reasoning_score}")
    assert eval_result.success is True
    assert eval_result.area_detection_correct is True
    assert eval_result.language_issue is False
    assert eval_result.composite_score >= 0
    assert eval_result.reasoning_score >= 0
    print("  OK")

    # ------------------------------------------------------------------
    # 6. to_dict テスト
    # ------------------------------------------------------------------
    print("\n[6] to_dict テスト")
    d = eval_result.to_dict()
    assert isinstance(d, dict)
    assert d["test_id"] == "MA-TEST-01"
    assert d["system_name"] == "dummy_system"
    assert "composite_score" in d
    assert "reasoning_score" in d
    assert "evidence_score" in d
    assert "has_coordinate" in d
    assert "has_poi_name" in d
    print(f"  keys: {list(d.keys())}")
    print("  OK")

    # ------------------------------------------------------------------
    # 7. エラーハンドリング テスト
    # ------------------------------------------------------------------
    print("\n[7] エラーハンドリング テスト")

    def error_system_fn(question: str) -> Dict:
        raise ValueError("テスト用エラー")

    tc_err = _DummyTestCase(id="MA-ERR-01")
    err_result = evaluator.evaluate_single_case("error_system", error_system_fn, tc_err)
    assert err_result.success is False
    assert err_result.error == "テスト用エラー"
    assert err_result.keyword_hit_rate == 0.0
    print(f"  error captured: {err_result.error}")
    print("  OK")

    # ------------------------------------------------------------------
    # 8. 多次元評価メソッド テスト
    # ------------------------------------------------------------------
    print("\n[8] 多次元評価メソッド テスト")

    test_answer_rich = (
        "渋谷駅周辺で最も近いコンビニはローソン渋谷神南店です。"
        "渋谷駅から約150mの距離にあり、徒歩で約2分です。"
        "座標は緯度35.6620、経度139.7005です。"
        "なぜなら、データを分析すると、渋谷駅から最も距離が短いコンビニだからです。"
        "ただし、営業時間の情報は確認できませんでした。"
    )

    assert evaluator._has_coordinate(test_answer_rich) is True, "_has_coordinate should detect coordinates"
    assert evaluator._has_coordinate("渋谷駅にカフェがあります") is False, "_has_coordinate should return False"

    reasoning = evaluator._evaluate_reasoning(test_answer_rich)
    assert 0 < reasoning <= 5.0, f"reasoning should be 0-5, got {reasoning}"
    print(f"  reasoning_score: {reasoning}")

    evidence = evaluator._evaluate_evidence(test_answer_rich)
    assert 0 <= evidence <= 5.0, f"evidence should be 0-5, got {evidence}"
    print(f"  evidence_score: {evidence}")

    constraint = evaluator._evaluate_constraint(test_answer_rich, ["距離200m以内"])
    assert 0 <= constraint <= 5.0, f"constraint should be 0-5, got {constraint}"
    print(f"  constraint_score: {constraint}")

    constraint_none = evaluator._evaluate_constraint(test_answer_rich, None)
    assert constraint_none == 3.0, "No constraints should return neutral 3.0"

    uncertainty = evaluator._evaluate_uncertainty(test_answer_rich)
    assert 0 <= uncertainty <= 5.0, f"uncertainty should be 0-5, got {uncertainty}"
    print(f"  uncertainty_score: {uncertainty}")

    composite = evaluator._calculate_composite(
        level=2, keyword_hits=80, keyword_total=100,
        has_coord=True, has_name=True,
        reasoning=3.0, evidence=2.5, constraint=3.0, uncertainty=2.0
    )
    assert 0 <= composite <= 100, f"composite should be 0-100, got {composite}"
    print(f"  composite_score (L2): {composite}")

    # _compute_multi_scores 一括テスト
    multi = evaluator._compute_multi_scores(test_answer_rich, level=2, keyword_hit_rate=0.8)
    assert "composite_score" in multi
    assert "reasoning_score" in multi
    print(f"  _compute_multi_scores: composite={multi['composite_score']}")
    print("  OK")

    # ------------------------------------------------------------------
    # 9. recalculate_scores テスト
    # ------------------------------------------------------------------
    print("\n[9] recalculate_scores テスト")

    # ダミーテストケース（constraintsあり）
    @dataclass
    class _DummyTestCaseWithConstraints:
        id: str = "MA-TEST-RC-01"
        prompt: str = "渋谷駅周辺の24時間営業のコンビニ"
        expected_keywords: List[str] = None
        target_area: Optional[str] = "shibuya"
        query_type: str = "single_area"
        subcategory: str = "constraint_single"
        level: int = 3
        constraints: Optional[List[str]] = None

        def __post_init__(self):
            if self.expected_keywords is None:
                self.expected_keywords = ["コンビニ", "24時間"]
            if self.constraints is None:
                self.constraints = ["24時間営業"]

    tc_rc = _DummyTestCaseWithConstraints()
    old_result = MultiAreaEvalResult(
        test_id="MA-TEST-RC-01",
        system_name="test_sys",
        target_area="shibuya",
        query_type="single_area",
        subcategory="constraint_single",
        level=3,
        answer="渋谷駅の近くにセブンイレブンがあり、24時間営業です。約100mの距離です。",
        time_sec=2.0,
        keyword_hit_rate=1.0,
        success=True,
        area_detected="shibuya",
        area_detection_correct=True,
    )

    recalculated = evaluator.recalculate_scores([old_result], [tc_rc])
    assert len(recalculated) == 1
    r = recalculated[0]
    assert r.composite_score > 0, f"recalculated composite should be >0, got {r.composite_score}"
    assert r.constraint_score > 0, f"recalculated constraint should be >0, got {r.constraint_score}"
    assert r.test_id == "MA-TEST-RC-01"
    assert r.keyword_hit_rate == 1.0  # 元の値が保持されていること
    print(f"  recalculated composite_score: {r.composite_score}")
    print(f"  recalculated constraint_score: {r.constraint_score}")
    print("  OK")

    print("\n" + "=" * 60)
    print("全セルフテスト完了")
