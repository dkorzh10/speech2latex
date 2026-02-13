#!/usr/bin/env python3
"""
Script to aggregate experiment results from ASRPostCorrection/ckpts folder.
Sorts experiments by properties and generates LaTeX tables.
"""

import copy
import os
import json
import re
from collections import defaultdict
from typing import Dict, List, Any
from tabulate import tabulate


def parse_experiment_name(model_name: str, name: str, model_type: str = 'ASR-PC') -> Dict[str, str]:
    """
    Parse experiment directory name to extract properties.

    Expected format: asr-normalized-Qwen2.5-0.5B_{dataset_split}_{column_type}_{language}_{data_type}_{hash}
    """

    name = name.replace('sentence_normalized', 'sentence-norm')
    name = name.replace('synthetic_small', 'synthetic-small')
    name = name.replace('mix_full', 'mix-full')

    exp_name = name

    if 'qwen' not in model_name.lower():
        # breakpoint()
        return None

    # Remove the base model name and hash
    parts = exp_name.split('_')

    if len(parts) >= 4:
        dataset_split = parts[0]  # equations or sentences
        column_type = parts[1]    # sentence or sentence_normalized
        language = parts[2]       # eng, ru, multilingual
        data_type = parts[3]      # human, synthetic_small, mix
        hash_id = '_'.join(parts[4:]) if len(parts) > 4 else ''

        return {
            'model_type': model_type,
            'model_name': model_name,
            'dataset_split': dataset_split,
            'column_type': column_type,
            'language': language,
            'data_type': data_type,
            'hash_id': hash_id,
            'full_name': name
        }
    else:
        # Fallback for unexpected formats
        return {
            'dataset_split': 'unknown',
            'column_type': 'unknown',
            'language': 'unknown',
            'data_type': 'unknown',
            'hash_id': '',
            'full_name': name
        }


def load_metrics(ckpt_dir: str, model_type: str = 'ASR-PC') -> Dict[str, Dict[str, float]]:
    """
    Load metrics from a checkpoint directory.
    Returns dict with keys: artificial, humans, mix
    """
    metrics = {}
    metric_files = ['artificial_metrics.json', 'humans_metrics.json', 'mix_metrics.json', 'eng_mix_metrics.json', 'ru_mix_metrics.json', 'eng_tts_metrics.json', 'ru_tts_metrics.json', 'eng_human_metrics.json', 'ru_human_metrics.json']

    broken_exp = False

    for metric_file in metric_files:
        if model_type == 'ASR-PC':
            file_path = os.path.join(ckpt_dir, metric_file)
        elif model_type == 'Multimodal':
            file_path = os.path.join(ckpt_dir, 'results', metric_file)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Extract the split name from filename
                    split_name = metric_file.replace('_metrics.json', '')
                    metrics[split_name] = data
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load {file_path}: {e}")
        else:
            print(f"Warning: Could not load {file_path}: File not found")
            broken_exp = True

    # if broken_exp:
    #     return None

    return metrics


def get_metric_value(metrics: Dict[str, float], metric_name: str, default: float = 0.0) -> float:
    """Safely get metric value with default fallback."""
    return metrics.get(metric_name, default) * 100


def create_results_table(experiments: List[Dict[str, Any]], split_type: str = 'mix') -> str:
    """
    Create a LaTeX table from experiment results.

    Args:
        experiments: List of experiment data
        split_type: Which split to use ('artificial', 'humans', 'mix')
    """
    # Define the metrics we want to display
    # metrics_to_show = [
    #     'wer', 'cer', 'bleu', 'sacrebleu', 'meteor', 'rouge1', 'chrf', 'tex_bleu'
    # ]

    # metric_split_types = ['artificial', 'humans', 'mix']
    metric_split_types = [ 'mix' ]

    metrics_to_show = [
        'cer_lower', 'tex_bleu'
    ]

    metrics_columns = []
    for metric_split_type in metric_split_types:
        for metric in metrics_to_show:
            metrics_columns.append(f"{metric_split_type}_{metric}")

    # Prepare table data
    table_data = []
    # headers = ['Dataset', 'Column', 'Language', 'Data Type', 'Hash'] + [m.upper() for m in metrics_columns]
    headers = ['Dataset', 'Column', 'Language', 'Data Type',] + [m.upper() for m in metrics_columns]

    for exp in experiments:
        if exp['properties']['data_type'] != split_type:
            # breakpoint()
            continue

        row = [
            exp['properties']['dataset_split'],
            exp['properties']['column_type'],
            exp['properties']['language'],
            exp['properties']['data_type'],
            exp['properties']['hash_id'][:8] if exp['properties']['hash_id'] else ''
        ]

        for metric_split_type in metric_split_types:
            if metric_split_type not in exp['metrics']:
                raise ValueError(f"Metric {metric_split_type} not found in {exp['properties']['full_name']}")

            metrics = exp['metrics'][metric_split_type]

            # Add metric values
            for metric in metrics_to_show:
                value = get_metric_value(metrics, metric)
                row.append(f"{value:.2f}")

            table_data.append(row)

    # Sort by dataset_split, language, data_type
    table_data.sort(key=lambda x: (x[0], x[2], x[3]))

    # Generate LaTeX table
    # breakpoint()
    latex_table = tabulate(
        table_data,
        headers=headers,
        tablefmt='latex',
        floatfmt='.2f',
        numalign='right'
    )

    return latex_table

