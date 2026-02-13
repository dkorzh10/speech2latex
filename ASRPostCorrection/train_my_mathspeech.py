from __future__ import annotations

import argparse
import os
import random
from typing import Dict

import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from torch.utils.tensorboard import SummaryWriter
from tqdm.auto import tqdm
from transformers import T5ForConditionalGeneration, T5Tokenizer

import random
import string
import json
from s2l.eval import LatexInContextMetrics

MAX_LENGTH1 = 540  # input (ASR text)
MAX_LENGTH2 = 275  # corrected text (stage 1 target and stage 2 input)
MAX_LENGTH3 = 275  # LaTeX target (stage 2 target)


class MathASR(torch.nn.Module):
    def __init__(self, tokenizer, model_name1, model_name2, device):
        super(MathASR, self).__init__()
        self.tokenizer = tokenizer
        self.model1 = model_name1
        self.model1.to(device)
        self.model2 = model_name2
        self.model2.to(device)
        self.device = device

    def forward(self, input_ids, attention_mask_correct, attention_mask_translate, labels_correct, labels_translate):
        input_ids = input_ids.contiguous()
        attention_mask_correct = attention_mask_correct.contiguous()
        labels_correct = labels_correct.contiguous()
        attention_mask_translate = attention_mask_translate.contiguous()
        labels_translate = labels_translate.contiguous()

        outputs1 = self.model1(input_ids=input_ids, attention_mask=attention_mask_correct, labels=labels_correct)
        loss1 = outputs1.loss
        logits1 = outputs1.logits

        intermediate_ids = torch.argmax(logits1, dim=-1).detach()

        outputs2 = self.model2(input_ids=intermediate_ids, attention_mask=attention_mask_translate, labels=labels_translate)
        loss2 = outputs2.loss

        total_loss = 0.3 * loss1 + 0.7 * loss2
        return total_loss, outputs1.logits, outputs2.logits

    @torch.no_grad()
    def translate_batch(
        self,
        asr_beam1,
        asr_beam2,
        max_length_input: int,
        max_length_correct: int,
        max_length_output: int,
        num_beams: int = 5,
    ):
        """Translate a batch of ASR hypotheses into LaTeX.

        Args:
            asr_beam1 (List[str]): first ASR hypothesis per sample.
            asr_beam2 (List[str]): second ASR hypothesis per sample.
        Returns:
            List[str]: LaTeX strings corresponding to each input sample.
        """
        assert len(asr_beam1) == len(asr_beam2)

        # 1. Build encoder input strings
        inputs_text = [
            f"translate ASR to truth: {b1} || {b2}"
            for b1, b2 in zip(asr_beam1, asr_beam2)
        ]

        # 2. Tokenise with *left* padding
        batch_enc = self.tokenizer(
            inputs_text,
            return_tensors="pt",
            padding="longest",
            truncation=True,
            max_length=max_length_input,
        ).to(self.device)

        # 3. Run error-corrector model
        corrected_ids = self.model1.generate(
            **batch_enc,
            max_length=max_length_correct,
            num_beams=num_beams,
            early_stopping=True,
        )

        corrected_sentences = [
            self.tokenizer.decode(ids[1:-1], skip_special_tokens=False).strip()
            for ids in corrected_ids
        ]

        corrected_sentences = [c.replace("<pad>", "").replace("</s>", "") for c in corrected_sentences]

        # 4. Tokenise corrected sentences
        batch_enc2 = self.tokenizer(
            corrected_sentences,
            return_tensors="pt",
            padding="longest",
            truncation=True,
            max_length=max_length_correct,
        ).to(self.device)

        # 5. Run translation model
        latex_ids = self.model2.generate(
            **batch_enc2,
            max_length=max_length_output,
            num_beams=num_beams,
            early_stopping=True,
        )

        latex_outputs = [
            self.tokenizer.decode(ids[1:-1], skip_special_tokens=False)
            for ids in latex_ids
        ]
        latex_outputs = [c.replace("<pad>", "").replace("</s>", "") for c in latex_outputs]

        return latex_outputs


