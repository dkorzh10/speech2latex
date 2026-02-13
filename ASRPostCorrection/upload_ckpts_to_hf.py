"""
Upload ASR post-correction checkpoints from ASRPostCorrection/ckpts to Hugging Face (marsianin500).

Usage:
  cd ASRPostCorrection
  pip install huggingface_hub
  huggingface-cli login
  python upload_ckpts_to_hf.py [--ckpts_dir ./ckpts] [--dry_run]

Repo IDs: marsianin500/<repo_name> where repo_name = base + "-" + variant (e.g. asr-normalized-Qwen2.5-0.5B-instruct-equations_sentence_normalized_multilingual_mix_tduwXj).
"""
import argparse
import os

# (base_folder, variant_folder, lora_only: only upload tokenizer + adapter, no full tuned-model)
MODELS_TO_UPLOAD = [
    ("asr-normalized-Qwen2.5-0.5B-instruct", "equations_sentence_normalized_multilingual_mix_tduwXj", False),
    ("asr-normalized-Qwen2.5-0.5B-instruct", "equations_sentence_normalized_multilingual_mix_full_nqVVnm", False),
    ("asr-normalized-Qwen2.5-0.5B-instruct", "sentences_sentence_normalized_eng_mix_fFZuui", False),
    ("asr-normalized-Qwen2.5-1.5B-instruct", "equations_sentence_normalized_multilingual_mix_DzL6wo", False),
    ("asr-normalized-Qwen2.5-math-1.5B-instruct", "equations_sentence_normalized_multilingual_mix_full_fMgSB2", False),
    ("asr-normalized-Qwen2.5-math-1.5B-instruct", "equations_sentence_normalized_multilingual_mix_FvQUss", False),
    ("asr-normalized-Qwen2.5-math-1.5B-instruct", "sentences_sentence_normalized_eng_mix_LunlPY", False),
    ("asr-normalized-Qwen2.5-7B-instruct-r16a64", "equations_sentence_normalized_multilingual_mix_WMbZjP", True),
    ("asr-normalized-Qwen2.5-7B-instruct-r16a64", "equations_sentence_normalized_multilingual_mix_full_Tuex5z", True),
]


def repo_id_for(base: str, variant: str) -> str:
    base = base.replace("asr-normalized-", "")
    variant = variant.replace("equations_sentence_normalized", "equations")
    variant = variant.replace("sentences_sentence_normalized", "sentences")
    variant = "_".join(variant.split("_")[:-1])
    name = f"{base}-{variant}".replace("/", "-")
    return f"marsianin500/{name}"


def upload_one(ckpts_dir: str, base: str, variant: str, lora_only: bool, dry_run: bool) -> None:
    local_path = os.path.join(ckpts_dir, base, variant)
    if not os.path.isdir(local_path):
        print(f"[SKIP] Not found: {local_path}")
        return
    repo_id = repo_id_for(base, variant)
    try:
        from huggingface_hub import HfApi, create_repo
        api = HfApi()
        if dry_run:
            print(f"[DRY-RUN] Would upload {local_path} -> {repo_id} (lora_only={lora_only})")
            return
        create_repo(repo_id, repo_type="model", exist_ok=True)
        if lora_only:
            api.upload_folder(folder_path=local_path, repo_id=repo_id, repo_type="model")
            print(f"[OK] Uploaded (adapter+tokenizer): {local_path} -> {repo_id}")
        else:
            tokenizer_path = os.path.join(local_path, "tokenizer")
            tuned_path = os.path.join(local_path, "tuned-model")
            if os.path.isdir(tokenizer_path):
                api.upload_folder(folder_path=tokenizer_path, repo_id=repo_id, repo_type="model")
            if os.path.isdir(tuned_path):
                api.upload_folder(folder_path=tuned_path, repo_id=repo_id, repo_type="model")
            print(f"[OK] Uploaded: {local_path} -> {repo_id}")
    except Exception as e:
        print(f"[ERROR] {local_path} -> {repo_id}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Upload ckpts to Hugging Face (marsianin500)")
    parser.add_argument("--ckpts_dir", type=str, default=os.path.join(os.path.dirname(__file__), "ckpts"),
                        help="Path to ckpts directory (default: ASRPostCorrection/ckpts)")
    parser.add_argument("--dry_run", action="store_true", help="Only print what would be uploaded")
    args = parser.parse_args()
    ckpts_dir = os.path.abspath(args.ckpts_dir)
    if not os.path.isdir(ckpts_dir):
        raise SystemExit(f"Not a directory: {ckpts_dir}")
    for base, variant, lora_only in MODELS_TO_UPLOAD:
        upload_one(ckpts_dir, base, variant, lora_only, args.dry_run)


if __name__ == "__main__":
    main()
