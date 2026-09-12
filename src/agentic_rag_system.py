"""
agentic_rag_system.py - Agentic RAGシステム

Phase 9: LangGraphベースのエージェントRAGシステム
複雑な地理空間クエリに対してツールを駆使して回答を生成

作成日: 2026-02-03
プロジェクト: experiments-local-llm
"""

import json
import time
import re
import torch
from typing import List, Dict, Any, Optional, Literal, Union
from dataclasses import dataclass

# HuggingFace Transformers
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

# LangGraph (for state management only, not for LLM integration)
from langgraph.graph import StateGraph, END

# ローカルモジュール
try:
    from .agent_state import (
        AgentState,
        create_initial_state,
        add_tool_result,
        add_intermediate_step,
        increment_iteration,
        set_final_answer,
        set_error,
        should_continue,
        get_state_summary
    )
    from .agent_tools import (
        get_all_tools,
        set_global_pois,
        set_global_pois_multi_area
    )
    from .agent_prompts import (
        AGENT_SYSTEM_PROMPT,
        format_react_prompt,
        format_answer_generation_prompt,
        generate_tools_description
    )
    from .geo_utils import enrich_all_pois, enrich_all_areas
except ImportError:
    from agent_state import (
        AgentState,
        create_initial_state,
        add_tool_result,
        add_intermediate_step,
        increment_iteration,
        set_final_answer,
        set_error,
        should_continue,
        get_state_summary
    )
    from agent_tools import (
        get_all_tools,
        set_global_pois,
        set_global_pois_multi_area
    )
    from agent_prompts import (
        AGENT_SYSTEM_PROMPT,
        format_react_prompt,
        format_answer_generation_prompt,
        generate_tools_description
    )
    from geo_utils import enrich_all_pois, enrich_all_areas


# =============================================================================
# Agentic RAGシステム
# =============================================================================

