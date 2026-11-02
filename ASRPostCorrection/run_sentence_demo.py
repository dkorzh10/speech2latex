"""Generate sentence demo predictions from the existing, unedited ASR snapshot.

Run with the inference dependencies in the project .venv. This reuses cached
Whisper transcriptions; it does not run ASR or use reference text in the prompt.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

from chat_template_with_generation import CHAT_TEMPLATE_WITH_GENERATION


experiment_configs = [
    {"name": "0.5b", "model": "marsianin500/Qwen2.5-0.5B-instruct-sentences_eng_mix"},
    {"name": "math-1.5b", "model": "marsianin500/Qwen2.5-math-1.5B-instruct-sentences_eng_mix"},
]
MAX_NEW_TOKENS = 512


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=root / "docs/demo_results.json")
    parser.add_argument("--output", type=Path, default=root / "docs/demo_sentence_results.json")
    parser.add_argument("--model", choices=[c["name"] for c in experiment_configs], default="0.5b")
    parser.add_argument("--revision", help="Optional published model commit to reproduce")
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    if args.revision and not re.fullmatch(r"[0-9a-f]{40}", args.revision):
        parser.error("--revision must be a complete 40-character model commit hash")
    source = args.source.read_bytes()
    rows = [r for r in json.loads(source)["results"] if r["split"].startswith("sentences_")]
    if not rows:
        parser.error("Source snapshot contains no sentence samples")

    import torch
    from huggingface_hub import model_info
    from transformers import AutoModelForCausalLM, AutoTokenizer

    repo = next(c["model"] for c in experiment_configs if c["name"] == args.model)
    revision = args.revision or model_info(repo).sha
    tokenizer = AutoTokenizer.from_pretrained(repo, revision=revision)
    dtype = torch.bfloat16 if args.device.startswith("cuda") else torch.float32
    torch.set_num_threads(8)
    model = AutoModelForCausalLM.from_pretrained(repo, revision=revision, torch_dtype=dtype).to(args.device)
    model.eval()
    predictions = []
    with torch.inference_mode():
        for row in rows:
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Please, give me LaTeX representation of the following formula. Formula pronunciation: " + row["whisper_transcription"]},
            ]
            inputs = tokenizer.apply_chat_template(
                messages, chat_template=CHAT_TEMPLATE_WITH_GENERATION,
                add_generation_prompt=True, tokenize=True,
                return_dict=True, return_tensors="pt",
            ).to(args.device)
            tokens = model.generate(
                **inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )[0, inputs["input_ids"].shape[1]:]
            result = {key: row[key] for key in (
                "split", "sample_id", "audio_path", "reference_latex", "whisper_transcription",
            )}
            result.update(
                model_id=repo,
                predicted_latex=tokenizer.decode(tokens, skip_special_tokens=True).strip(),
                hit_token_limit=len(tokens) == MAX_NEW_TOKENS and tokens[-1].item() != tokenizer.eos_token_id,
            )
            predictions.append(result)
            print(row["split"], row["sample_id"], result["predicted_latex"], flush=True)
    payload = {
        "model_id": repo, "model_revision": revision,
        "input_snapshot_sha256": hashlib.sha256(source).hexdigest(),
        "asr_source": "Cached whisper_transcription fields from the input snapshot; original ASR model was not recorded.",
        "results": predictions,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
