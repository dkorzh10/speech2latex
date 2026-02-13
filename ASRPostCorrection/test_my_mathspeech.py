from __future__ import annotations

import argparse
import json
import os
from typing import List

import pandas as pd
import torch
from tqdm.auto import tqdm
from transformers import T5ForConditionalGeneration, T5Tokenizer

from s2l.eval import LatexInContextMetrics


# Keep defaults consistent with training script
MAX_LENGTH1 = 540  # input (ASR text)
MAX_LENGTH2 = 275  # corrected text (stage 1 target and stage 2 input)
MAX_LENGTH3 = 275  # LaTeX target (stage 2 target)


class MathASRForInference(torch.nn.Module):
    def __init__(self, tokenizer, model_corrector: T5ForConditionalGeneration, model_translator: T5ForConditionalGeneration, device: torch.device):
        super().__init__()
        self.tokenizer = tokenizer
        self.model1 = model_corrector.to(device)
        self.model2 = model_translator.to(device)
        self.device = device

    @torch.no_grad()
    def translate_batch(
        self,
        asr_beam1: List[str],
        asr_beam2: List[str],
        max_length_input: int,
        max_length_correct: int,
        max_length_output: int,
        num_beams: int = 5,
    ) -> List[str]:
        assert len(asr_beam1) == len(asr_beam2)

        # 1) Build encoder inputs
        inputs_text = [f"translate ASR to truth: {b1} || {b2}" for b1, b2 in zip(asr_beam1, asr_beam2)]

        # 2) Left-pad inputs
        batch_enc = self.tokenizer(
            inputs_text,
            return_tensors="pt",
            padding="longest",
            truncation=True,
            max_length=max_length_input,
        ).to(self.device)

        # 3) Run corrector
        corrected_ids = self.model1.generate(
            **batch_enc,
            max_length=max_length_correct,
            num_beams=num_beams,
            early_stopping=True,
        )
        corrected_sentences = [
            self.tokenizer.decode(ids[1:-1], skip_special_tokens=False).strip() for ids in corrected_ids
        ]
        corrected_sentences = [c.replace("<pad>", "").replace("</s>", "") for c in corrected_sentences]

        # 4) Tokenize corrected sentences
        batch_enc2 = self.tokenizer(
            corrected_sentences,
            return_tensors="pt",
            padding="longest",
            truncation=True,
            max_length=max_length_correct,
        ).to(self.device)

        # 5) Run translator
        latex_ids = self.model2.generate(
            **batch_enc2,
            max_length=max_length_output,
            num_beams=num_beams,
            early_stopping=True,
        )
        latex_outputs = [self.tokenizer.decode(ids[1:-1], skip_special_tokens=False) for ids in latex_ids]
        latex_outputs = [c.replace("<pad>", "").replace("</s>", "") for c in latex_outputs]
        return latex_outputs


