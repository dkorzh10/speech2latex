
import argparse
from typing import Dict, List, Tuple

import pandas as pd
from datasets import Dataset, load_dataset

def compute_counts_df(df: pd.DataFrame, columns: List[str]) -> Dict[Tuple[str, str], Dict[str, int]]:
    counts: Dict[Tuple[str, str], Dict[str, int]] = {}
    # Create grouping keys
    tmp = df.copy()
    tmp["g_lang"] = tmp["language"].map({"ru": "ru", "eng": "en"})
    tmp["g_tts"] = tmp["is_tts"].map({0: "h", 1: "a"})
    tmp = tmp[tmp["g_lang"].isin(["ru", "en"]) & tmp["g_tts"].isin(["h", "a"])]

    if len(tmp) == 0:
        for key in [("ru", "h"), ("ru", "a"), ("en", "h"), ("en", "a")]:
            counts[key] = {col: 0 for col in columns}
            counts[key]["__rows__"] = 0
        return counts

    per_col_counts = tmp.groupby(["g_lang", "g_tts"])[columns].count()
    group_sizes = tmp.groupby(["g_lang", "g_tts"]).size()

    for key in [("ru", "h"), ("ru", "a"), ("en", "h"), ("en", "a")]:
        if key in per_col_counts.index:
            stats = {col: int(per_col_counts.loc[key, col]) for col in columns}
            stats["__rows__"] = int(group_sizes.loc[key]) if key in group_sizes.index else 0
        else:
            stats = {col: 0 for col in columns}
            stats["__rows__"] = 0
        counts[key] = stats
    return counts


def print_counts(split_name: str, counts: Dict[Tuple[str, str], Dict[str, int]], columns: List[str]) -> None:
    ordered_groups: List[Tuple[str, str]] = [("ru", "h"), ("ru", "a"), ("en", "h"), ("en", "a")]
    print(f"\n=== Split: {split_name} ===")
    for g in ordered_groups:
        stats = counts.get(g)
        if not stats or stats.get("__rows__", 0) == 0:
            print(f"Group {g}: rows=0")
            continue
        print(f"Group {g}: rows={stats['__rows__']}")
        # for col in columns:
        #     print(f"  {col}: {stats[col]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute per-column non-empty counts for Speech2Latex test splits by language/is_tts groups.")
    parser.add_argument(
        "--splits",
        nargs="*",
        default=["equations_test", "sentences_test", "sentences_train", "equations_train"],
        help="Dataset splits to evaluate (default: equations_test sentences_test)",
    )
    parser.add_argument(
        "--columns",
        nargs="*",
        default=None,
        help="Columns to include in aggregation (in addition to language,is_tts). Default: all columns.",
    )
    parser.add_argument(
        "--num-proc",
        type=int,
        default=16,
        help="Number of processes for dataset loading (default: 16)",
    )
    args = parser.parse_args()

    for split in args.splits:
        ds = load_dataset("marsianin500/Speech2Latex", split=split, num_proc=args.num_proc)
        # Determine which columns to keep
        all_columns = list(ds.column_names)
        base_needed = ["language", "is_tts"]
        if args.columns is None or len(args.columns) == 0:
            # Use all columns
            needed = list(dict.fromkeys(base_needed + all_columns))
        else:
            needed = list(dict.fromkeys(base_needed + [c for c in args.columns]))
        drop = [c for c in all_columns if c not in needed]
        if drop:
            ds = ds.remove_columns(drop)

        # Convert to pandas and compute counts
        df = ds.to_pandas()
        # Ensure stable column order for printing, excluding grouping columns at the front
        columns = [c for c in df.columns if c not in ("language", "is_tts")]
        counts = compute_counts_df(df, columns)
        print_counts(split, counts, columns)


if __name__ == "__main__":
    main()

