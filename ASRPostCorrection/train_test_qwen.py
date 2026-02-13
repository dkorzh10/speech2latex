import sys
import datasets
from pytorch_lightning.loggers import WandbLogger, CSVLogger

import argparse
import json
import os
import pickle
import random
import string

from collections import defaultdict

import numpy as np
import torch
import torch.nn as nn
import pytorch_lightning as pl
import torchmetrics

from tqdm.auto import tqdm

from typing import List

from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.optimization import get_linear_schedule_with_warmup
# from peft import LoraConfig, get_peft_model, TaskType
from pytorch_lightning.loggers import CSVLogger
from dataset import ASRDataset, get_collate_function, get_dataloader
        
import pandas as pd

from s2l.eval import LatexInContextMetrics


from test_qwen import batched_model_generation

from qwen_pl import Model_pl, Config

def test(
        model,
        tokenizer,
        test_dataset,
        model_name,
        pron_column_name = 'whisper_text',
        latex_column_name = 'sentence',
        transcribation_column_name = None,
    ):

    DEVICE='cuda'

    torch.set_default_dtype(torch.bfloat16)

    assert tokenizer.padding_side == 'left'

    model.eval()
    # model = torch.compile(model, mode='reduce-overhead')

    outputs = defaultdict(list)

    test_dataset = ASRDataset(test_dataset, pron_column_name=pron_column_name, latex_column_name=latex_column_name, transcribation_column_name=args.transcribation_column_name)

    # formulas normalization will be performed in batched_model_generation
    collate_function = get_collate_function(tokenizer, model_name, process_formulas=None)

    batch_size = 32
    test_loader = get_dataloader(test_dataset, batch_size, collate_function, num_workers=0, train=False)

    for batch in tqdm(test_loader):

        generated_latex = batched_model_generation(model, tokenizer, batch, device=DEVICE)

        predicted_text = []
        if transcribation_column_name is None:
            predicted_text = generated_latex['predicted_text']
        else:
            for item in generated_latex['predicted_text']:
                item_split = item.split('LaTex: ')
                latex_only = item_split[-1]
                predicted_text.append(latex_only)

        target_text = generated_latex['target_text']

        outputs['latex_pred'].extend(predicted_text)
        outputs['latex_true'].extend(target_text)

    return outputs


