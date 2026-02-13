import argparse
import os
from typing import List, Dict

import datasets
import pandas as pd
import torch
import torchaudio
import whisper
from tqdm.auto import tqdm


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe a dataset split with Whisper and export a CSV."
    )
    parser.add_argument(
        "--dataset-path",
        type=str,
        default="marsianin500/Speech2Latex",
        help="HuggingFace dataset path or local path (default: marsianin500/Speech2Latex)",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="equations_train",
        help="Dataset split to use (default: equations_train)",
    )
    parser.add_argument(
        "--shard-index",
        type=int,
        default=None,
        help="Shard index (0-based). Use with --num-shards for dataset sharding.",
    )
    parser.add_argument(
        "--num-shards",
        type=int,
        default=None,
        help="Total number of shards. Use with --shard-index for dataset sharding.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Limit number of samples to process; use -1 for all (default: 10)",
    )
    parser.add_argument(
        "--models",
        type=str,
        nargs="+",
        default=["small", "base"],
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model sizes to run (default: small base)",
    )
    parser.add_argument(
        "--language",
        type=str,
        default="en",
        help="Language hint for Whisper (default: en)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        choices=["auto", "cpu", "cuda"],
        help='Device to use for inference (default: "auto")',
    )
    parser.add_argument(
        "--preprocess-workers",
        type=int,
        default=0,
        help="If >0, pre-resample audio to 16kHz using datasets.map with num_proc.",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help='Path to output CSV file (default: "<split>.csv")',
    )
    return parser.parse_args()


def resolve_device(user_device: str) -> str:
    if user_device == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return user_device


def load_models(model_names: List[str], device: str) -> Dict[str, "whisper.Whisper"]:
    models: Dict[str, "whisper.Whisper"] = {}
    for name in model_names:
        models[name] = whisper.load_model(name, device=device)
    return models


def main() -> None:
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context

    args = parse_args()
    device = resolve_device(args.device)

    dataset = datasets.load_dataset(args.dataset_path, split=args.split)
    # Optional limit applied after sharding
    if args.limit is not None and args.limit >= 0:
        dataset = dataset.select(range(min(args.limit, len(dataset))))

    # Optional sharding across multiple processes/machines
    if args.shard_index is not None or args.num_shards is not None:
        if args.shard_index is None or args.num_shards is None:
            raise ValueError("Both --shard-index and --num-shards must be provided for sharding.")
        if args.num_shards <= 0:
            raise ValueError("--num-shards must be > 0.")
        if not (0 <= args.shard_index < args.num_shards):
            raise ValueError("--shard-index must satisfy 0 <= shard_index < num_shards.")
        # Datasets API: shard(num_shards, index)
        dataset = dataset.shard(num_shards=args.num_shards, index=args.shard_index)


    # Optional preprocessing to resample to 16kHz in parallel
    if args.preprocess_workers and args.preprocess_workers > 0:
        def _prep(example):
            array = example["audio_path"]["array"]
            sr = example["audio_path"]["sampling_rate"]
            if sr != 16000:
                audio_tensor = torch.tensor(array, dtype=torch.float32)
                audio_tensor = torchaudio.functional.resample(audio_tensor, sr, 16000)
                example["audio_16k"] = audio_tensor.numpy()
            else:
                example["audio_16k"] = array.astype("float32")
            return example
        dataset = dataset.map(_prep, num_proc=args.preprocess_workers)

    models = load_models(args.models, device=device)

    # Prepare collectors
    collected_texts: Dict[str, List[str]] = {f"whisper_{m}_text": [] for m in args.models}
    latex: List[str] = []
    pronunciation: List[str] = []
    is_tts: List[bool] = []
    language_col: List[str] = []

    for item in tqdm(dataset, total=len(dataset)):
        # Prepare 16kHz mono float32 numpy audio for Whisper
        if args.preprocess_workers and "audio_16k" in item:
            audio_np = item["audio_16k"].astype("float32")
        else:
            sample_rate = item["audio_path"]["sampling_rate"]
            if sample_rate == 16000:
                audio_np = item["audio_path"]["array"].astype("float32")
            else:
                audio_tensor = torch.tensor(item["audio_path"]["array"], dtype=torch.float32)
                audio_tensor = torchaudio.functional.resample(audio_tensor, sample_rate, 16000)
                audio_np = audio_tensor.numpy()

        pronunciation.append(item["pronunciation"])
        latex.append(item["sentence_normalized"])
        is_tts.append(item.get("is_tts"))
        language_col.append(item.get("language"))

        # Inference (no grad)
        with torch.no_grad():
            for model_name, model in models.items():
                result = model.transcribe(audio_np, language=args.language, fp16=(device == "cuda"))
                collected_texts[f"whisper_{model_name}_text"].append(result["text"])

    data = {
        **collected_texts,
        "latex_normalized": latex,
        "pronunciation": pronunciation,
        "is_tts": is_tts,
        "language": language_col,
    }
    df = pd.DataFrame.from_dict(data)

    if args.output_file:
        output_file = args.output_file
    else:
        shard_suffix = ""
        if args.shard_index is not None and args.num_shards is not None:
            shard_suffix = f"_shard{args.shard_index}of{args.num_shards}"
        output_file = f"{args.split}{shard_suffix}_whisper_small_base_transcriptions.csv"
    df.to_csv(output_file, index=False)
    print("saved to", output_file)


if __name__ == "__main__":
    main()
