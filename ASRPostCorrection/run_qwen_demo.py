"""
Run Qwen ASR post-correction on repo sample_datasets and save results to JSON
for use on the project page demo.

Usage:
  cd ASRPostCorrection
  PYTHONPATH=. python run_qwen_demo.py --ckpt /path/to/checkpoint --output ../docs/demo_results.json

  With a pre-built CSV (columns: split, sample_id, whisper_transcription, reference_latex):
  PYTHONPATH=. python run_qwen_demo.py --ckpt /path/to/ckpt --output ../docs/demo_results.json --samples_csv ./sample_manifest.csv

  Without --samples_csv: loads HuggingFace marsianin500/Speech2Latex, matches first N samples
  per (is_tts, language) per split, runs Whisper on local wavs, then Qwen. Requires whisper, datasets, torchaudio.
"""
import argparse
import json
import os
import sys
from collections import defaultdict

import pandas as pd
import torch
from tqdm.auto import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

from dataset import ASRDataset, get_collate_function, get_dataloader
from test_qwen import batched_model_generation

# Sample files per split (same order as project page)
SAMPLE_IDS = {
    "equations_test": [
        "human_eng_00", "human_eng_01", "human_eng_02", "human_eng_03",
        "human_ru_00", "human_ru_01", "human_ru_02", "human_ru_03",
        "tts_eng_00", "tts_eng_01", "tts_eng_02", "tts_eng_03",
        "tts_ru_00", "tts_ru_01", "tts_ru_02", "tts_ru_03",
    ],
    "equations_train": [
        "human_eng_00", "human_eng_01", "human_eng_02", "human_eng_03",
        "human_ru_00", "human_ru_01", "human_ru_02", "human_ru_03",
        "tts_eng_00", "tts_eng_01", "tts_eng_02", "tts_eng_03",
        "tts_ru_00", "tts_ru_01", "tts_ru_02", "tts_ru_03",
    ],
    "sentences_test": [
        "human_eng_00", "human_eng_01", "human_eng_02", "human_eng_03",
        "tts_eng_00", "tts_eng_01", "tts_eng_02", "tts_eng_03",
    ],
    "sentences_train": [
        "human_eng_00", "human_eng_01", "human_eng_02", "human_eng_03",
        "tts_eng_00", "tts_eng_01", "tts_eng_02", "tts_eng_03",
    ],
}


def _ensure_latex_with_dollars(s: str, is_equation: bool) -> str:
    s = (s or "").strip()
    if not s:
        return s
    if is_equation and not s.startswith("$"):
        s = "$" + s
    if is_equation and not s.endswith("$"):
        s = s + "$"
    return s


def _manifest_cache_path(samples_dir: str, dataset_name: str) -> str:
    """Default cache path for build_manifest_from_hf (parent of samples_dir, dataset in filename)."""
    safe_name = dataset_name.replace("/", "_")
    return os.path.join(os.path.dirname(samples_dir), f".demo_manifest_cache_{safe_name}.csv")


def build_manifest_from_hf(samples_dir: str, dataset_name: str = "marsianin500/Speech2Latex", cache_path: str | None = None, use_cache: bool = True) -> pd.DataFrame:
    """Load HF dataset per split, match samples by (is_tts, language) order, run Whisper on local wavs. Uses CSV cache if present."""
    if cache_path is None:
        cache_path = _manifest_cache_path(samples_dir, dataset_name)
    if use_cache and os.path.isfile(cache_path):
        print(f"Loading manifest from cache: {cache_path}")
        return pd.read_csv(cache_path)

    import torchaudio
    import datasets
    import whisper

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("device", device)
    whisper_model = whisper.load_model("base", device=device)

    rows = []
    for split, sample_ids in tqdm(SAMPLE_IDS.items(), desc="Loading dataset"):
        ds = datasets.load_dataset(dataset_name, split=split, num_proc=16)
        # Order: (is_tts=False, eng), (False, ru), (True, eng), (True, ru) for equations;
        # (False, eng), (True, eng) for sentences
        is_equation = "equations" in split
        if is_equation:
            order_keys = [(False, "eng"), (False, "ru"), (True, "eng"), (True, "ru")]
        else:
            order_keys = [(False, "eng"), (True, "eng")]

        selected = []
        for is_tts, lang in order_keys:
            count = 4
            for i, ex in enumerate(ds):
                if ex.get("is_tts") == is_tts and ex.get("language") == lang:
                    selected.append(i)
                    count -= 1
                    if count == 0:
                        break
                if len(selected) >= len(sample_ids):
                    break
            if len(selected) >= len(sample_ids):
                break
        selected = selected[: len(sample_ids)]
        if len(selected) != len(sample_ids):
            raise ValueError(f"Split {split}: found {len(selected)} matching rows, need {len(sample_ids)}")

        for idx, sample_id in tqdm(zip(selected, sample_ids), desc="Processing samples", total=len(selected)):
            ex = ds[idx]
            ref = ex.get("sentence_normalized") or ex.get("sentence") or ""
            ref = _ensure_latex_with_dollars(ref, is_equation)

            wav_path = os.path.join(samples_dir, split, sample_id + ".wav")
            if not os.path.isfile(wav_path):
                raise FileNotFoundError(f"Sample wav not found: {wav_path}")

            audio_array, sr = torchaudio.load(wav_path)
            if sr != 16000:
                audio_array = torchaudio.functional.resample(audio_array, sr, 16000)
            audio_np = audio_array.squeeze().numpy().astype("float32")

            with torch.no_grad():
                result = whisper_model.transcribe(audio_np, language="en" if "eng" in sample_id else "ru", fp16=(device == "cuda"))
            whisper_text = (result.get("text") or "").strip()

            rows.append({
                "split": split,
                "sample_id": sample_id,
                "whisper_transcription": whisper_text,
                "reference_latex": ref,
            })
    df = pd.DataFrame(rows)
    df.to_csv(cache_path, index=False)
    print(f"Saved manifest cache: {cache_path}")
    return df