class AgenticRAGSystem:
    """
    Agentic RAGシステム

    LangGraphを使用してエージェントループを実装し、
    複数のツールを駆使して複雑な地理空間クエリに回答する
    """

    def __init__(
        self,
        model = None,
        tokenizer = None,
        model_name: str = "Qwen/Qwen2.5-7B-Instruct",
        temperature: float = 0.0,
        max_iterations: int = 10,
        verbose: bool = True,
        load_in_4bit: bool = True
    ):
        """
        初期化

        Args:
            model: 事前ロード済みのHuggingFaceモデル（Noneの場合は自動ロード）
            tokenizer: 事前ロード済みのトークナイザー（Noneの場合は自動ロード）
            model_name: 使用するLLMモデル名
            temperature: LLMの温度パラメータ
            max_iterations: 最大イテレーション数
            verbose: デバッグ出力を有効にするか
            load_in_4bit: 4bit量子化を使用するか
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_iterations = max_iterations
        self.verbose = verbose

        # モデル・トークナイザーのロード
        if model is None or tokenizer is None:
            if self.verbose:
                print(f"Loading model {model_name}...")

            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True
            )

            if load_in_4bit:
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True
                )
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    quantization_config=bnb_config,
                    device_map="auto",
                    trust_remote_code=True
                )
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    device_map="auto",
                    trust_remote_code=True
                )
        else:
            self.model = model
            self.tokenizer = tokenizer

        # ツール取得
        self.tools = get_all_tools()

        # ツール名とツールのマッピング
        self.tool_map = {tool.name: tool for tool in self.tools}

        # グラフ構築
        self.graph = self._build_graph()

        if self.verbose:
            print(f"✓ Agentic RAG System initialized")
            print(f"  Model: {model_name}")
            print(f"  Tools: {len(self.tools)}")
            print(f"  Max Iterations: {max_iterations}")

    def _build_graph(self) -> StateGraph:
        """
        LangGraphのStateGraphを構築

        Returns:
            構築されたStateGraph
        """
        # グラフ定義
        workflow = StateGraph(AgentState)

        # ノード追加
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", self._tool_execution_node)
        workflow.add_node("finalize", self._finalize_node)

        # エントリーポイント
        workflow.set_entry_point("agent")

        # エッジ追加
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "finalize": "finalize",
                "end": END
            }
        )

        workflow.add_edge("tools", "agent")
        workflow.add_edge("finalize", END)

        # コンパイル
        return workflow.compile()

    def _generate_llm_response(self, prompt: str) -> str:
        """
        LLMレスポンスを生成

        Args:
            prompt: プロンプトテキスト

        Returns:
            生成されたテキスト
        """
        messages = [
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=self.temperature > 0,
                temperature=self.temperature if self.temperature > 0 else None,
                pad_token_id=self.tokenizer.eos_token_id
            )

        response = self.tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        return response.strip()

    def _parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """
        モデルの出力からツール呼び出しをパース

        日本語メタ言語（行動/行動入力）と英語メタ言語（Action/Action Input）の両方に対応。

        Args:
            response: モデルの出力テキスト

        Returns:
            ツール呼び出しのリスト [{"tool": "tool_name", "args": {...}}]
        """
        tool_calls = []

        # 日本語メタ言語パターン（Phase 9-B）
        # 行動: tool_name
        # 行動入力: {"arg1": "value1", ...}
        patterns = [
            r'行動:\s*(\w+)\s*\n\s*行動入力:\s*(\{[^}]+\})',
            r'Action:\s*(\w+)\s*\n\s*Action Input:\s*(\{[^}]+\})',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, response, re.MULTILINE)
            for match in matches:
                tool_name = match.group(1)
                try:
                    args_str = match.group(2)
                    args = json.loads(args_str)
                    tool_calls.append({
                        "tool": tool_name,
                        "args": args
                    })
                except json.JSONDecodeError:
                    if self.verbose:
                        print(f"Failed to parse tool arguments: {match.group(2)}")

            if tool_calls:
                break  # 最初にマッチしたパターンの結果を使用

        return tool_calls

    def _agent_node(self, state: AgentState) -> AgentState:
        """
        エージェントノード：質問を分析し、ツールを実行するか回答を生成する

        Args:
            state: 現在の状態

        Returns:
            更新された状態
        """
        if self.verbose:
            print(f"\n--- Agent Node (Iteration {state['iteration']}) ---")

        # イテレーションをインクリメント
        state = increment_iteration(state)

        # プロンプト構築（日本語ReActフォーマット）
        prompt_parts = [
            f"質問: {state['question']}\n"
        ]

        # ツール説明
        tools_desc = generate_tools_description()
        prompt_parts.append(f"\n利用可能なツール:\n{tools_desc}\n")

        # これまでのツール実行結果を追加
        if state["tool_results"]:
            prompt_parts.append("\nこれまでのツール実行結果:")
            for r in state["tool_results"]:
                prompt_parts.append(f"\nツール: {r['tool']}")
                prompt_parts.append(f"結果: {r['output']}")

        # ReAct指示（日本語メタ言語）
        prompt_parts.append("\n\n以下のフォーマットで回答してください:")
        prompt_parts.append("思考: [考えの内容]")
        prompt_parts.append("行動: [ツール名]")
        prompt_parts.append("行動入力: {\"arg1\": \"value1\", ...}")
        prompt_parts.append("\nまたは、十分な情報がある場合:")
        prompt_parts.append("思考: 十分な情報が集まったので最終回答を生成できる")
        prompt_parts.append("最終回答: [回答内容（必ず日本語で）]")

        prompt = "\n".join(prompt_parts)

        # LLM呼び出し
        try:
            response = self._generate_llm_response(prompt)

            if self.verbose:
                print(f"Agent response: {response[:300]}...")

            # ツール呼び出しをパース
            tool_calls = self._parse_tool_calls(response)

            if tool_calls:
                # ツール呼び出しを中間ステップに保存
                state = add_intermediate_step(state, "tool_calls", {
                    "tool_calls": tool_calls,
                    "response": response
                })

                if self.verbose:
                    print(f"Parsed tool calls: {[tc['tool'] for tc in tool_calls]}")
            else:
                # ツール呼び出しがない場合は最終回答を抽出（日本語/英語両対応）
                final_answer_match = (
                    re.search(r'最終回答:\s*(.+?)(?:\n|$)', response, re.DOTALL)
                    or re.search(r'Final Answer:\s*(.+?)(?:\n|$)', response, re.DOTALL)
                )
                if final_answer_match:
                    answer = final_answer_match.group(1).strip()
                    state = set_final_answer(state, answer)
                else:
                    # パースできない場合はそのままresponseを保存
                    state = add_intermediate_step(state, "response", {
                        "response": response
                    })

        except Exception as e:
            if self.verbose:
                print(f"Error in agent node: {e}")
            state = set_error(state, str(e))

        return state

    def _tool_execution_node(self, state: AgentState) -> AgentState:
        """
        ツール実行ノード：パースされたツール呼び出しを実行

        Args:
            state: 現在の状態

        Returns:
            更新された状態
        """
        if self.verbose:
            print(f"\n--- Tool Execution Node ---")

        # 最新の中間ステップからツール呼び出しを取得
        if not state["intermediate_steps"]:
            return state

        last_step = state["intermediate_steps"][-1]
        content = last_step.get("content", {})
        tool_calls = content.get("tool_calls", [])

        if not tool_calls:
            return state

        # 各ツールを実行
        for tool_call in tool_calls:
            tool_name = tool_call["tool"]
            args = tool_call["args"]

            if tool_name not in self.tool_map:
                if self.verbose:
                    print(f"Unknown tool: {tool_name}")
                continue

            tool = self.tool_map[tool_name]

            try:
                if self.verbose:
                    print(f"Executing {tool_name} with args: {args}")

                # ツール実行
                output = tool.invoke(args)

                if self.verbose:
                    print(f"Tool output: {str(output)[:200]}...")

                # 結果を保存
                state = add_tool_result(state, tool_name, args, output)

            except Exception as e:
                error_msg = f"Error executing {tool_name}: {str(e)}"
                if self.verbose:
                    print(error_msg)
                state = add_tool_result(state, tool_name, args, error_msg)

        return state

    def _should_continue(self, state: AgentState) -> Literal["continue", "finalize", "end"]:
        """
        継続判定：次にツールを実行するか、回答を生成するか、終了するか

        Args:
            state: 現在の状態

        Returns:
            次のアクション（"continue", "finalize", "end"）
        """
        # エラーがある場合は終了
        if state.get("error"):
            return "end"

        # すでに最終回答がある場合は終了
        if state.get("answer"):
            return "end"

        # 最大イテレーションに達した場合は回答生成
        if state["iteration"] >= self.max_iterations:
            if self.verbose:
                print("Max iterations reached, finalizing...")
            return "finalize"

        # 最新の中間ステップを確認
        if state["intermediate_steps"]:
            last_step = state["intermediate_steps"][-1]

            # ツール呼び出しがある場合は継続
            if last_step.get("type") == "tool_calls":
                content = last_step.get("content", {})
                if content.get("tool_calls"):
                    return "continue"

        # ツール実行結果があり、かつ新しいツール呼び出しがない場合は回答生成
        if state["tool_results"]:
            return "finalize"

        # それ以外は終了
        return "end"

    def _finalize_node(self, state: AgentState) -> AgentState:
        """
        最終ノード：ツール実行結果から最終回答を生成

        Args:
            state: 現在の状態

        Returns:
            更新された状態
        """
        if self.verbose:
            print("\n--- Finalize Node ---")

        try:
            # 回答生成プロンプト
            prompt_text = format_answer_generation_prompt(
                state["question"],
                state["tool_results"]
            )

            # LLM呼び出し
            response = self._generate_llm_response(prompt_text)

            if self.verbose:
                print(f"Final answer generated: {response[:200]}...")

            # 最終回答を設定
            state = set_final_answer(state, response)

        except Exception as e:
            if self.verbose:
                print(f"Error in finalize node: {e}")
            state = set_error(state, str(e))

        return state

    def query(self, question: str) -> Dict[str, Any]:
        """
        質問に対して回答を生成

        Args:
            question: ユーザーからの質問

        Returns:
            回答と実行情報を含む辞書
        """
        start_time = time.time()

        if self.verbose:
            print("=" * 60)
            print(f"Question: {question}")
            print("=" * 60)

        # 初期状態作成
        initial_state = create_initial_state(question)

        # グラフ実行
        try:
            final_state = self.graph.invoke(initial_state)
        except Exception as e:
            if self.verbose:
                print(f"Error during graph execution: {e}")
            return {
                "question": question,
                "answer": f"エラーが発生しました: {str(e)}",
                "error": str(e),
                "execution_time": time.time() - start_time
            }

        execution_time = time.time() - start_time

        # 結果構築
        result = {
            "question": question,
            "answer": final_state.get("answer", "回答を生成できませんでした"),
            "tool_results": final_state.get("tool_results", []),
            "iterations": final_state.get("iteration", 0),
            "execution_time": round(execution_time, 2),
            "error": final_state.get("error")
        }

        if self.verbose:
            print("=" * 60)
            print(f"Answer: {result['answer']}")
            print(f"Iterations: {result['iterations']}")
            print(f"Execution time: {result['execution_time']}s")
            print("=" * 60)

        return result

    def batch_query(self, questions: List[str]) -> List[Dict[str, Any]]:
        """
        複数の質問に対して一括で回答を生成

        Args:
            questions: 質問のリスト

        Returns:
            回答のリスト
        """
        results = []
        for i, question in enumerate(questions, 1):
            if self.verbose:
                print(f"\n[{i}/{len(questions)}] Processing question...")
            result = self.query(question)
            results.append(result)
        return results


# =============================================================================
# ヘルパー関数
# =============================================================================

def load_poi_data(
    poi_file: str = "poi_documents.json",
    areas_config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    POIデータを読み込み、空間情報を付加

    Args:
        poi_file: POIデータファイルのパス
        areas_config: エリア設定辞書（None時は渋谷単一エリア）

    Returns:
        空間情報付きPOIリスト
    """
    print(f"Loading POI data from {poi_file}...")

    with open(poi_file, "r", encoding="utf-8") as f:
        raw_pois = json.load(f)

    # メタデータをフラット化（poi_documents.json形式対応）
    flat_pois = []
    for poi in raw_pois:
        if "metadata" in poi:
            flat_poi = poi["metadata"].copy()
            flat_pois.append(flat_poi)
        else:
            flat_pois.append(poi)

    # 空間情報付加（広域対応）
    if areas_config and len(areas_config) > 1:
        pois = enrich_all_areas(flat_pois, areas_config)
        set_global_pois_multi_area(pois, areas_config)
        print(f"✓ Loaded {len(pois)} POIs with spatial info ({len(areas_config)} areas)")
    else:
        pois = enrich_all_pois(flat_pois)
        set_global_pois(pois)
        print(f"✓ Loaded {len(pois)} POIs with spatial info")

    return pois


