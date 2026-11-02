# Speech2LaTeX

Use Python 3.11 and the project-local `.venv` via uv; install each component's dependencies separately.

## Usage arms

- ASR training/evaluation: `ASRPostCorrection/`; requirements in `ASRPostCorrection/requirements.txt`.
- Speech baselines: `MathSpeech/`; requirements in `MathSpeech/requirements.txt`.
- Audio model training/inference: `Multimodal/`; model-specific requirements.
- LaTeX normalization: `ProcessLaTeXFormulaTools/process_formula/normalize_formulas.py`.
- Metrics: `src/s2l/eval.py`; use `PYTHONPATH=src`.
- Notebook demo: `demo_speech2latex.ipynb`.
- Project page: `docs/index.html`; selection in `docs/demo_showcase.json`; browser/provenance tests in `tests/test_demo_showcase.py`.
- Equation demo generation: `ASRPostCorrection/run_qwen_demo.py`; snapshot in `docs/demo_results.json`.
- Sentence demo generation: `ASRPostCorrection/run_sentence_demo.py`; snapshot in `docs/demo_sentence_results.json`.
