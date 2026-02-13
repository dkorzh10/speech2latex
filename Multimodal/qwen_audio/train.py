import string
import random
import argparse
import json
import os
import torch
import torch.nn as nn
import numpy as np
import pytorch_lightning as pl
from s2l.eval import LatexInContextMetrics


import datasets
from datasets import Audio

from tqdm import tqdm
from peft import LoraConfig, get_peft_model, TaskType
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoProcessor, Qwen2AudioForConditionalGeneration
from transformers.optimization import Adafactor, AdafactorSchedule, get_cosine_schedule_with_warmup, get_linear_schedule_with_warmup
from torch.utils.data import DataLoader, Dataset
from pytorch_lightning.loggers import CSVLogger
from qwen_audio_data_collator import DataCollatorForQwen2Audio

from evaluate_qwen_audio import evaluate

import pandas as pd


class Config:
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            if isinstance(v, dict):
                setattr(self, k, Config(**v))
            else:
                setattr(self, k, v)

    def __str__(self):
        return '\n'.join(f'{key}: {value}' for key, value in self.__dict__.items())

    def __repr__(self):
        return self.__str__()

def freeze(model):
    for p in model.parameters():
        p.requires_grad_(False)

def unfreeze(model):
    for p in model.parameters():
        p.requires_grad_(True)