if __name__ == "__main__":
    # jobs env crutches
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context
    import nltk
    nltk.download('punkt_tab')

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='./config-4.json')
    parser.add_argument('--dataset_split', required=True, choices=['sentences', 'equations'])
    parser.add_argument('--latex_column_name', required=True, choices=['sentence', 'sentence_normalized'])
    parser.add_argument('--transcribation_column_name', default=None)
    parser.add_argument('--language', required=True, choices=['eng', 'ru', 'multilingual'])
    parser.add_argument('--data_type', required=True, choices=['human', 'synthetic_small', 'synthetic_full', 'mix', 'mix_full'])

    parser.add_argument('--few_train_samples', type=int, default=None)
    parser.add_argument('--few_test_samples', type=int, default=None)
    parser.add_argument('--test_equations', action='store_true')
    parser.add_argument('--test_equations_math_speech_normalized', action='store_true')
    parser.add_argument('--test_equations_my_normalized', action='store_true')
    parser.add_argument('--test_equations_unnormalized', action='store_true')
    parser.add_argument('--test_sentences', action='store_true')
    parser.add_argument('--balanced_sampling', action='store_true', help='Enable balanced RU/EN sampling for multilingual training')
    args = parser.parse_args()


    with open(args.config, 'r') as config_file:
        config_dict = json.load(config_file)

    cfg = Config(**config_dict)

    torch.set_default_dtype(torch.bfloat16)

    tokenizer = AutoTokenizer.from_pretrained(cfg.model_ckpt, padding_side="left")
    model = AutoModelForCausalLM.from_pretrained(cfg.model_ckpt, attn_implementation='flash_attention_2', torch_dtype=torch.bfloat16)
    # model = AutoModelForCausalLM.from_pretrained("ckpts/asr-sentence/version_24/tuned-model")
    model_config = model.config

    if hasattr(cfg, 'lora_r') and cfg.lora_r is not None:
        from peft import LoraConfig, get_peft_model
        lora_config = LoraConfig(
            r=cfg.lora_r,
            lora_alpha=cfg.lora_alpha,
            # target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "down_proj", "up_proj"],
            target_modules=cfg.target_modules,
        )

        model = get_peft_model(model, lora_config)
        print("model", model)
    elif hasattr(cfg, 'unfreeze_head_and_last_layer') and cfg.unfreeze_head_and_last_layer:
        for p in model.parameters():
            p.requires_grad = False
        for p in model.lm_head.parameters():
            p.requires_grad = True
        for p in model.model.layers[-2:].parameters():
            p.requires_grad = True

    print("Trainable params:", sum(p.numel() for p in model.parameters() if p.requires_grad))

    ### Work with data
    collate_function = get_collate_function(tokenizer, cfg.model_ckpt)

    train_dataset_split = args.dataset_split
    test_dataset_split = args.dataset_split

    train_dataset = datasets.load_dataset('marsianin500/Speech2Latex', split=f'{args.dataset_split}_train', num_proc=32)
    test_dataset = datasets.load_dataset('marsianin500/Speech2Latex', split=f'{args.dataset_split}_test', num_proc=32)

    pron_column_name = 'whisper_text'
    latex_column_name = args.latex_column_name

    columns_to_keep = {pron_column_name, latex_column_name, 'is_tts', 'language'}
    if args.transcribation_column_name is not None:
        columns_to_keep.add(args.transcribation_column_name)

    train_dataset = train_dataset.remove_columns(set(train_dataset.column_names) - columns_to_keep)
    test_dataset = test_dataset.remove_columns(set(test_dataset.column_names) - columns_to_keep)

    if 'full' in args.data_type:
        big_synthetic_dataset = datasets.Dataset.load_from_disk('../Data/mathbridge/MathBridge_train_cleaned_normalized_train_dataset/')
        big_synthetic_dataset = big_synthetic_dataset.add_column('is_tts', [1] * len(big_synthetic_dataset))
        big_synthetic_dataset = big_synthetic_dataset.add_column('language', ['eng'] * len(big_synthetic_dataset))

        big_synthetic_dataset = big_synthetic_dataset.remove_columns(set(big_synthetic_dataset.column_names) - columns_to_keep)

        print("Adding synthetic dataset to train dataset")
        print("Train dataset size", len(train_dataset))
        print("Synthetic dataset size", len(big_synthetic_dataset))

        train_dataset = datasets.concatenate_datasets([train_dataset, big_synthetic_dataset])
        print("Concatenated dataset size", len(train_dataset))

    def filter_by_language_and_data_type(item):
        if args.language != 'multilingual' and item['language'] != args.language:
            return False

        if args.data_type != 'mix':
            if 'synthetic' in args.data_type and item['is_tts'] == 0:
                return False
            elif args.data_type == 'human' and item['is_tts'] == 1:
                return False

        return True

    if args.few_train_samples is not None:
        train_dataset = train_dataset.select(range(args.few_train_samples))

    train_dataset = train_dataset.filter(filter_by_language_and_data_type)

    print("Train dataset size", len(train_dataset))
    print("Test dataset size", len(test_dataset))

    # Prepare optional balanced RU/EN sampler for multilingual training
    balanced_sampler = None
    if args.balanced_sampling:
        if args.language != 'multilingual':
            print("Warning: --balanced_sampling is only applicable with --language multilingual; ignoring.")
        else:
            langs = train_dataset['language']
            num_ru = sum(1 for l in langs if l == 'ru')
            num_eng = sum(1 for l in langs if l == 'eng')
            if num_ru > 0 and num_eng > 0:
                # Inverse-frequency weights to balance classes
                weights = [
                    (1.0 / num_ru) if l == 'ru' else ((1.0 / num_eng) if l == 'eng' else 0.0)
                    for l in langs
                ]
                balanced_sampler = torch.utils.data.WeightedRandomSampler(
                    weights=weights,
                    num_samples=len(langs),
                    replacement=True,
                )
                print("Balanced RU/EN sampling enabled for training.")
            else:
                print("Warning: --balanced_sampling requested but both RU and ENG are not present; using default sampling.")

    train_dataset = ASRDataset(train_dataset, pron_column_name=pron_column_name, latex_column_name=latex_column_name, transcribation_column_name=args.transcribation_column_name)
    train_loader = get_dataloader(train_dataset, cfg.batch_size, collate_function, cfg.num_workers, train=True, sampler=balanced_sampler)

    module = Model_pl(cfg, len(train_loader), model, model_config, tokenizer)

    random_chars = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    csv_logger = CSVLogger(save_dir=f"ckpts/{cfg.exp_name}/{args.dataset_split}_{args.latex_column_name}_{args.language}_{args.data_type}_{random_chars}")
    os.makedirs(csv_logger.save_dir, exist_ok=True)

    print("output dir", csv_logger.save_dir)

    trainer = pl.Trainer(
        max_epochs=cfg.n_epochs,
        logger=csv_logger,
        enable_checkpointing=False,
        # val_check_interval=0.2,
        # limit_train_batches=1,
    )

    trainer.fit(
        model=module,
        train_dataloaders=train_loader,
    )

    module.eval()
    module.to('cuda')

    if args.language != 'multilingual':
        # If there was no language in training split, it can't be processed
        test_dataset = test_dataset.filter(lambda x: x['language'] == args.language)

    if args.few_test_samples is not None:
        test_dataset = test_dataset.select(range(args.few_test_samples))

    # Compute Metrics
    results_save_dir = csv_logger.save_dir

    outputs = test(
        model,
        tokenizer,
        test_dataset,
        model_name=cfg.model_ckpt,
        latex_column_name=latex_column_name,
    )

    evaluation_df = pd.DataFrame({**outputs, 'is_tts': test_dataset['is_tts']})

    evaluation_df.to_csv(os.path.join(results_save_dir, 'evaluation_generations.csv'), index=False)

    evaluation_df_mix = evaluation_df.copy()
    evaluation_df_artificial = evaluation_df[ evaluation_df['is_tts'] == 1 ].copy()
    evaluation_df_humans = evaluation_df[ evaluation_df['is_tts'] == 0 ].copy()

    # Mix metrics
    metrics_splits = [
        (evaluation_df_artificial, 'artificial'),
        (evaluation_df_humans, 'humans'),
        (evaluation_df_mix, 'mix'),
    ]

    for evaluation_df, test_split in metrics_splits:
        print(f"Computing metrics for {test_split}")

        in_context_metrics = LatexInContextMetrics()
        metrics_values = in_context_metrics.compute_all(evaluation_df['latex_pred'].values.tolist(), evaluation_df['latex_true'].values.tolist(), compute_text_only=(args.dataset_split == 'sentences'))
        in_context_metrics.dump(metrics_values)

        output_file_path = os.path.join(results_save_dir, f'{test_split}_metrics.json')
        with open(output_file_path, 'w') as f:
            json.dump(metrics_values, f)
            print(f"Metrics for {test_split} saved to {output_file_path}")


