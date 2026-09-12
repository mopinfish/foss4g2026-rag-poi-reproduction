"""
agent_state.py - Agentic RAG用状態管理

Phase 9: LangGraphのStateGraphで使用する状態管理クラス

作成日: 2026-02-03
プロジェクト: experiments-local-llm
"""

from typing import TypedDict, Annotated, Sequence, List, Dict, Any, Optional


class AgentState(TypedDict):
    """
    Agentic RAGシステムの状態を管理するクラス

    LangGraphのStateGraphで使用される状態定義
    """
    # メッセージ履歴（エージェントとのやり取り）
    messages: List[Dict[str, str]]

    # 質問（ユーザーからの入力）
    question: str

    # 中間思考プロセス
    intermediate_steps: List[Dict[str, Any]]

    # ツール実行結果
    tool_results: List[Dict[str, Any]]

    # 最終回答
    answer: Optional[str]

    # ループカウンタ（無限ループ防止）
    iteration: int

    # 次のアクション（"continue", "finish"）
    next_action: str

    # エラー情報
    error: Optional[str]


class PlanningState(TypedDict):
    """
    プランニングフェーズの状態

    エージェントが最初に質問を分析し、実行計画を立てる際の状態
    """
    # 質問
    question: str

    # 質問分析結果
    analysis: Dict[str, Any]

    # 実行計画
    plan: List[str]

    # 必要なツールリスト
    required_tools: List[str]


class ExecutionState(TypedDict):
    """
    実行フェーズの状態

    プランに基づいてツールを実行する際の状態
    """
    # 現在のプラン
    plan: List[str]

    # 完了したステップ
    completed_steps: List[str]

    # 実行結果
    results: List[Dict[str, Any]]

    # 次のステップ
    current_step: Optional[str]


class ValidationState(TypedDict):
    """
    検証フェーズの状態

    実行結果を検証し、必要に応じて再実行する際の状態
    """
    # 実行結果
    results: List[Dict[str, Any]]

    # 検証結果
    validation: Dict[str, Any]

    # 再実行が必要か
    needs_retry: bool

    # 再実行プラン
    retry_plan: Optional[List[str]]


# =============================================================================
# 状態更新ヘルパー関数
# =============================================================================

def create_initial_state(question: str) -> AgentState:
    """
    初期状態を作成

    Args:
        question: ユーザーからの質問

    Returns:
        初期化されたAgentState
    """
    return AgentState(
        messages=[],
        question=question,
        intermediate_steps=[],
        tool_results=[],
        answer=None,
        iteration=0,
        next_action="continue",
        error=None
    )


def add_tool_result(
    state: AgentState,
    tool_name: str,
    tool_input: Dict[str, Any],
    tool_output: Any
) -> AgentState:
    """
    ツール実行結果を状態に追加

    Args:
        state: 現在の状態
        tool_name: ツール名
        tool_input: ツールへの入力
        tool_output: ツールからの出力

    Returns:
        更新された状態
    """
    state["tool_results"].append({
        "tool": tool_name,
        "input": tool_input,
        "output": tool_output
    })
    return state


def add_intermediate_step(
    state: AgentState,
    step_type: str,
    content: Any
) -> AgentState:
    """
    中間ステップを状態に追加

    Args:
        state: 現在の状態
        step_type: ステップのタイプ（"thought", "action", "observation"等）
        content: ステップの内容

    Returns:
        更新された状態
    """
    state["intermediate_steps"].append({
        "type": step_type,
        "content": content,
        "iteration": state["iteration"]
    })
    return state


def increment_iteration(state: AgentState) -> AgentState:
    """
    イテレーションをインクリメント

    Args:
        state: 現在の状態

    Returns:
        更新された状態
    """
    state["iteration"] += 1
    return state


def set_final_answer(state: AgentState, answer: str) -> AgentState:
    """
    最終回答を設定

    Args:
        state: 現在の状態
        answer: 最終回答

    Returns:
        更新された状態
    """
    state["answer"] = answer
    state["next_action"] = "finish"
    return state