class MathSpeechDataset(Dataset):
    def __init__(
        self,
        csv_path: str,
        tokenizer: T5Tokenizer,
        max_input_len: int = MAX_LENGTH1,
        max_correct_len: int = MAX_LENGTH2,
        max_latex_len: int = MAX_LENGTH3,
        is_tts_filter: list[int] | None = None,
        language_filter: list[str] | None = None,
    ) -> None:
        self.tokenizer = tokenizer
        self.max_input_len = max_input_len
        self.max_correct_len = max_correct_len
        self.max_latex_len = max_latex_len

        df = pd.read_csv(csv_path)
        # Ensure required columns exist
        for col in ["pronunciation", "whisper_small_text", "whisper_base_text", "latex_normalized"]:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' not found in {csv_path}")
        # Optional filters if corresponding columns exist
        if is_tts_filter is not None:
            if "is_tts" not in df.columns:
                raise ValueError("Requested is_tts filtering but 'is_tts' column not found in CSV")
            df = df[df["is_tts"].isin(is_tts_filter)]
        if language_filter is not None:
            if "language" not in df.columns:
                raise ValueError("Requested language filtering but 'language' column not found in CSV")
            df = df[df["language"].isin(language_filter)]
        # Drop rows with missing values in required fields
        df = df.dropna(subset=["pronunciation", "whisper_small_text", "whisper_base_text", "latex_normalized"]).reset_index(drop=True)
        self.pronunciation = df["pronunciation"].astype(str).tolist()
        self.asr_small_text = df["whisper_small_text"].astype(str).tolist()
        self.asr_base_text = df["whisper_base_text"].astype(str).tolist()
        self.latex = df["latex_normalized"].astype(str).tolist()

    def __len__(self) -> int:
        return len(self.latex)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        input_small_text = self.asr_small_text[idx]
        input_base_text = self.asr_base_text[idx]
        corrected_text = self.pronunciation[idx]
        latex_text = self.latex[idx]

        input_enc = self.tokenizer(
            f"translate ASR to truth: {input_small_text} || {input_base_text}",
            max_length=self.max_input_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        correct_enc = self.tokenizer(
            corrected_text,
            max_length=self.max_correct_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        latex_enc = self.tokenizer(
            latex_text,
            max_length=self.max_latex_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        input_ids = input_enc.input_ids.squeeze(0)
        attention_mask_correct = input_enc.attention_mask.squeeze(0)

        labels_correct = correct_enc.input_ids.squeeze(0)
        attention_mask_translate = correct_enc.attention_mask.squeeze(0)

        labels_translate = latex_enc.input_ids.squeeze(0)

        # Replace pad token ids in labels with -100 so they are ignored by loss
        pad_id = self.tokenizer.pad_token_id
        labels_correct = labels_correct.masked_fill(labels_correct == pad_id, -100)
        labels_translate = labels_translate.masked_fill(labels_translate == pad_id, -100)

        return {
            "input_ids": input_ids.long(),
            "attention_mask_correct": attention_mask_correct.long(),
            "attention_mask_translate": attention_mask_translate.long(),
            "labels_correct": labels_correct.long(),
            "labels_translate": labels_translate.long(),
        }


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def train(
    model: MathASR,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scheduler: torch.optim.lr_scheduler._LRScheduler | None,
    device: torch.device,
    num_epochs: int,
    grad_clip: float | None = None,
    writer: SummaryWriter | None = None,
) -> None:
    model.train()
    global_step = 0
    for epoch in range(1, num_epochs + 1):
        epoch_loss = 0.0
        pbar = tqdm(dataloader, desc=f"Epoch {epoch}/{num_epochs}")
        for batch in pbar:
            input_ids = batch["input_ids"].to(device)
            attention_mask_correct = batch["attention_mask_correct"].to(device)
            attention_mask_translate = batch["attention_mask_translate"].to(device)
            labels_correct = batch["labels_correct"].to(device)
            labels_translate = batch["labels_translate"].to(device)

            optimizer.zero_grad(set_to_none=True)
            loss, _, _ = model(
                input_ids=input_ids,
                attention_mask_correct=attention_mask_correct,
                attention_mask_translate=attention_mask_translate,
                labels_correct=labels_correct,
                labels_translate=labels_translate,
            )
            loss.backward()
            if grad_clip is not None and grad_clip > 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
            optimizer.step()

            epoch_loss += loss.item()
            pbar.set_postfix({"loss": f"{loss.item():.4f}", "lr": f"{optimizer.param_groups[0]['lr']:.2e}"})
            if writer is not None:
                writer.add_scalar("train/loss", loss.item(), global_step)
                writer.add_scalar("train/lr", optimizer.param_groups[0]["lr"], global_step)
            global_step += 1

            if scheduler is not None:
                scheduler.step()

        avg_loss = epoch_loss / max(1, len(dataloader))
        tqdm.write(f"Epoch {epoch} average loss: {avg_loss:.4f}")
        if writer is not None:
            writer.add_scalar("train/epoch_avg_loss", avg_loss, epoch)
            writer.flush()


def main() -> None:
    parser = argparse.ArgumentParser(description="Train MathASR (two-stage T5) with raw PyTorch")
    parser.add_argument("--csv_path", type=str, default="./result_ASR.csv", help="Path to CSV with columns: whisper_text, pronunciation, latex_normalized")
    parser.add_argument("--tokenizer_path", type=str, default="AAAI2025/MathSpeech_Ablation_Study_LaTeX_translator_T5_small", help="Tokenizer name or path")
    parser.add_argument("--corrector_model", type=str, default="google-t5/t5-small", help="Stage-1 (correction) T5 model name or path")
    parser.add_argument("--translator_model", type=str, default="google-t5/t5-small", help="Stage-2 (translation) T5 model name or path")
    parser.add_argument("--math_speech_checkpoint", type=str, default=None)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--weight_decay", type=float, default=0.0)
    parser.add_argument("--grad_clip", type=float, default=1.0)
    parser.add_argument("--max_input_len", type=int, default=MAX_LENGTH1)
    parser.add_argument("--max_correct_len", type=int, default=MAX_LENGTH2)
    parser.add_argument("--max_latex_len", type=int, default=MAX_LENGTH3)
    parser.add_argument("--output_path", type=str, default="math_speech_ckpts")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--is_tts", type=int, nargs="+", choices=[0, 1], default=[0, 1], help="Filter by is_tts values (e.g., --is_tts 0 1)")
    parser.add_argument("--languages", type=str, nargs="+", choices=["ru", "eng"], default=["ru", "eng"], help="Filter by language values (e.g., --languages ru eng)")
    # Test/evaluation arguments
    parser.add_argument("--test_csv_path", type=str, default=None, help="Optional: path to CSV to evaluate after training")
    parser.add_argument("--test_output_csv", type=str, default=None, help="Optional: where to save test predictions CSV")
    parser.add_argument("--test_batch_size", type=int, default=64, help="Batch size for translate_batch during test")
    parser.add_argument("--num_beams", type=int, default=5, help="Beam size for generation during test")
    args = parser.parse_args()

    set_seed(args.seed)

    output_path_base = args.output_path
    # Derive run-descriptive tags for is_tts and language to embed into output dir
    tts_values = set(args.is_tts or [0, 1])
    if tts_values == {0, 1}:
        tts_tag = "mix"
    elif tts_values == {0}:
        tts_tag = "human"
    elif tts_values == {1}:
        tts_tag = "artificial"
    else:
        raise ValueError("invalid tts values")

    lang_values = set(args.languages or ["ru", "eng"])
    if lang_values == {"ru", "eng"}:
        lang_tag = "multilang"
    elif lang_values == {"ru"}:
        lang_tag = "ru"
    elif lang_values == {"eng"}:
        lang_tag = "eng"
    else:
        raise ValueError("invalid languages argument")

    characters = string.ascii_letters + string.digits

    while True:
        random_string = ''.join(random.choice(characters) for i in range(6))
        output_path = os.path.join(
            output_path_base,
            f"run_{random_string}_tts-{tts_tag}_lang-{lang_tag}",
        )
        if not os.path.exists(output_path):
            break

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print("output dir", output_path)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    tokenizer = T5Tokenizer.from_pretrained(args.tokenizer_path)

    model_corrector = T5ForConditionalGeneration.from_pretrained(args.corrector_model)
    model_corrector.resize_token_embeddings(len(tokenizer))
    model_corrector.to(device)

    model_translator = T5ForConditionalGeneration.from_pretrained(args.translator_model)
    model_translator.resize_token_embeddings(len(tokenizer))
    model_translator.to(device)

    dataset = MathSpeechDataset(
        csv_path=args.csv_path,
        tokenizer=tokenizer,
        max_input_len=args.max_input_len,
        max_correct_len=args.max_correct_len,
        max_latex_len=args.max_latex_len,
        is_tts_filter=args.is_tts,
        language_filter=args.languages,
    )
    tqdm.write(f"Training samples after filtering: {len(dataset)}")

    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, drop_last=False)

    model = MathASR(tokenizer=tokenizer, model_name1=model_corrector, model_name2=model_translator, device=device)

    if args.math_speech_checkpoint is not None:
        model.load_state_dict(torch.load(args.math_speech_checkpoint)) # Load model weights. You need to write the path where the weights are stored.

    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=(len(dataset) // args.batch_size) * args.epochs)

    writer = SummaryWriter(log_dir=output_path)
    train(
        model=model,
        dataloader=dataloader,
        optimizer=optimizer,
        scheduler=scheduler,
        device=device,
        num_epochs=args.epochs,
        grad_clip=args.grad_clip,
        writer=writer,
    )
    writer.close()

    output_path_checkpoint = os.path.join(output_path, 'checkpoint.pt')
    torch.save(
        {
            "model1_state_dict": model.model1.state_dict(),
            "model2_state_dict": model.model2.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict(),
            "tokenizer_name_or_path": args.tokenizer_path,
            "args": vars(args),
        },
        output_path_checkpoint,
    )
    print(f"Saved final checkpoint to {output_path}")

    # -------------------------------
    # Optional test stage (inference)
    # -------------------------------
    if args.test_csv_path:
        # Ensure evaluation mode and left padding for generation
        model.eval()
        tokenizer.padding_side = "left"

        df_test = pd.read_csv(args.test_csv_path)

        # Required ASR hypothesis columns
        required_test_cols = ["whisper_small_text", "whisper_base_text"]
        for col in required_test_cols:
            if col not in df_test.columns:
                raise ValueError(f"Required column '{col}' not found in test CSV {args.test_csv_path}")

        # If training was non-multilingual, filter test by the same languages
        train_langs = list(dict.fromkeys(args.languages)) if hasattr(args, "languages") and args.languages is not None else None
        if train_langs:
            is_multilingual_train = set(train_langs) == {"ru", "eng"}
            if not is_multilingual_train:
                if "language" in df_test.columns:
                    before = len(df_test)
                    df_test = df_test[df_test["language"].isin(train_langs)].reset_index(drop=True)
                    after = len(df_test)
                    print(f"Filtered test by languages {train_langs}: {before} -> {after}")
                else:
                    print("Warning: training used language filtering but test CSV lacks 'language' column; skipping test language filter.")

        beam_small = df_test["whisper_small_text"].astype(str).tolist()
        beam_base = df_test["whisper_base_text"].astype(str).tolist()

        predictions: list[str] = []
        for start in tqdm(range(0, len(beam_small), args.test_batch_size), desc="Testing"):
            end = min(start + args.test_batch_size, len(beam_small))
            batch_preds = model.translate_batch(
                beam_small[start:end],
                beam_base[start:end],
                max_length_input=args.max_input_len,
                max_length_correct=args.max_correct_len,
                max_length_output=args.max_latex_len,
                num_beams=args.num_beams,
            )
            predictions.extend(batch_preds)

        df_test["mathasr_pred_latex"] = predictions

        # Decide output CSV path
        out_csv = "test_result.csv"
        predictions_csv_path = os.path.join(output_path, out_csv)

        # If ground-truth exists, report accuracy and compute in-context metrics
        if "latex_normalized" in df_test.columns:
            truths = df_test["latex_normalized"].astype(str).tolist()
            predictions_no_spaces = [p.replace(' ', '') for p in predictions]
            exact = sum(1 for p, t in zip(predictions, truths) if p.strip() == t.strip())
            total = len(predictions)
            acc = exact / total if total else 0.0
            print(f"Test exact-match accuracy: {acc:.4f} ({exact}/{total})")

            metrics = LatexInContextMetrics()
            # Mix/all
            metrics_values_mix = metrics.compute_all(predictions, truths)
            print("\nIn-context metrics (mix):")
            metrics.dump(metrics_values_mix)
            metrics_base, _ = os.path.splitext(predictions_csv_path)
            with open(f"{metrics_base}_metrics_mix.json", "w") as f:
                json.dump(metrics_values_mix, f)

            # Mix/all without spaces
            metrics_values_mix_nospaces = metrics.compute_all(predictions_no_spaces, truths)
            print("\nIn-context metrics without spaces (mix):")
            metrics.dump(metrics_values_mix_nospaces)
            with open(f"{metrics_base}_metrics_mix_nospaces.json", "w") as f:
                json.dump(metrics_values_mix_nospaces, f)

            # Splits by is_tts if available
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
                    # Artificial without spaces
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
                    # Humans without spaces
                    preds_hum_nospaces = [p.replace(' ', '') for p in preds_hum]
                    metrics_values_hum_nospaces = metrics.compute_all(preds_hum_nospaces, truths_hum)
                    print("\nIn-context metrics without spaces (humans):")
                    metrics.dump(metrics_values_hum_nospaces)
                    with open(f"{metrics_base}_metrics_humans_nospaces.json", "w") as f:
                        json.dump(metrics_values_hum_nospaces, f)

        # Save predictions CSV
        df_test.to_csv(predictions_csv_path, index=False)
        print(f"Saved test predictions to {predictions_csv_path}")


if __name__ == "__main__":
    main()

