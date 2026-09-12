# FOSS4G 2026 Phase 2 追試パッケージ — RAG Architectures for Geographic POI QA

[FOSS4G 2026 Hiroshima Academic Track](https://2026.foss4g.org/) 採録論文
*A Systematic Comparison of RAG Architectures for Geographic POI Question Answering
Using OpenStreetMap Data* のうち、**Phase 2（4エリア・130件・4方式比較）** を
第三者が追試できるように、著者個人が公開する再現パッケージです。

- 論文DOI: https://doi.org/10.5194/isprs-archives-L-4-W1-2026-219-2026
- 出版情報: ISPRS Archives, Vol. L-4/W1-2026, pp. 219–226
- 著者: Noboru Otsuka（Geolonia Inc.）

> このリポジトリは論文の完全な研究成果一式（論文本文、統計検定、全Phaseの実験コード等）
> を含む正式なリポジトリではありません。FOSS4G発表を聞いた方が最短経路でPhase 2を
> 追試できるよう、必要なコード・データ・評価スクリプトのみを抜粋した個人発の派生物です。

## Phase 2 とは

渋谷・新宿・池袋・東京駅の4エリア（合計約3,600 OSM POI）に対し、130件のテストケースで
Structured(Hybrid) RAG・GraphRAG・Adaptive RAG・Agentic RAG の4方式を比較する多エリア
汎化評価です。論文中ではHybrid RAGが複合品質67.1/100でレベル別安定性も最良という結果でした。

## リポジトリ構成

```
├── notebooks/phase2_multi_area_evaluation.ipynb  # Google Colab評価ノートブック（本体）
├── src/            # 4方式のRAG実装 + 空間計算・グラフ構築などの依存モジュール
├── eval/           # 130件のテストケース定義とスコアリングロジック
├── data/           # 実験に使用したOSM POIデータ（4エリア、ODbLライセンス）
├── results/        # 論文Phase 2の評価結果JSON（追試結果と比較するためのベースライン）
├── questions.json / questions.md  # 130件の質問リスト（コードを読まなくても内容が分かる形式）
├── scripts/export_questions.py    # questions.{json,md} を eval/ の定義から再生成するスクリプト
└── tests/test_smoke.py            # GPU不要な範囲の動作確認テスト
```

## 実行環境

- **Google Colab（GPU必須）**: `notebooks/phase2_multi_area_evaluation.ipynb` を実行するには
  `Qwen/Qwen2.5-7B-Instruct` の4bit量子化推論と `intfloat/multilingual-e5-base` 埋め込みモデルの
  ロードが必要です。T4でも動作しますが、A100を推奨します。
- **ローカルCPU環境**: LLM推論を伴うセルは実行できません。データ読み込み・空間情報付与・
  テストケース読み込み・評価関数の疎通確認など、GPU不要な範囲は `tests/test_smoke.py` で
  検証済みです（後述）。

## 追試手順（Google Colab）

1. このリポジトリをGoogle Driveにアップロードするか、Colab上で `git clone` してください。
2. `notebooks/phase2_multi_area_evaluation.ipynb` をGoogle Colab（GPUランタイム）で開きます。
3. 冒頭の環境チェックセルで `PROJECT_PATH` をリポジトリの配置先に合わせて変更してください。
4. 上から順にセルを実行します。「10. Full Test実行」は130件×4システムで数時間かかります。
   `run_full_test = False` にすると13件のQuick Testのみ実行できます。
5. 生成される `results/phase9b_evaluation_<timestamp>.json` を、本リポジトリ同梱の
   `results/phase9b_evaluation_20260218_234531.json`（論文Phase 2の元データ）と比較してください。

## ローカルでの動作確認（GPU不要）

```bash
uv sync   # または pip install -e .
uv run pytest tests/test_smoke.py -v
```

以下を検証します（GPUなしのローカル環境で全てPASS確認済み）:

- 4エリア分のPOI JSON（計3,567件）が正しくparse・結合できる
- `geo_utils.enrich_all_areas` による空間情報付与（駅からの距離等）
- 130件のテストケースが重複なく読み込める
- `GraphRAGSystem`（LLM不要なグラフベースRAG）が実際のクエリに応答できる
- `MultiAreaEvaluator` がダミーの回答関数で最後まで動作する

質問リストのみ再生成したい場合:

```bash
uv run python scripts/export_questions.py
```

## データライセンス

POIデータは [OpenStreetMap](https://www.openstreetmap.org/copyright) の
[Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/) の下で提供されています。
© OpenStreetMap contributors。データはOverpass APIで取得したものです。

## ライセンス

- **コード**: [MIT License](LICENSE)（元はGeolonia Inc.が開発したコードで、MITライセンスの
  著作権表示を継承しています）
- **論文**: ISPRS Archives から [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) の下で公開
- **POIデータ**: 上記「データライセンス」を参照（ODbL）

## 引用方法

```bibtex
@article{otsuka2026ragcomparison,
  author  = {Otsuka, Noboru},
  title   = {A Systematic Comparison of RAG Architectures for Geographic POI Question Answering Using OpenStreetMap Data},
  journal = {The International Archives of the Photogrammetry, Remote Sensing and Spatial Information Sciences},
  volume  = {L-4/W1-2026},
  pages   = {219--226},
  year    = {2026},
  doi     = {10.5194/isprs-archives-L-4-W1-2026-219-2026},
  url     = {https://doi.org/10.5194/isprs-archives-L-4-W1-2026-219-2026}
}
```

## 既知の制限事項

- 評価は東京都心の高密度4地区（渋谷・新宿・池袋・東京駅）に限定されています。
- Phase 2のHybrid/Graph/Adaptive RAG間の差は補正後で統計的有意差なし
  （より大規模な評価での再検証が今後の課題）。
- スコアリングはルールベース（正規表現・キーワードマッチング）による決定的評価です。
- 全実験で7Bパラメータ・4bit量子化LLMを使用しています。