def load_from_checkpoint(
    checkpoint_path: str,
    override_tokenizer: str | None = None,
) -> tuple[MathASRForInference, dict]:
    """
    Loads tokenizer and two-stage T5 models from a training checkpoint.
    Returns (wrapped_model, saved_args_dict).
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(checkpoint_path, map_location=device)

    saved_args = ckpt.get("args", {})
    tokenizer_name = override_tokenizer or ckpt.get("tokenizer_name_or_path") or saved_args.get("tokenizer_path")
    if tokenizer_name is None:
        raise ValueError("Tokenizer path/name not found in checkpoint. Please pass --tokenizer explicitly.")

    corrector_name = saved_args.get("corrector_model", "google-t5/t5-small")
    translator_name = saved_args.get("translator_model", "google-t5/t5-small")

    tokenizer = T5Tokenizer.from_pretrained(tokenizer_name)
    tokenizer.padding_side = "left"  # generation uses left padding

    model_corrector = T5ForConditionalGeneration.from_pretrained(corrector_name)
    model_corrector.resize_token_embeddings(len(tokenizer))
    model_corrector.load_state_dict(ckpt["model1_state_dict"], strict=True)
    model_corrector.eval().to(device)

    model_translator = T5ForConditionalGeneration.from_pretrained(translator_name)
    model_translator.resize_token_embeddings(len(tokenizer))
    model_translator.load_state_dict(ckpt["model2_state_dict"], strict=True)
    model_translator.eval().to(device)

    wrapped = MathASRForInference(tokenizer, model_corrector, model_translator, device)
    return wrapped, saved_args


def main() -> None:
    parser = argparse.ArgumentParser(description="Test MathASR (two-stage T5) from a training checkpoint.")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to checkpoint.pt saved by train_my_mathspeech.py")
    parser.add_argument("--test_csv_path", type=str, required=True, help="CSV containing at least whisper_small_text and whisper_base_text")
    parser.add_argument("--out_dir", type=str, default=None, help="Directory to write predictions/metrics (defaults next to checkpoint)")
    parser.add_argument("--out_csv_name", type=str, default="test_result.csv", help="Output CSV filename")
    parser.add_argument("--tokenizer", type=str, default=None, help="Override tokenizer name/path")
    parser.add_argument("--languages", type=str, nargs="+", choices=["ru", "eng"], default=None, help="Optional: filter test by language(s)")
    parser.add_argument("--max_input_len", type=int, default=MAX_LENGTH1)
    parser.add_argument("--max_correct_len", type=int, default=MAX_LENGTH2)
    parser.add_argument("--max_latex_len", type=int, default=MAX_LENGTH3)
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--num_beams", type=int, default=5)
    args = parser.parse_args()

    # Derive output directory
    if args.out_dir is None:
        base = os.path.dirname(os.path.abspath(args.checkpoint))
        out_dir = base
    else:
        out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)

    # Load model and tokenizer
    model, saved_args = load_from_checkpoint(args.checkpoint, override_tokenizer=args.tokenizer)
    tokenizer = model.tokenizer

    # Load test CSV
    df_test = pd.read_csv(args.test_csv_path)
    for col in ["whisper_small_text", "whisper_base_text"]:
        if col not in df_test.columns:
            raise ValueError(f"Required column '{col}' not found in test CSV {args.test_csv_path}")

    # If requested, filter by languages
    if args.languages:
        if "language" in df_test.columns:
            before = len(df_test)
            df_test = df_test[df_test["language"].isin(args.languages)].reset_index(drop=True)
            after = len(df_test)
            print(f"Filtered test by languages {args.languages}: {before} -> {after}")
        else:
            print("Warning: --languages provided but test CSV lacks 'language' column; skipping language filter.")

    beam_small = df_test["whisper_small_text"].astype(str).tolist()
    beam_base = df_test["whisper_base_text"].astype(str).tolist()

    predictions: List[str] = []
    for start in tqdm(range(0, len(beam_small), args.batch_size), desc="Testing"):
        end = min(start + args.batch_size, len(beam_small))
        batch_preds = model.translate_batch(
            beam_small[start:end],
            beam_base[start:end],
            max_length_input=args.max_input_len,
            max_length_correct=args.max_correct_len,
            max_length_output=args.max_latex_len,
            num_beams=args.num_beams,
        )
        predictions.extend(batch_preds)

    # Attach predictions
    df_test["mathasr_pred_latex"] = predictions

    # Save predictions CSV
    predictions_csv_path = os.path.join(out_dir, args.out_csv_name)
    df_test.to_csv(predictions_csv_path, index=False)
    print(f"Saved test predictions to {predictions_csv_path}")

    # If target exists, compute metrics
    if "latex_normalized" in df_test.columns:
        truths = df_test["latex_normalized"].astype(str).tolist()
        predictions_no_spaces = [p.replace(' ', '') for p in predictions]
        exact = sum(1 for p, t in zip(predictions, truths) if p.strip() == t.strip())
        total = len(predictions)
        acc = exact / total if total else 0.0
        print(f"Test exact-match accuracy: {acc:.4f} ({exact}/{total})")

        metrics = LatexInContextMetrics()
        metrics_values_mix = metrics.compute_all(predictions, truths)
        print("\nIn-context metrics (mix):")
        metrics.dump(metrics_values_mix)
        metrics_base, _ = os.path.splitext(predictions_csv_path)
        with open(f"{metrics_base}_metrics_mix.json", "w") as f:
            json.dump(metrics_values_mix, f)

        # No-spaces metrics (mix)
        metrics_values_mix_nospaces = metrics.compute_all(predictions_no_spaces, truths)
        print("\nIn-context metrics without spaces (mix):")
        metrics.dump(metrics_values_mix_nospaces)
        with open(f"{metrics_base}_metrics_mix_nospaces.json", "w") as f:
            json.dump(metrics_values_mix_nospaces, f)

        # Optional splits by is_tts
        if "is_tts" in df_test.columns:
            df_artificial = df_test[df_test["is_tts"] == 1]
            df_humans = df_test[df_test["is_tts"] == 0]
            if len(df_artificial) > 0:
                preds_art = df_artificial["mathasr_pred_latex"].astype(str).tolist()
                truths_art = df_artificial["latex_normalized"].astype(str).tolist()
                metrics_values_art = metrics.compute_all(preds_art, truths_art)
                print("\nIn-context metrics (artificial):")
                metrics.dump(metrics_values_art)
                with open(f"{metrics_base}_metrics_artificial.json", "w") as f:
                    json.dump(metrics_values_art, f)
                # No-spaces (artificial)
                preds_art_nospaces = [p.replace(' ', '') for p in preds_art]
                metrics_values_art_nospaces = metrics.compute_all(preds_art_nospaces, truths_art)
                print("\nIn-context metrics without spaces (artificial):")
                metrics.dump(metrics_values_art_nospaces)
                with open(f"{metrics_base}_metrics_artificial_nospaces.json", "w") as f:
                    json.dump(metrics_values_art_nospaces, f)
            if len(df_humans) > 0:
                preds_hum = df_humans["mathasr_pred_latex"].astype(str).tolist()
                truths_hum = df_humans["latex_normalized"].astype(str).tolist()
                metrics_values_hum = metrics.compute_all(preds_hum, truths_hum)
                print("\nIn-context metrics (humans):")
                metrics.dump(metrics_values_hum)
                with open(f"{metrics_base}_metrics_humans.json", "w") as f:
                    json.dump(metrics_values_hum, f)
                # No-spaces (humans)
                preds_hum_nospaces = [p.replace(' ', '') for p in preds_hum]
                metrics_values_hum_nospaces = metrics.compute_all(preds_hum_nospaces, truths_hum)
                print("\nIn-context metrics without spaces (humans):")
                metrics.dump(metrics_values_hum_nospaces)
                with open(f"{metrics_base}_metrics_humans_nospaces.json", "w") as f:
                    json.dump(metrics_values_hum_nospaces, f)


if __name__ == "__main__":
    main()