def main():
    parser = argparse.ArgumentParser(description="Run Qwen on sample_datasets and save demo JSON")
    parser.add_argument("--ckpt", type=str, required=True, help="Path to Qwen checkpoint (tokenizer + tuned-model)")
    parser.add_argument("--output", type=str, required=True, help="Output JSON path (e.g. docs/demo_results.json)")
    parser.add_argument("--samples_csv", type=str, default=None,
                        help="Optional CSV with columns: split, sample_id, whisper_transcription, reference_latex")
    parser.add_argument("--samples_dir", type=str, default=None,
                        help="Root dir containing sample_datasets/ (default: repo root = parent of ASRPostCorrection)")
    parser.add_argument("--no_cache_manifest", action="store_true",
                        help="Ignore cached manifest and rebuild from HuggingFace + Whisper")
    parser.add_argument("--cuda", type=int, default=0)
    parser.add_argument("--batch_size", type=int, default=8)
    args = parser.parse_args()

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    samples_dir = args.samples_dir or os.path.join(repo_root, "sample_datasets")
    device = f"cuda:{args.cuda}" if torch.cuda.is_available() else "cpu"

    if args.samples_csv:
        df = pd.read_csv(args.samples_csv)
        for col in ["split", "sample_id", "whisper_transcription", "reference_latex"]:
            if col not in df.columns:
                sys.exit(f"CSV must have column: {col}")
    else:
        print("Building manifest from HuggingFace + Whisper on local wavs...")
        df = build_manifest_from_hf(samples_dir, use_cache=not args.no_cache_manifest)
        print(f"Got {len(df)} samples")
    df = df.fillna({"whisper_transcription": "", "reference_latex": ""})

    torch.set_default_dtype(torch.bfloat16)
    ckpt_path = args.ckpt
    tokenizer = AutoTokenizer.from_pretrained(os.path.join(ckpt_path, "tokenizer"))

    use_flash = "cuda" in device and torch.cuda.is_available()
    if use_flash:
        try:
            model = AutoModelForCausalLM.from_pretrained(
                os.path.join(ckpt_path, "tuned-model"),
                attn_implementation="flash_attention_2",
                torch_dtype=torch.bfloat16,
            )
            model = model.to(device)
        except (ValueError, Exception):
            model = AutoModelForCausalLM.from_pretrained(
                os.path.join(ckpt_path, "tuned-model"),
                torch_dtype=torch.bfloat16,
            ).to(device)
    else:
        model = AutoModelForCausalLM.from_pretrained(
            os.path.join(ckpt_path, "tuned-model"),
            torch_dtype=torch.bfloat16,
        ).to(device)
    model.eval()

    # ASRDataset expects list-like indexing (dataset[i] = row); DataFrame[i] is column access.
    records = df.to_dict("records")
    pron_col = "whisper_transcription"
    latex_col = "reference_latex"
    dataset = ASRDataset(records, pron_column_name=pron_col, latex_column_name=latex_col)
    collate_fn = get_collate_function(tokenizer, ckpt_path, process_formulas=None, latex_column="latex", whisper_column="pron")
    loader = get_dataloader(dataset, args.batch_size, collate_fn, num_workers=0, train=False)

    predictions = []
    for batch in tqdm(loader, desc="Qwen inference"):
        out = batched_model_generation(model, tokenizer, batch, device=device)
        predictions.extend(out["predicted_text"])

    if len(predictions) != len(df):
        raise RuntimeError(f"Prediction count {len(predictions)} != dataset size {len(df)}")

    results = []
    for i in range(len(df)):
        row = df.iloc[i]
        audio_path = f"sample_datasets/{row['split']}/{row['sample_id']}.wav"
        results.append({
            "split": row["split"],
            "sample_id": row["sample_id"],
            "audio_path": audio_path,
            "reference_latex": row["reference_latex"].replace("\\\\", " "),
            "whisper_transcription": row["whisper_transcription"],
            "predicted_latex": predictions[i].replace("\\\\", " "),
        })

    out_data = {
        "checkpoint": os.path.abspath(ckpt_path),
        "results": results,
    }
    out_path = args.output
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(results)} results to {out_path}")


if __name__ == "__main__":
    main()