def build_s2l_equations_table(experiments):

    metric_split_types_languages = [
        ('multilingual', ['mix', 'humans', 'artificial']),
        ('eng', ['eng_mix', 'eng_human', 'eng_tts']),
        ('ru', ['ru_mix', 'ru_human', 'ru_tts']),
    ]
    # metric_split_types =
    # metric_split_types = ['mix']

    metrics_to_show = [
        'cer_lower', 'tex_bleu'
    ]

    metrics_columns = []
    for metric_split_type in metric_split_types_languages[0][1]:
        for metric in metrics_to_show:
            metrics_columns.append(f"{metric_split_type[:1]}_{metric}")

    # Prepare table data
    table_data = []
    # headers = ['Dataset', 'Column', 'Language', 'Data Type', 'Hash'] + [m.upper() for m in metrics_columns]
    # headers = ['Model', 'Train', 'Language', 'Hash' ] + [m.upper() for m in metrics_columns]
    headers = ['Model', 'Train', 'Train Lang', 'Test Lang'] + [m.upper() for m in metrics_columns]

    for exp in experiments:

        for test_lang, metric_split_types in metric_split_types_languages:

            model_name_mapping = {
                'Qwen2.5-0.5B-instruct': 'Q-0.5B',
                'Qwen2.5-1.5B-instruct': 'Q-1.5B',
                'Qwen2.5-1.5B-instruct-test': 'Q-1.5B',
                'Qwen2.5-math-1.5B-instruct': 'Q-math-1.5B',
                'Qwen2.5-7B-instruct': 'Q-7B',
                'Qwen2.5-7B-instruct-partial-unfreeze': 'Q-7B-pu',
                'Qwen2.5-7B-instruct-r16a64': 'Q-7B-r16a64',
                'Qwen2.5-7B-instruct-r8a32': 'Q-7B-r8a32',
                'Qwen2-Audio-7B-instruct-LoRa-r16-a32-lr1e-4': 'QA-7B-r16a32',
                'Qwen2-Audio-7B-instruct-LoRa-r16-a64-lr1e-4': 'QA-7B-r16a64',
                'Qwen2-Audio-7B-instruct-LoRa-r8-a32-lr1e-4': 'QA-7B-r8a32',
                'Qwen2-Audio-7B-instruct-LoRa-r8-a16-lr1e-4': 'QA-7B-r8a16',
            }

            data_type_mapping = {
                'mix': 'Mix',
                'mix-full': 'Mix-full',
                'human': 'H',
                'synthetic-small': 'A',
            }

            language_mapping = {
                'eng': 'Eng',
                'ru': 'Ru',
                'multilingual': 'Eng+Ru',
            }

            row = [
                model_name_mapping[exp['properties']['model_name']],
                data_type_mapping[exp['properties']['data_type']],
                language_mapping[exp['properties']['language']],
                language_mapping[test_lang],
                # exp['properties']['hash_id'][:8] if exp['properties']['hash_id'] else ''
            ]
            for metric_split_type in metric_split_types:
                if metric_split_type not in exp['metrics']:
                    print(f"Metric {metric_split_type} not found in {exp['properties']['full_name']}")
                    continue
                    # raise ValueError(f"Metric {metric_split_type} not found in {exp['properties']['full_name']}")

                metrics = exp['metrics'][metric_split_type]
                if metric_split_type == 'eng':
                    breakpoint()

                # row.append(metric_split_type)

                # Add metric values
                for metric in metrics_to_show:
                    value = get_metric_value(metrics, metric)
                    row.append(f"{value:.2f}")

            table_data.append(row)

    # Sort by dataset_split, language, data_type

    models_order = [ 'Q-0.5B', 'Q-1.5B', 'Q-math-1.5B', 'Q-7B', 'QA-7B', 'Q-7B-pu', 'Q-7B-r16a64', 'Q-7B-r8a32', 'QA-7B-r16a32', 'QA-7B-r16a64', 'QA-7B-r8a32', 'QA-7B-r8a16']
    train_split_order = [ 'Mix-full', 'Mix', 'H', 'A', '-' ]
    languages_order = [ 'Eng+Ru', 'Eng', 'Ru', ]

    table_data.sort(key=lambda x: (models_order.index(x[0]), train_split_order.index(x[1]), languages_order.index(x[2])))

    # Generate LaTeX table
    # breakpoint()
    latex_table = tabulate(
        table_data,
        headers=headers,
        tablefmt='latex',
        floatfmt='.2f',
        numalign='right'
    )

    return latex_table


