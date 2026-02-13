import argparse
import glob
import os
import re
from typing import Iterable, List, Optional, Sequence

import pandas as pd


SHARD_NAME_RE = re.compile(r"^(?P<prefix>.+)_shard(?P<idx>\d+)of(?P<total>\d+)_(?P<suffix>.+)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Join transcriptions from shard CSVs in correct order.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--glob", dest="glob_pattern", type=str, default=None, help="Glob pattern to match shard CSVs.")
    group.add_argument("--input-files", nargs="+", default=None, help="Explicit list of shard CSV file paths.")
    parser.add_argument("--num-shards", type=int, default=None, help="Total number of shards; if omitted, inferred from filenames.")
    parser.add_argument("--mode", choices=["interleave", "concat"], default="interleave", help="Merge strategy; default interleave.")
    parser.add_argument("--output-file", type=str, default=None, help="Path to output merged CSV.")
    return parser.parse_args()


def discover_files(glob_pattern: Optional[str], input_files: Optional[Sequence[str]]) -> List[str]:
    if glob_pattern:
        files = sorted(glob.glob(glob_pattern))
    else:
        files = list(input_files or [])
    if not files:
        raise FileNotFoundError("No input files found.")
    return files


def parse_shard_info(path: str) -> Optional[tuple[int, int, str, str]]:
    name = os.path.basename(path)
    m = SHARD_NAME_RE.match(name)
    if not m:
        return None
    idx = int(m.group("idx"))
    total = int(m.group("total"))
    return idx, total, m.group("prefix"), m.group("suffix")


def infer_output_name(files: List[str]) -> str:
    # Try to infer from first matching filename
    for f in files:
        info = parse_shard_info(f)
        if info is None:
            continue
        _idx, _total, prefix, suffix = info
        return f"{prefix}_{suffix}"
    return "merged_shards.csv"


def ensure_same_columns(dfs: List[pd.DataFrame]) -> List[pd.DataFrame]:
    # Union of all columns, preserve order from first df then append missing
    base_cols = list(dfs[0].columns)
    union = list(base_cols)
    for df in dfs[1:]:
        for c in df.columns:
            if c not in union:
                union.append(c)
    aligned = [df.reindex(columns=union) for df in dfs]
    return aligned


def interleave_rows(dfs: List[pd.DataFrame]) -> pd.DataFrame:
    # Append rows in order: row0 of each shard, then row1, etc.
    lengths = [len(df) for df in dfs]
    max_len = max(lengths)
    parts: List[pd.DataFrame] = []
    for i in range(max_len):
        row_chunks = [dfs[s].iloc[[i]] for s in range(len(dfs)) if i < lengths[s]]
        if row_chunks:
            parts.append(pd.concat(row_chunks, axis=0, ignore_index=True))
    if not parts:
        return pd.DataFrame(columns=dfs[0].columns)
    return pd.concat(parts, axis=0, ignore_index=True)


def concat_rows(dfs: List[pd.DataFrame]) -> pd.DataFrame:
    return pd.concat(dfs, axis=0, ignore_index=True)


def main() -> None:
    args = parse_args()
    files = discover_files(args.glob_pattern, args.input_files)

    # Parse shard info and sort by shard index if available
    shard_infos = []
    for f in files:
        info = parse_shard_info(f)
        shard_infos.append((f, info))

    # If all have shard info, sort; also validate total shards
    all_have_info = all(info is not None for _, info in shard_infos)
    if all_have_info:
        total_from_names = shard_infos[0][1][1]  # type: ignore[index]
        if args.num_shards is None:
            args.num_shards = total_from_names
        elif args.num_shards != total_from_names:
            raise ValueError(f"--num-shards={args.num_shards} does not match filenames' total={total_from_names}")
        shard_infos.sort(key=lambda x: x[1][0])  # type: ignore[index]
        files = [f for f, _ in shard_infos]
    else:
        if args.num_shards is None:
            args.num_shards = len(files)
        # Keep user order; assume provided in shard index order

    # Read dataframes
    dfs = [pd.read_csv(f) for f in files]
    dfs = ensure_same_columns(dfs)

    # Choose merge strategy
    if args.mode == "interleave":
        merged = interleave_rows(dfs)
    else:
        merged = concat_rows(dfs)

    # Infer output filename if needed
    output_file = args.output_file or infer_output_name(files)
    merged.to_csv(output_file, index=False)
    print(f"Saved merged CSV to {output_file}")


if __name__ == "__main__":
    main()

