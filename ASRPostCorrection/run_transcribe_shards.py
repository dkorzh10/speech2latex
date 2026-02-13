import argparse
import os
import sys
from typing import List, Tuple
from mls.manager.job.utils import training_job_api_from_profile


def parse_args() -> Tuple[argparse.Namespace, List[str]]:
    parser = argparse.ArgumentParser(
        description="Submit transcribe_dataset.py across shards to the jobs cluster."
    )
    parser.add_argument(
        "--num-shards",
        type=int,
        required=True,
        help="Total number of shards/jobs to submit.",
    )
    parser.add_argument(
        "--script",
        type=str,
        default=None,
        help="Path to transcribe_dataset.py (default: resolve next to this file).",
    )
    parser.add_argument(
        "--instance-type",
        type=str,
        default="a100.1gpu",
        help="Cluster instance type (default: a100.1gpu).",
    )
    parser.add_argument(
        "--base-image",
        type=str,
        default="cr.ai.cloud.ru/aicloud-base-images/cuda12.1-torch2-py311:0.0.36",
        help="Base docker image for jobs.",
    )
    parser.add_argument(
        "--env-prefix",
        type=str,
        default="/workspace-SR004.nfs2/d.tarasov/envs/dtarasov-speech2latex/bin",
        help="Directory containing python executable inside the job environment.",
    )
    parser.add_argument(
        "--shm-size-class",
        type=str,
        default="medium",
        help="Shared memory size class for jobs.",
    )
    parser.add_argument(
        "--job-desc-prefix",
        type=str,
        default="S2L: transcribe",
        help="Prefix text for job description.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned job commands without submitting.",
    )
    # Capture remaining args to forward to the underlying script
    args, forward_args = parser.parse_known_args()
    return args, forward_args


def resolve_script_path(user_path: str | None) -> str:
    if user_path:
        return user_path
    this_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(this_dir, "transcribe_dataset.py")


def build_command(
    workdir: str,
    env_prefix: str,
    script_path: str,
    shard_index: int,
    num_shards: int,
    forward_args: List[str],
) -> str:
    # Compose a single shell command string to run inside the job container
    # We cd into the repository workdir to ensure relative paths work
    forwarded = " ".join(forward_args)
    cmd = (
        f"cd {workdir} && {env_prefix}/python {script_path} "
        f"--shard-index {shard_index} --num-shards {num_shards} {forwarded}"
    )
    return cmd.strip()


def main() -> None:
    args, forward_args = parse_args()
    if args.num_shards <= 0:
        raise ValueError("--num-shards must be > 0.")

    script_path = resolve_script_path(args.script)
    if not os.path.isfile(script_path):
        raise FileNotFoundError(f"transcribe script not found: {script_path}")

    client, extra_options = training_job_api_from_profile("default")
    workdir = os.getcwd()
    author_name = "d.tarasov"

    commands: List[str] = []
    for shard_idx in range(args.num_shards):
        cmd = build_command(
            workdir=workdir,
            env_prefix=args.env_prefix,
            script_path=script_path,
            shard_index=shard_idx,
            num_shards=args.num_shards,
            forward_args=forward_args,
        )
        commands.append(cmd)

    if args.dry_run:
        for cmd in commands:
            print(cmd)
        return

    # Submit one job per shard
    for shard_idx, cmd in enumerate(commands):
        job_desc = (
            f"{args.job_desc_prefix} shard {shard_idx}/{args.num_shards} "
            f"#{author_name} #rnd #multimodal #notify_completed @mrsndmn"
        )
        print("\n\n", cmd)
        result = client.run_job(
            payload={
                "script": cmd,
                "job_desc": job_desc,
                "env_variables": {
                    "PYTHONPATH": "./:../src:/workspace-SR004.nfs2/d.tarasov/ProcessLaTeXFormulaTools/:../TeXBLEU",
                    "HF_HOME": "/workspace-SR004.nfs2/.cache/huggingface",
                },
                "instance_type": args.instance_type,
                "region": extra_options["region"],
                "type": "binary_exp",
                "shm_size_class": args.shm_size_class,
                "base_image": args.base_image,
                "n_workers": 1,
                "processes_per_worker": 1,
            }
        )
        print("submitted shard", shard_idx, "result", result)
    print("Submitted", args.num_shards, "jobs.")


if __name__ == "__main__":
    main()

