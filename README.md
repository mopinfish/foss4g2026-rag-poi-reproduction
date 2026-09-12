# FOSS4G 2026 Phase 2 Reproduction Package — RAG Architectures for Geographic POI QA

A personal reproduction package for **Phase 2** (4 areas, 130 cases, 4-system comparison) of the
[FOSS4G 2026 Hiroshima Academic Track](https://2026.foss4g.org/) paper
*A Systematic Comparison of RAG Architectures for Geographic POI Question Answering
Using OpenStreetMap Data*, published by the paper's author so that attendees can rerun it
themselves.

- Paper DOI: https://doi.org/10.5194/isprs-archives-L-4-W1-2026-219-2026
- Publication: ISPRS Archives, Vol. L-4/W1-2026, pp. 219–226
- Author: Noboru Otsuka (Geolonia Inc.)

> This repository is **not** the full research repository (paper source, statistical tests, code
> for every phase of the study). It is a personal derivative that extracts just enough code, data,
> and evaluation scripts for FOSS4G attendees to reproduce Phase 2 as quickly as possible.

## What is Phase 2?

A multi-area generalization evaluation across four areas near Shibuya, Shinjuku, Ikebukuro, and
Tokyo Station (about 3,600 OSM POIs in total), comparing four RAG architectures — Structured
(Hybrid), GraphRAG, Adaptive RAG, and Agentic RAG — on 130 test cases. In the paper, Hybrid RAG
achieved the best composite quality score (67.1/100) with the most stable per-level performance.

## Repository layout

```
├── notebooks/phase2_multi_area_evaluation.ipynb  # Google Colab evaluation notebook (main entry point)
├── src/            # 4 RAG system implementations + spatial calculation / graph-building dependencies
├── eval/           # Definitions and scoring logic for the 130 test cases
├── data/           # OSM POI data used in the experiment (4 areas, ODbL-licensed)
├── results/        # Phase 2 evaluation result JSON from the paper (baseline to compare your reproduction against)
├── questions.json / questions.md  # The 130-case question list, readable without opening the code
├── scripts/export_questions.py    # Regenerates questions.{json,md} from the definitions in eval/
└── tests/test_smoke.py            # GPU-free smoke tests
```

## Runtime requirements

- **Google Colab (GPU required)**: `notebooks/phase2_multi_area_evaluation.ipynb` needs 4-bit
  quantized inference with `Qwen/Qwen2.5-7B-Instruct` and the `intfloat/multilingual-e5-base`
  embedding model. It runs on a T4, but an A100 is recommended.
- **Local CPU environment**: cells that run LLM inference cannot be executed. The GPU-free parts
  (data loading, spatial enrichment, test-case loading, evaluator wiring) are verified by
  `tests/test_smoke.py` (see below).

Note: the RAG systems being evaluated answer Japanese-language questions about Tokyo POIs, so the
system prompts and the 130 test questions are in Japanese — that reflects what was actually
tested in the paper. Everything else in this repository (documentation, code comments, notebook
markdown, log output) is in English.

## Reproducing on Google Colab

1. Upload this repository to Google Drive, or `git clone` it directly inside Colab.
2. Open `notebooks/phase2_multi_area_evaluation.ipynb` in Google Colab with a GPU runtime.
3. In the environment-check cell near the top, set `PROJECT_PATH` to wherever you placed the repo.
4. Run the cells in order. "10. Run Full Test" evaluates 130 cases x 4 systems and can take
   several hours; set `run_full_test = False` to run only the 13-case quick test instead.
5. Compare the generated `results/phase9b_evaluation_<timestamp>.json` against the paper's
   original Phase 2 data, included here as `results/phase9b_evaluation_20260218_234531.json`.

## Local verification (no GPU required)

```bash
uv sync   # or: pip install -e .
uv run pytest tests/test_smoke.py -v
```

This verifies (all passing on a GPU-free local machine):

- The 4 per-area POI JSON files (3,567 records total) parse and concatenate correctly
- Spatial enrichment via `geo_utils.enrich_all_areas` (e.g. distance from each area's station)
- All 130 test cases load with no duplicate IDs
- `GraphRAGSystem` (a graph-based RAG that needs no LLM) answers a real query end to end
- `MultiAreaEvaluator` runs to completion with a dummy answer function

To regenerate the question list only:

```bash
uv run python scripts/export_questions.py
```

## Data license

The POI data is provided under the [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/)
via [OpenStreetMap](https://www.openstreetmap.org/copyright). © OpenStreetMap contributors. Data
was retrieved via the Overpass API.

## License

- **Code**: [MIT License](LICENSE) (originally developed at Geolonia Inc.; the MIT copyright
  notice is retained as required by the license)
- **Paper**: published under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) by ISPRS Archives
- **POI data**: see "Data license" above (ODbL)

## Citation

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

## Known limitations

- Evaluation is limited to four dense-urban districts in central Tokyo (Shibuya, Shinjuku,
  Ikebukuro, Tokyo Station).
- Differences between Hybrid, Graph, and Adaptive RAG in Phase 2 were not statistically
  significant after correction (larger-scale re-evaluation is future work).
- Scoring is deterministic and rule-based (regex / keyword matching).
- All experiments used a 7B-parameter, 4-bit quantized LLM.