def initialize_system(
    poi_file: str = "poi_documents.json",
    model = None,
    tokenizer = None,
    model_name: str = "Qwen/Qwen2.5-7B-Instruct",
    areas_config: Optional[Dict[str, Any]] = None,
    verbose: bool = True,
    load_in_4bit: bool = True
) -> AgenticRAGSystem:
    """
    Agentic RAGシステムを初期化

    Args:
        poi_file: POIデータファイル
        model: 事前ロード済みのHuggingFaceモデル（Noneの場合は自動ロード）
        tokenizer: 事前ロード済みのトークナイザー（Noneの場合は自動ロード）
        model_name: LLMモデル名
        areas_config: エリア設定辞書（None時は渋谷単一エリア）
        verbose: デバッグ出力
        load_in_4bit: 4bit量子化を使用するか

    Returns:
        初期化されたAgenticRAGSystem
    """
    # POIデータ読み込み（広域対応）
    load_poi_data(poi_file, areas_config=areas_config)

    # システム初期化
    system = AgenticRAGSystem(
        model=model,
        tokenizer=tokenizer,
        model_name=model_name,
        verbose=verbose,
        load_in_4bit=load_in_4bit
    )

    return system


# =============================================================================
# メイン実行
# =============================================================================

def main():
    """メイン実行"""
    print("=" * 60)
    print("Agentic RAG System - Interactive Mode")
    print("=" * 60)

    # システム初期化
    system = initialize_system()

    # インタラクティブモード
    print("\n質問を入力してください（'quit'で終了）:")

    while True:
        question = input("\n> ").strip()

        if not question:
            continue

        if question.lower() in ["quit", "exit", "q"]:
            print("終了します。")
            break

        # 質問実行
        result = system.query(question)

        # 結果表示
        print(f"\n回答: {result['answer']}")
        print(f"実行時間: {result['execution_time']}秒")


def test_system():
    """システムテスト"""
    print("=" * 60)
    print("Agentic RAG System - Test Mode")
    print("=" * 60)

    # システム初期化
    system = initialize_system(verbose=True)

    # テストケース
    test_questions = [
        "渋谷駅から最も近いカフェは？",
        "渋谷駅から500m以内にカフェは何件ありますか？",
        "カフェは東側と西側でどちらが多いですか？",
    ]

    print(f"\n{len(test_questions)}件のテストケースを実行します\n")

    results = []
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'=' * 60}")
        print(f"Test {i}/{len(test_questions)}")
        print(f"{'=' * 60}")

        result = system.query(question)
        results.append(result)

        print(f"\n回答: {result['answer']}")
        print(f"イテレーション数: {result['iterations']}")
        print(f"実行時間: {result['execution_time']}秒")

    # サマリー
    print(f"\n{'=' * 60}")
    print("Test Summary")
    print(f"{'=' * 60}")
    print(f"総質問数: {len(results)}")
    print(f"平均実行時間: {sum(r['execution_time'] for r in results) / len(results):.2f}秒")
    print(f"エラー数: {sum(1 for r in results if r.get('error'))}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_system()
    else:
        main()
