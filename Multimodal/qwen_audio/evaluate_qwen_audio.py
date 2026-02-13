import argparse
import os
import json
from collections import defaultdict
from tqdm import tqdm


import torch
import datasets
from torch.utils.data import DataLoader

from transformers import AutoProcessor, Qwen2AudioForConditionalGeneration
from qwen_audio_data_collator import TestDataCollatorForQwen2Audio

from peft import PeftModel

@torch.no_grad()
def evaluate(
    model,
    processor,
    test_dataset,
    latex_column_name = 'sentence',
):
    # formulas normalization will be performed in batched_model_generation
    collate_function = TestDataCollatorForQwen2Audio(processor, sampling_rate=16000, latex_column_name=latex_column_name)

    batch_size = 8
    test_loader = DataLoader(test_dataset, batch_size=batch_size, collate_fn=collate_function, num_workers=0, shuffle=False)

    outputs = defaultdict(list)

    with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
    # if True:
        for batch in tqdm(test_loader):
            batch = batch.to('cuda')

            max_new_tokens = max(len(target_text) for target_text in batch['target_text'])

            generated_latex = model.generate(
                batch['input_ids'],
                attention_mask=batch['attention_mask'],
                input_features=batch['input_features'],
                feature_attention_mask=batch['feature_attention_mask'],
                max_new_tokens=max_new_tokens * 2,
                return_dict_in_generate=True,
            )
            generated_latex = generated_latex.sequences[:, batch['input_ids'].shape[1]:]

            generated_latex = processor.batch_decode(generated_latex, skip_special_tokens=True)
            target_text = batch['target_text']

            print('generated_latex', generated_latex[0])
            print('target_text', target_text[0])

            outputs['latex_pred'].extend(generated_latex)
            outputs['latex_true'].extend(target_text)

    return outputs


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--base_model', type=str, default='Qwen/Qwen2-Audio-7B-Instruct')
    parser.add_argument('--checkpoint_path', type=str, required=True)
    parser.add_argument('--dataset_split', type=str, choices=['sentences', 'equations'], required=True)
    parser.add_argument('--language', type=str, choices=['eng', 'ru', 'multilingual'], required=True)
    parser.add_argument('--data_type', type=str, choices=['human', 'synthetic_small', 'mix'], required=True)
    parser.add_argument('--latex_column_name', type=str, choices=['sentence', 'sentence_normalized'], required=True)


    args = parser.parse_args()

    model_path = f'{args.checkpoint_path}/tuned-model'

    print("\n\nbase_model", args.base_model, "\n\n")
    processor = AutoProcessor.from_pretrained(args.base_model)
    model = Qwen2AudioForConditionalGeneration.from_pretrained(args.base_model, trust_remote_code=True, torch_dtype=torch.bfloat16)

    model = PeftModel.from_pretrained(model, model_path)
    model.to('cuda')

    test_dataset = datasets.load_dataset('marsianin500/Speech2Latex', split=f'{args.dataset_split}_test', num_proc=32)

    pron_column_name = 'whisper_text'
    latex_column_name = args.latex_column_name

    columns_to_keep = {pron_column_name, latex_column_name, 'is_tts', 'language', 'audio_path'}

    test_dataset = test_dataset.remove_columns(set(test_dataset.column_names) - columns_to_keep)

    if args.language != 'multilingual':
        test_dataset = test_dataset.filter(lambda x: x['language'] == args.language)

    test_dataset_artificial = test_dataset.filter(lambda x: x['is_tts'] == 1)
    test_dataset_humans = test_dataset.filter(lambda x: x['is_tts'] == 0)
    test_dataset_mix = test_dataset

    results_save_dir = os.path.join(args.checkpoint_path, 'results')
    os.makedirs(results_save_dir, exist_ok=True)

    test_splits = [
        (test_dataset_mix, 'mix'),
        # (test_dataset_artificial, 'artificial'),
        # (test_dataset_humans, 'humans'),
    ]

    model.to('cuda')

    for test_dataset, test_split in test_splits:
        metrics = evaluate(
            model,
            processor,
            test_dataset,
            latex_column_name=latex_column_name,
            # compute_text_only=(args.dataset_split == 'sentences'),
        )
        output_file_path = os.path.join(results_save_dir, f'{test_split}_metrics.json')
        with open(output_file_path, 'w') as f:
            json.dump(metrics, f)
            print(f"Metrics for {test_split} saved to {output_file_path}")