def build_s2l_sentences_table(experiments):

    metric_split_types = ['humans', 'artificial']
    # metric_split_types = ['mix']

    metrics_to_show = [
        'cer_lower', 'text_only_cer_lower', 'formulas_only_cer_lower', 'formulas_only_tex_bleu'
    ]

    metrics_columns = []
    for metric_split_type in metric_split_types:
        for metric in metrics_to_show:
            metric_name = metric
            if metric_name.startswith('text_only'):
                metric_name = metric_name.removeprefix('text_only_')
                metric_name = metric_name + '(Txt)'
            elif metric_name.startswith('formulas_only'):
                metric_name = metric_name.removeprefix('formulas_only_')
                metric_name = metric_name + '(Eq)'

            metrics_columns.append(f"{metric_split_type[:1]}_{metric_name}")

    # Prepare table data
    table_data = []
    # headers = ['Dataset', 'Column', 'Language', 'Data Type', 'Hash'] + [m.upper() for m in metrics_columns]
    # headers = ['Model', 'Train', 'Hash' ] + [m.upper() for m in metrics_columns]
    headers = ['Model', 'Train', ] + [m.upper() for m in metrics_columns]

    for exp in experiments:

        model_name_mapping = {
            'Qwen2.5-0.5B-instruct': 'Q-0.5B',
            'Qwen2.5-1.5B-instruct': 'Q-1.5B',
            'Qwen2.5-1.5B-instruct-test': 'Q-1.5B',
            'Qwen2.5-math-1.5B-instruct': 'Q-math-1.5B',
            'Qwen2.5-7B-instruct': 'Q-7B',
        }

        data_type_mapping = {
            'mix': 'Mix',
            'mix-full': 'Mix-full',
            'human': 'H',
            'synthetic-small': 'A',
        }

        language_mapping = {
            'eng': 'Eng',
            'ru': 'Ru',
            'multilingual': 'Eng+Ru',
        }

        row = [
            model_name_mapping[exp['properties']['model_name']],
            data_type_mapping[exp['properties']['data_type']],
            language_mapping[exp['properties']['language']],
            # exp['properties']['hash_id'][:8] if exp['properties']['hash_id'] else ''
        ]


        for metric_split_type in metric_split_types:
            if metric_split_type not in exp['metrics']:
                raise ValueError(f"Metric {metric_split_type} not found in {exp['properties']['full_name']}")

            metrics = exp['metrics'][metric_split_type]

            # row.append(metric_split_type)

            # Add metric values
            for metric in metrics_to_show:
                value = get_metric_value(metrics, metric)
                row.append(f"{value:.2f}")

        table_data.append(row)

    # Sort by dataset_split, language, data_type

    models_order = [ 'Q-0.5B', 'Q-1.5B', 'Q-math-1.5B', 'Q-7B' ]
    train_split_order = [ 'Mix', 'H', 'A' ]

    table_data.sort(key=lambda x: (models_order.index(x[0]), train_split_order.index(x[1])))

    # Generate LaTeX table
    # breakpoint()
    latex_table = tabulate(
        table_data,
        headers=headers,
        tablefmt='latex',
        floatfmt='.2f',
        numalign='right'
    )

    return latex_table