class Model_pl(pl.LightningModule):
    def __init__(self, cfg, model, train_dataset, collate_function, tokenizer):
        super().__init__()
        self.cfg = cfg
        self.model = model

        self.n_embeddings = model.config.vocab_size
        # self.loss_fct = nn.CrossEntropyLoss(reduction="none", ignore_index=tokenizer.pad_token_id)
        self.loss_fct = nn.CrossEntropyLoss(reduction="none")
        self.train_dataset = train_dataset
        self.collate_function = collate_function
        self.n_iters = len(self.train_dataloader())
        self.save_hyperparameters('cfg')
        self.tokenizer = tokenizer

    def configure_optimizers(self):

        optimizer = torch.optim.AdamW([p for p in self.model.parameters() if p.requires_grad], lr=self.cfg.learning_rate, weight_decay=0.05, betas=(0.9, 0.999), )
        scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=300, num_training_steps=self.n_iters)
        return {
            'optimizer': optimizer,
            'lr_scheduler': {
                'scheduler': scheduler,
                'interval': 'step',
                'frequency': 1
            },
        }

    def on_train_epoch_end(self):
        # torch.save(self.model.lm_head.state_dict() ,f"ckpts/{self.cfg.exp_name}/lm_head_state_dict.pth")
        self.model.save_pretrained(f"{self.logger.save_dir}/tuned-model")
        self.tokenizer.save_pretrained(f"{self.logger.save_dir}/tokenizer")

    def training_step(self, batch, batch_idx):
        batch = batch.to(self.device)

        with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
            outputs = self.model(**batch)

        loss = outputs.loss

        self.log("my_loss", loss, on_step=True, on_epoch=True, prog_bar=True, sync_dist=True)

        return loss


    def train_dataloader(self):
        print("Batch size:", self.cfg.batch_size)
        return DataLoader(self.train_dataset, batch_size=self.cfg.batch_size, collate_fn=self.collate_function, num_workers = self.cfg.num_workers, shuffle = True)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='./configs/config.json')
    parser.add_argument('--few_test_samples', type=int, default=None)
    parser.add_argument('--few_train_samples', type=int, default=None)
    parser.add_argument('--dataset_split', type=str, required=True, choices=['sentences', 'equations'])
    parser.add_argument('--latex_column_name', type=str, required=True, choices=['sentence', 'sentence_normalized'])
    parser.add_argument('--language', type=str, required=True, choices=['ru', 'eng', 'multilingual'])
    parser.add_argument('--data_type', type=str, required=True, choices=['synthetic_small', 'human', 'mix', 'mix_full'])

    args = parser.parse_args()

    dataset_split = args.dataset_split

    with open(args.config, 'r') as config_file:
        config_dict = json.load(config_file)
    cfg = Config(**config_dict)
    # df = pd.read_csv(cfg.df_path, index_col=False)dummy_ex

    processor = AutoProcessor.from_pretrained(cfg.model_ckpt, trust_remote_code=True)


    s2l_dataset = datasets.load_dataset('marsianin500/Speech2Latex', split=f'{dataset_split}_train', num_proc=32)

    if args.few_train_samples is not None:
        s2l_dataset = s2l_dataset.select(range(args.few_train_samples))

    print("len dataset", len(s2l_dataset))

    columns_to_keep = ['audio_path', args.latex_column_name, 'is_tts', 'language']
    s2l_dataset = s2l_dataset.remove_columns(list(set(s2l_dataset.column_names) - set(columns_to_keep)))

    s2l_dataset = s2l_dataset.cast_column('audio_path', Audio(sampling_rate=processor.feature_extractor.sampling_rate))

    if 'full' in args.data_type:
        big_synthetic_dataset = datasets.Dataset.load_from_disk('../../Data/mathbridge/MathBridge_train_cleaned_normalized_train_dataset/')
        big_synthetic_dataset = big_synthetic_dataset.add_column('is_tts', [1] * len(big_synthetic_dataset))
        big_synthetic_dataset = big_synthetic_dataset.add_column('language', ['eng'] * len(big_synthetic_dataset))

        big_synthetic_dataset = big_synthetic_dataset.remove_columns(set(big_synthetic_dataset.column_names) - set(columns_to_keep))

        print("Adding synthetic dataset to train dataset")
        print("Train dataset size", len(s2l_dataset))
        print("Synthetic dataset size", len(big_synthetic_dataset))

        train_dataset = datasets.concatenate_datasets([s2l_dataset, big_synthetic_dataset])
        print("Concatenated dataset size", len(train_dataset))

    def filter_by_language_and_data_type(item):
        if args.language != 'multilingual' and item['language'] != args.language:
            return False

        if 'mix' not in args.data_type:
            if args.data_type == 'synthetic_small' and item['is_tts'] == 0:
                return False
            elif args.data_type == 'human' and item['is_tts'] == 1:
                return False

        return True


    if args.data_type != 'mix_full':
        s2l_dataset = s2l_dataset.filter(filter_by_language_and_data_type)

    torch.manual_seed(1234)

    model = Qwen2AudioForConditionalGeneration.from_pretrained(cfg.model_ckpt, device_map="cpu", trust_remote_code=True, torch_dtype=torch.bfloat16)

    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        # target_modules=['k_proj', 'v_proj', 'q_proj', 'o_proj']
        # target_modules=['k_proj', 'v_proj', 'q_proj', 'o_proj', 'out_proj', 'gate_proj', 'up_proj', 'down_proj'],
        target_modules=["k_proj","down_proj","gate_proj","up_proj","q_proj","out_proj","lm_head","v_proj","linear","o_proj"],
        # exclude_modules=['audio_tower'],
        # exclude_modules=r'.*audio_tower.*',
        inference_mode=False,
        r=cfg.lora_rank,
        lora_alpha=cfg.lora_alpha,
        lora_dropout=0.1,
        bias="none",
    )
    if cfg.n_epochs != 0:
        model = get_peft_model(model, peft_config)
        print("model", model)
    # model = torch.compile(model, dynamic=True, )

    # print("Unfreese multi_modal_projector")
    # for p in model.base_model.multi_modal_projector.parameters():
    #     p.requires_grad_(True)

    print("Num trainable parameters:", sum(p.numel() for p in model.parameters() if p.requires_grad))

    random_chars = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    logger = CSVLogger(save_dir=f"ckpts/{cfg.exp_name}/{args.dataset_split}_{args.latex_column_name}_{args.language}_{args.data_type}_{random_chars}")
    os.makedirs(logger.save_dir, exist_ok=True)
    print("Logger save dir:", logger.save_dir)

    train_dataset = s2l_dataset
    collate_function = DataCollatorForQwen2Audio(processor, sampling_rate=processor.feature_extractor.sampling_rate, latex_column_name=args.latex_column_name)

    module = Model_pl(cfg, model, train_dataset, collate_function, processor.tokenizer)
    trainer = pl.Trainer(
        max_epochs=cfg.n_epochs,
        logger = logger,
        accumulate_grad_batches = cfg.grad_accum,
        enable_checkpointing=False,
        gradient_clip_val=1.0,
    )

    if cfg.n_epochs != 0:
        trainer.fit(module)

    # Evaluation
    test_dataset = datasets.load_dataset('marsianin500/Speech2Latex', split=f'{dataset_split}_test', num_proc=32)

    pron_column_name = 'whisper_text'
    latex_column_name = args.latex_column_name

    columns_to_keep = {pron_column_name, latex_column_name, 'is_tts', 'language', 'audio_path'}

    test_dataset = test_dataset.remove_columns(set(test_dataset.column_names) - columns_to_keep)

    if args.language != 'multilingual':
        test_dataset = test_dataset.filter(lambda x: x['language'] == 'eng')

    if args.few_test_samples is not None:
        test_dataset = test_dataset.select(range(args.few_test_samples))

    results_save_dir = os.path.join(logger.save_dir, 'results')
    os.makedirs(results_save_dir, exist_ok=True)

    model = model.to('cuda')

    outputs = evaluate(
        model,
        processor,
        test_dataset,
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
        metrics_values = in_context_metrics.compute_all(evaluation_df['latex_pred'].values.tolist(), evaluation_df['latex_true'].values.tolist(), compute_text_only=(dataset_split == 'sentences'))
        in_context_metrics.dump(metrics_values)

        output_file_path = os.path.join(results_save_dir, f'{test_split}_metrics.json')
        with open(output_file_path, 'w') as f:
            json.dump(metrics_values, f)
            print(f"Metrics for {test_split} saved to {output_file_path}")


