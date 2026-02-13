
import os
import sys
import argparse
import fnmatch

from mls.manager.job.utils import training_job_api_from_profile

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run Qwen ASR post-correction jobs over configs")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to a single config .json file to run")
    parser.add_argument("--config-filter", "--config_filter", dest="config_filter", type=str, default=None,
                        help="Substring or glob pattern to filter configs under ./configs (e.g. '*qwen2.5*.json')")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print jobs without submitting")
    parser.add_argument("--dataset-split", "--dataset_split", dest="dataset_splits", action="append", default=None,
                        help="Dataset split(s) to run: sentences,equations. Multiple flags or comma-separated.")
    parser.add_argument("--latex-column-name", "--latex_column_name", dest="latex_column_names", action="append", default=None,
                        help="Latex column name(s) to run: sentence_normalized or sentence. Multiple flags or comma-separated.")
    parser.add_argument("--language", dest="languages", action="append", default=None,
                        help="Language(s) to run: eng,ru,multilingual. Multiple flags or comma-separated.")
    parser.add_argument("--data-type", "--data_type", dest="data_types", action="append", default=None,
                        help="Data type(s) to run: human,synthetic_small,mix,mix_full. Multiple flags or comma-separated.")
    parser.add_argument("--balanced-sampling", "--balanced_sampling", dest="balanced_sampling", action="store_true",
                        help="Enable balanced RU/EN sampling when training with language=multilingual")
    parser.add_argument("--transcribation_column_name", default=None)

    args, _unknown = parser.parse_known_args()

    # Backward compatibility with positional 'dry'
    dry_run = args.dry_run or ('dry' in sys.argv[1:])

    client, extra_options = training_job_api_from_profile('default')

    workdir = os.getcwd()

    env_prefix = '/workspace-SR004.nfs2/d.tarasov/envs/dtarasov-speech2latex/bin'

    author_name = 'd.tarasov'

    configs_dir = os.path.join(workdir, 'configs')
    discovered_configs = []
    try:
        discovered_configs = [f for f in os.listdir(configs_dir) if f.endswith('.json')]
    except FileNotFoundError:
        pass

    selected_config_paths = []

    if args.config is not None:
        user_path = args.config
        candidate_paths = [
            user_path if os.path.isabs(user_path) else os.path.join(workdir, user_path),
            os.path.join(configs_dir, os.path.basename(user_path)),
        ]
        found = next((p for p in candidate_paths if os.path.exists(p)), None)
        if found is None:
            raise FileNotFoundError(f"Config file not found: {args.config}")
        selected_config_paths = [found]
    else:
        filtered = discovered_configs
        if args.config_filter:
            pattern = args.config_filter
            if any(ch in pattern for ch in '*?[]'):
                filtered = [f for f in filtered if fnmatch.fnmatch(f, pattern)]
            else:
                filtered = [f for f in filtered if pattern in f]

        # Preserve previous hard-coded restrictions only when no filter is provided
        if args.config_filter is None and args.config is None:
            keep = []
            for fname in filtered:
                if 'test' in fname:
                    continue
                if fname in ('config-qwen2.5-math-2e.json', 'config-qwen2.5-1.5B.json'):
                    continue
                if fname != 'config-llama3.2-1B.json':
                    continue
                keep.append(fname)
            filtered = keep

        selected_config_paths = [os.path.join(configs_dir, f) for f in filtered]

    print("selected_config_paths", [os.path.relpath(p, workdir) if p.startswith(workdir) else p for p in selected_config_paths])

    # Normalize list-like CLI inputs
    def _normalize_list(maybe_list):
        if maybe_list is None:
            return None
        result = []
        for item in maybe_list:
            if item is None:
                continue
            parts = [p for p in (s.strip() for s in item.split(',')) if p]
            result.extend(parts)
        return result or None

    user_dataset_splits = _normalize_list(args.dataset_splits)
    user_latex_column_names = _normalize_list(args.latex_column_names)
    user_languages = _normalize_list(args.languages)
    user_data_types = _normalize_list(args.data_types)

    dataset_splits_iter = user_dataset_splits if user_dataset_splits is not None else ['sentences', 'equations']
    latex_column_names_iter = user_latex_column_names if user_latex_column_names is not None else ['sentence_normalized']
    languages_iter = user_languages if user_languages is not None else ['eng', 'ru', 'multilingual']
    data_types_iter = user_data_types if user_data_types is not None else ['human', 'synthetic_small', 'mix', 'mix_full']

    for config_path in selected_config_paths:
        config_file = os.path.basename(config_path)

        for dataset_split in dataset_splits_iter:
            for latex_column_name in latex_column_names_iter:
                for language in languages_iter:
                    if dataset_split == 'sentences' and (language == 'ru' or language == 'multilingual'):
                        # print("skip 1")
                        continue

                    for data_type in data_types_iter:

                        if data_type == 'mix_full':
                            if dataset_split != 'equations':
                                # print("skip non eq")
                                continue
                            if language != 'multilingual':
                                # print("skip non ml")
                                continue

                        command = (
                            f"cd {workdir} && {env_prefix}/python train_test_qwen.py "
                            f"--dataset_split {dataset_split} "
                            f"--latex_column_name {latex_column_name} "
                            f"--language {language} "
                            f"--data_type {data_type} "
                            f"--config \"{config_path}\""
                        )
                        if args.balanced_sampling:
                            command += " --balanced_sampling"

                        if args.transcribation_column_name:
                            command += f" --transcribation_column_name {args.transcribation_column_name}"

                        print("\n\n", command)
                        if dry_run:
                            continue

                        result = client.run_job(
                            payload={
                                'script': command,
                                'job_desc': f'S2L: {config_file.removesuffix(".json")} {dataset_split} lang={language} data={data_type} #{author_name} #rnd #multimodal  #notify_completed @mrsndmn',
                                'env_variables': {
                                    'PYTHONPATH': './:../src:/workspace-SR004.nfs2/d.tarasov/ProcessLaTeXFormulaTools/:../TeXBLEU',
                                    'HF_HOME': '/workspace-SR004.nfs2/.cache/huggingface',
                                },
                                'instance_type': 'a100.1gpu',
                                'region': extra_options['region'],
                                'type': 'binary_exp',
                                'shm_size_class': 'medium',
                                'base_image': 'cr.ai.cloud.ru/aicloud-base-images/cuda12.1-torch2-py311:0.0.36',
                                'n_workers': 1,              # Количество воркеров.
                                'processes_per_worker': 1,   # Количество процессов на воркер. Для accelerate нужно запускать 1 процесс на воркер. Для torchrun лучше не заполнять этот параметр. По умолчанию запускается по количеству GPU на одном воркере - это подходит для torchrun.
                            }
                        )

                        print("dataset_split", dataset_split, "latex_column_name", latex_column_name, "language", language, "data_type", data_type, "result", result)