def set_error(state: AgentState, error: str) -> AgentState:
    """
    エラー情報を設定

    Args:
        state: 現在の状態
        error: エラーメッセージ

    Returns:
        更新された状態
    """
    state["error"] = error
    state["next_action"] = "finish"
    return state


def should_continue(state: AgentState, max_iterations: int = 10) -> bool:
    """
    エージェントが継続すべきか判定

    Args:
        state: 現在の状態
        max_iterations: 最大イテレーション数

    Returns:
        継続すべきならTrue
    """
    if state["next_action"] == "finish":
        return False
    if state["iteration"] >= max_iterations:
        return False
    if state["error"] is not None:
        return False
    return True


# =============================================================================
# 状態サマリー関数
# =============================================================================

def get_state_summary(state: AgentState) -> str:
    """
    状態のサマリーを文字列で取得（デバッグ用）

    Args:
        state: 現在の状態

    Returns:
        サマリー文字列
    """
    lines = []
    lines.append("=" * 60)
    lines.append("Agent State Summary")
    lines.append("=" * 60)
    lines.append(f"Question: {state['question']}")
    lines.append(f"Iteration: {state['iteration']}")
    lines.append(f"Next Action: {state['next_action']}")

    if state["tool_results"]:
        lines.append(f"\nTool Results ({len(state['tool_results'])}):")
        for i, result in enumerate(state["tool_results"], 1):
            lines.append(f"  {i}. {result['tool']}")

    if state["intermediate_steps"]:
        lines.append(f"\nIntermediate Steps ({len(state['intermediate_steps'])}):")
        for step in state["intermediate_steps"][-5:]:  # 直近5件
            lines.append(f"  - [{step['type']}] {str(step['content'])[:50]}...")

    if state["answer"]:
        lines.append(f"\nAnswer: {state['answer'][:100]}...")

    if state["error"]:
        lines.append(f"\nError: {state['error']}")

    lines.append("=" * 60)
    return "\n".join(lines)


def get_tool_results_summary(state: AgentState) -> str:
    """
    ツール実行結果のサマリーを取得

    Args:
        state: 現在の状態

    Returns:
        ツール実行結果のサマリー文字列
    """
    if not state["tool_results"]:
        return "ツール実行結果なし"

    lines = ["ツール実行結果:"]
    for i, result in enumerate(state["tool_results"], 1):
        lines.append(f"{i}. {result['tool']}")
        # 出力の一部を表示
        output_str = str(result['output'])[:200]
        lines.append(f"   出力: {output_str}...")

    return "\n".join(lines)


# =============================================================================
# テスト・デバッグ用
# =============================================================================

def test_agent_state():
    """状態管理のテスト"""
    print("=" * 60)
    print("agent_state.py 動作確認")
    print("=" * 60)

    # 初期状態作成
    state = create_initial_state("渋谷駅から最も近いカフェは？")
    print("\n初期状態:")
    print(get_state_summary(state))

    # ツール実行結果を追加
    state = add_tool_result(
        state,
        tool_name="tool_get_nearest_pois",
        tool_input={"category": "カフェ", "top_n": 3},
        tool_output='{"pois": [...], "count": 3}'
    )

    # 中間ステップを追加
    state = add_intermediate_step(
        state,
        step_type="thought",
        content="最寄りのカフェを検索するツールを使う"
    )

    # イテレーションをインクリメント
    state = increment_iteration(state)

    print("\n更新後の状態:")
    print(get_state_summary(state))

    # 最終回答を設定
    state = set_final_answer(state, "最も近いカフェはスターバックス渋谷マークシティ店です（約150m）")

    print("\n最終状態:")
    print(get_state_summary(state))

    print("\n✅ agent_state.py 動作確認完了")


if __name__ == "__main__":
    test_agent_state()
