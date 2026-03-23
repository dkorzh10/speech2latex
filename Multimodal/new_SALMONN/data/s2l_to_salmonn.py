import io
import os
import csv
import json

import datasets
from datasets import load_dataset, Audio
import torch
import torchaudio
from tqdm import tqdm


base_path = "/mnt/shared_ru.ml.SZ-2_000049/antispoofing_datasets/S2L_full_dataset/"


def _get_audio_column(ds: datasets.Dataset) -> str:
    """Return the name of the audio column (first column with Audio feature)."""
    for name, feat in ds.features.items():
        if isinstance(feat, Audio):
            return name
    raise ValueError(f"No Audio column found in dataset features: {ds.features}")


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _to_serializable(value):
    """Convert value to something that can be safely written to CSV."""
    if isinstance(value, (str, int, float)) or value is None:
        return value
    # For lists/dicts and any other complex types – store JSON string.
    try:
        return json.dumps(value, ensure_ascii=False)
    except TypeError:
        return str(value)


# splits = ["equations_test", "equations_train", "sentences_test", "sentences_train"]
# splits = ["equations_mathbridge_clean"]

splits = ["equations_test"]


if __name__ == "__main__":
    for split in splits:
        print(f"Processing split: {split}")
        ds = load_dataset("marsianin500/Speech2Latex", split=split)
        # ds = load_dataset("marsianin500/Speech2LatexMathBridge", split=split)

        audio_col = _get_audio_column(ds)

        split_dir = os.path.join(base_path, split)
        _ensure_dir(split_dir)

        csv_path = os.path.join(base_path, f"{split}.csv")
        tmp_csv_path = csv_path + ".tmp"

        # CSV will contain all non-audio columns + path to saved audio file.
        non_audio_columns = [c for c in ds.column_names if c != audio_col]
        fieldnames = non_audio_columns + ["audio_path"]

        # Use raw Arrow table to avoid datasets Audio decoder (torchcodec/FFmpeg dependency).
        table = ds.data
        audio_column = table[audio_col]
        n = len(ds)

        # Write CSV atomically (avoid leaving an empty/partial file on crashes/ENOSPC).
        try:
            with open(tmp_csv_path, "w", newline="", encoding="utf-8") as csv_f:
                writer = csv.DictWriter(csv_f, fieldnames=fieldnames)
                writer.writeheader()

                for idx in tqdm(range(n), desc=f"  {split}"):
                    audio_rel_path = None
                    try:
                        raw = audio_column[idx].as_py()
                        path, bytes_val = raw.get("path"), raw.get("bytes")
                        if bytes_val is not None:
                            waveform, sr = torchaudio.load(io.BytesIO(bytes_val))
                        else:
                            waveform, sr = torchaudio.load(path)

                        # torchaudio.save expects a 2D tensor: (channels, time).
                        # Some samples can be multi-channel; normalize to mono (1, T).
                        if waveform.dim() == 1:
                            waveform = waveform.unsqueeze(0)
                        elif waveform.dim() != 2:
                            raise RuntimeError(f"Unexpected waveform shape: {tuple(waveform.shape)}")

                        if waveform.size(0) > 1:
                            waveform = waveform.mean(dim=0, keepdim=True)

                        sr = int(sr)
                        target_sr = 16000
                        if sr != target_sr:
                            waveform = torchaudio.functional.resample(
                                waveform, orig_freq=sr, new_freq=target_sr
                            )
                            sr = target_sr

                        filename = f"{split}_{idx:06d}.wav"
                        audio_rel_path = os.path.join(split, filename)
                        audio_abs_path = os.path.join(base_path, audio_rel_path)
                        _ensure_dir(os.path.dirname(audio_abs_path))
                        torchaudio.save(audio_abs_path, waveform, sr)
                    except Exception as e:
                        print(f"Warning: failed audio idx={idx} split={split}: {e}")
                        continue

                    row = {}
                    for col in non_audio_columns:
                        val = table[col][idx]
                        row[col] = _to_serializable(val.as_py() if hasattr(val, "as_py") else val)
                    if audio_rel_path is not None:
                        row["audio_path"] = audio_rel_path
                        writer.writerow(row)

            os.replace(tmp_csv_path, csv_path)
        finally:
            # Best-effort cleanup if something failed before os.replace
            try:
                if os.path.exists(tmp_csv_path):
                    os.remove(tmp_csv_path)
            except OSError:
                pass

        print(f"Saved {len(ds)} examples for split {split} to:")
        print(f"  audio dir: {split_dir}")
        print(f"  metadata : {csv_path}")
