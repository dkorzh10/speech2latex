# Speech-to-LaTeX

[![Paper](https://img.shields.io/badge/arXiv-2508.03542-b31b1b.svg)](https://arxiv.org/abs/2508.03542)
[![Project page](https://img.shields.io/badge/Project%20Page-GitHub%20Pages-0969da.svg)](https://mrsndmn.github.io/speech2latex/)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/dkorzh10/speech2latex/blob/main/demo_speech2latex.ipynb)

Converting spoken mathematical expressions into LaTeX: models, datasets, and benchmarks for **S2L-equations** and **S2L-sentences** in English and Russian.

**Paper:** [Speech-to-LaTeX: New Models and Datasets for Converting Spoken Equations and Sentences](https://arxiv.org/abs/2508.03542) (arXiv:2508.03542)

**Project page (demos & samples):** [GitHub Pages](https://mrsndmn.github.io/speech2latex/) — enable in repo **Settings → Pages → Source: Deploy from branch → Branch: main (or master) → /docs**.

**Colab demo:** [Open in Colab](https://colab.research.google.com/github/dkorzh10/speech2latex/blob/main/demo_speech2latex.ipynb) — run ASR post-correction in the browser; choose a model, play repo samples (no dataset download), or record/upload your own audio.

---

## Main contributions

- **First large-scale open-source S2L dataset** — [Hugging Face: marsianin500/Speech2Latex](https://huggingface.co/datasets/marsianin500/Speech2Latex): spoken mathematical expressions and sentences (**S2L-sentences**, **S2L-equations**) in English and Russian; 66k human and 571k synthetic audio samples with diverse pronunciations and complexities.
- **Multiple S2L methods** — ASR post-correction, few-shot prompting, and audio-LLM integration; strong performance and improvement over MathSpeech on several tasks.
- **Reproducible evaluation** — Baselines, metrics, and analysis for future S2L research. Code: [github.com/dkorzh10/speech2latex](https://github.com/dkorzh10/speech2latex).

---

## Repository structure

| Path | Description |
|------|-------------|
| `ProcessLaTeXFormulaTools/` | LaTeX formula normalization |
| `ASRPostCorrection/` | ASR post-correction training and evaluation |
| `Multimodal/` | Gemma and SALMONN for Speech2LaTeX |
| `sample_datasets/` | Sample audio (equations & sentences, train/test) |

---

## ProcessLaTeXFormulaTools

LaTeX normalization in `ProcessLaTeXFormulaTools/process_formula/normalize_formulas.py`:

```python
from ProcessLaTeXFormulaTools.process_formula import NormalizeFormula

norm = NormalizeFormula(check_node=False)
print(norm(" \sum_i^n i "))  # ['\\sum_{i}^{n}i']
```

**Install:** `pip install -r ProcessLaTeXFormulaTools/requirements.txt` (from `ProcessLaTeXFormulaTools/`).

---

## Gemma for Speech2LaTeX

```shell
conda env create -f envs/multimodal/gemma_env.yml
conda activate gemma_s2l
```

If needed (PyTorch):

```shell
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
```

In `Multimodal/Gemma`: create `train.csv` and `test.csv` with `audio_path` and `formula_normalized`, then:

```shell
python gemma_ft.py
python gemma_inf.py
```

Multi-GPU: `torchrun --nproc_per_node="3" gemma_ft.py`

---

## SALMONN for Speech2LaTeX

```shell
conda env create -f envs/multimodal/salmonn_env.yml
conda activate salmonn_s2l
```

In `Multimodal/Salmonn/SALMONN`: download checkpoints (see `configs/config.yaml`), create CSV with `audio_path` and `formula_normalized`, then:

```shell
python convert_csv_to_json_annot.py
python train.py --cfg-path configs/config.yaml
```

Inference:

```shell
python inference.py --cfg-path "./configs/decode_config.yaml" --test_table "test.csv"
```

---

## ASRPostCorrection

**Training:**

```shell
cd ASRPostCorrection
PYTHONPATH=. python train_qwen.py --config ./config-qwen2.5-in_context_training.json --train_df ../Data/latex_in_context_tts/latex_in_context_tts_v2_train.csv --val_df ../Data/latex_in_context_tts/latex_in_context_tts_v2_test.csv
```

**Testing:**

```shell
python test_qwen.py --cuda 0 --test_file_csv ../Data/latex_in_context_tts/latex_in_context_tts_v2_test.csv --batch_size 20 --ckpt ./ckpts/tts-in-context/version_9/
```

**Evaluation:**

```python
from s2l.eval import LatexInContextMetrics
in_context_metrics = LatexInContextMetrics()
metrics_values = in_context_metrics.compute_all(outputs['latex_pred'], outputs['latex_true'])
in_context_metrics.dump(metrics_values)
```

CLI: `python src/s2l/eval.py --csv-data <path> --pred-column model_prediction --target-column target_text`

### Demo results for project page

Run the Qwen checkpoint on repo sample audio and save JSON for the [project page](https://mrsndmn.github.io/speech2latex/) demo:

```shell
cd ASRPostCorrection
PYTHONPATH=. python run_qwen_demo.py --ckpt /path/to/checkpoint --output ../docs/demo_results.json
```

Without `--samples_csv`: the script loads HuggingFace `marsianin500/Speech2Latex`, matches samples to `sample_datasets/`, runs Whisper on local wavs, then Qwen. With `--samples_csv`: use a CSV with columns `split`, `sample_id`, `whisper_transcription`, `reference_latex`. Commit `docs/demo_results.json` so the project page can show reference vs predicted LaTeX per sample.

### Upload checkpoints to Hugging Face

Upload selected ckpts to [marsianin500](https://huggingface.co/marsianin500) for the Colab demo:

```shell
cd ASRPostCorrection
pip install huggingface_hub
huggingface-cli login
python upload_ckpts_to_hf.py [--ckpts_dir ./ckpts] [--dry_run]
```

See `upload_ckpts_to_hf.py` for the list of models (0.5B, 1.5B, math-1.5B, 7B LoRA). Repo IDs: `marsianin500/<base>-<variant>`.

### ASR post-correction models on Hugging Face

Pre-trained checkpoints (use in Colab demo or load with `transformers`):

| Model | Hugging Face |
|-------|--------------|
| Qwen2.5-0.5B (equations, multilingual mix) | [marsianin500/Qwen2.5-0.5B-instruct-equations_multilingual_mix](https://huggingface.co/marsianin500/Qwen2.5-0.5B-instruct-equations_multilingual_mix) |
| Qwen2.5-0.5B (equations, multilingual mix full) | [marsianin500/Qwen2.5-0.5B-instruct-equations_multilingual_mix_full](https://huggingface.co/marsianin500/Qwen2.5-0.5B-instruct-equations_multilingual_mix_full) |
| Qwen2.5-0.5B (sentences, eng mix) | [marsianin500/Qwen2.5-0.5B-instruct-sentences_eng_mix](https://huggingface.co/marsianin500/Qwen2.5-0.5B-instruct-sentences_eng_mix) |
| Qwen2.5-1.5B (equations, multilingual mix) | [marsianin500/Qwen2.5-1.5B-instruct-equations_multilingual_mix](https://huggingface.co/marsianin500/Qwen2.5-1.5B-instruct-equations_multilingual_mix) |
| Qwen2.5-math-1.5B (equations, multilingual mix full) | [marsianin500/Qwen2.5-math-1.5B-instruct-equations_multilingual_mix_full](https://huggingface.co/marsianin500/Qwen2.5-math-1.5B-instruct-equations_multilingual_mix_full) |
| Qwen2.5-math-1.5B (equations, multilingual mix) | [marsianin500/Qwen2.5-math-1.5B-instruct-equations_multilingual_mix](https://huggingface.co/marsianin500/Qwen2.5-math-1.5B-instruct-equations_multilingual_mix) |
| Qwen2.5-math-1.5B (sentences, eng mix) | [marsianin500/Qwen2.5-math-1.5B-instruct-sentences_eng_mix](https://huggingface.co/marsianin500/Qwen2.5-math-1.5B-instruct-sentences_eng_mix) |
| Qwen2.5-7B LoRA (equations, multilingual mix) | [marsianin500/Qwen2.5-7B-instruct-r16a64-equations_multilingual_mix](https://huggingface.co/marsianin500/Qwen2.5-7B-instruct-r16a64-equations_multilingual_mix) |
| Qwen2.5-7B LoRA (equations, multilingual mix full) | [marsianin500/Qwen2.5-7B-instruct-r16a64-equations_multilingual_mix_full](https://huggingface.co/marsianin500/Qwen2.5-7B-instruct-r16a64-equations_multilingual_mix_full) |

---

## Pronunciation generation (xTTS v2)

```shell
conda env create -f envs/tts/tts_env.yml
conda activate tts_s2l
```

Create CSV/JSONL with `id`, `pronunciation`, `language`. Set `path` and `output_dir` in `EngTTS/tts.py`, then:

```shell
python EngTTS/tts.py
```

---

## Citation

```bibtex
@inproceedings{
korzh2026speechtolatex,
title={Speech-to-LaTeX: New Models and Datasets for Converting Spoken Equations and Sentences},
author={Dmitrii Korzh and Dmitrii Tarasov and Artyom Iudin and Elvir Karimov and Matvey Skripkin and Nikita Kuzmin and Andrey Kuznetsov and Oleg Rogov and Ivan Oseledets},
booktitle={The Fourteenth International Conference on Learning Representations},
year={2026},
url={https://openreview.net/forum?id=gk8WMxzIQP}
}
```