def main():
    # Path to the checkpoints directory

    # import sys
    # ckpts_dir = sys.argv[1]
    ckpts_dir = "./ckpts"
    

    if not os.path.exists(ckpts_dir):
        print(f"Error: Directory {ckpts_dir} not found!")
        return

    # Collect all experiment directories
    experiments = []

    for model_name in os.listdir(ckpts_dir):
        # print("model_name", model_name)
        if model_name == 'asr-normalized-Qwen2.5-math-1.5B-instruct-2e':
            continue

        # if 'Qwen2.5-1.5B-instruct-test' in model_name:
        #     continue

        model_experiments = os.path.join(ckpts_dir, model_name)
        if not os.path.isdir(model_experiments):
            continue

        # if 'unnormalized' not in model_name:
        #     continue

        model_name = model_name.replace('asr-normalized-', '')
        model_name = model_name.replace('asr-unnormalized-', '')
        if model_name == 'pretrained_Qwen2.5-0.5B':
            continue
        
        print("model_experiments", model_experiments)
        for item in os.listdir(model_experiments):

            item_path = os.path.join(model_experiments, item)
            if not os.path.isdir(item_path):
                continue

            # Parse experiment properties
            properties = parse_experiment_name(model_name, item)
            if properties is None:
                print("properties is None", item_path)
                continue

            # Load metrics
            metrics = load_metrics(item_path)

            if metrics:  # Only include if we found metrics
                experiments.append({
                    'properties': properties,
                    'metrics': metrics,
                    'path': item_path
                })

    # experiments = []
    qwen_audio_experiments = [
        '../Multimodal/qwen_audio/ckpts/qwen2-audio-7b-instruct-lora-r8-a32-lr1e-4',
        # '../Multimodal/qwen_audio/ckpts/qwen2-audio-7b-instruct-lora-r16-a32-lr1e-4',
        # '../Multimodal/qwen_audio/ckpts/qwen2-audio-7b-instruct-lora-r8-a16-lr1e-4',
        '../Multimodal/qwen_audio/ckpts/qwen2-audio-7b-instruct-lora-r16-a64-lr1e-4',
    ]
    # qwen_audio_experiments = []
    for qwen_audio_experiment in qwen_audio_experiments:
        for item in os.listdir(qwen_audio_experiment):
            item_path = os.path.join(qwen_audio_experiment, item)
            assert os.path.isdir(item_path)

            model_name = os.path.basename(qwen_audio_experiment)
            model_name = model_name.replace('qwen2-audio-7b-instruct-lora', 'Qwen2-Audio-7B-instruct-LoRa')

            # Parse experiment properties
            properties = parse_experiment_name(model_name, item, model_type='Multimodal')
            # if properties['language'] != 'eng':
            #     breakpoint()
            #     continue

            # Load metrics
            metrics = load_metrics(item_path, model_type='Multimodal')

            if metrics:  # Only include if we found metrics
                experiments.append({
                    'properties': properties,
                    'metrics': metrics,
                    'path': item_path
                })


    print(f"Found {len(experiments)} experiments with full metrics")

    # Group experiments by properties for better organization
    # grouped_experiments = defaultdict(list)
    # for exp in experiments:
    #     key = (exp['properties']['dataset_split'], exp['properties']['language'])
    #     grouped_experiments[key].append(exp)

    # S2L Equations tables

    # Mix train for different languages
    equations_experiments = [exp for exp in experiments if exp['properties']['dataset_split'] == 'equations']

    mathspeech_experiment = {
        'properties': {
            'model_name': 'MathSpeech',
            'data_type': '-',
            'language': 'eng',
            'hash_id': '',
        },
        'metrics': load_metrics('../MathSpeech/Experiments'),
        'path': ''
    }
    # equations_experiments.append(mathspeech_experiment)


    # equations_experiments = [ exp for exp in experiments if exp['properties']['model_name'] not in ['proofGPT-1.3B', 'Llama-3.2-1B-Instruct', 'Qwen2.5-1.5B-instruct-test'] ]
    # equations_experiments = [ exp for exp in experiments if exp['properties']['language'] == 'multilingual' ]

    sentences_experiments = [exp for exp in experiments if exp['properties']['dataset_split'] == 'sentences']

    s2l_equations_table = build_s2l_equations_table(copy.deepcopy(equations_experiments))
    print(s2l_equations_table)

    text_only_cer_lower_table = build_s2l_sentences_table(copy.deepcopy(sentences_experiments))
    print(text_only_cer_lower_table)

    return

    # Generate tables for each split type
    split_types = ['mix', 'human', 'synthetic-small']

    for split_type in split_types:
        print(f"\n{'='*80}")
        print(f"Results for {split_type.upper()} split")
        print(f"{'='*80}")

        # Create table for all experiments
        all_table = create_results_table(experiments, split_type)
        print(all_table)

        # Create tables for each group
        for (dataset_split, language), group_exps in grouped_experiments.items():
            if len(group_exps) > 1:  # Only show groups with multiple experiments
                print(f"\n{'-'*60}")
                print(f"Group: {dataset_split} - {language}")
                print(f"{'-'*60}")
                group_table = create_results_table(group_exps, split_type)
                print(group_table)

    # # Save results to file
    # output_file = "experiment_results.tex"
    # with open(output_file, 'w') as f:
    #     f.write("\\documentclass{article}\n")
    #     f.write("\\usepackage{booktabs}\n")
    #     f.write("\\usepackage{longtable}\n")
    #     f.write("\\begin{document}\n\n")

    #     for split_type in split_types:
    #         f.write(f"\\section*{{Results for {split_type.upper()} split}}\n")
    #         f.write(create_results_table(experiments, split_type))
    #         f.write("\n\n")

    #     f.write("\\end{document}\n")

    # print(f"\nResults saved to {output_file}")


if __name__ == "__main__":
    main()
