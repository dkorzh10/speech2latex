import torch
from torch.utils.data import DataLoader, Dataset

from typing import Callable, List

import random

from chat_template_with_generation import CHAT_TEMPLATE_WITH_GENERATION, CHAT_TEMPLATE_WITH_GENERATION_LLAMA32
from process_formula import NormalizeFormula



class ASRDataset(Dataset):
    def __init__(self, dataset, pron_column_name='pron', latex_column_name='latex', transcribation_column_name=None):
        self.dataset = dataset

        self.pron_column_name = pron_column_name
        self.latex_column_name = latex_column_name
        self.transcribation_column_name = transcribation_column_name

    def __len__(self):
        return len(self.dataset)


    def __getitem__(self, idx):
        item = self.dataset[idx]
        result_item = {
            "pron": item[self.pron_column_name],
            "latex": item[self.latex_column_name],
        }
        if self.transcribation_column_name is not None:
            result_item[self.transcribation_column_name] = item[self.transcribation_column_name]
        return result_item

def get_collate_function(tokenizer, model_name, process_formulas=None, latex_column='latex', whisper_column='pron', transcribation_column_name=None):

    user_instructions_prefix = [
        # 'Translate  transcribation to LaTex formula: '
        'Please, give me LaTeX representation of the following formula. Formula pronunciation: '
    ]

    chat_template = CHAT_TEMPLATE_WITH_GENERATION
    if 'llama' in model_name.lower():
        chat_template = CHAT_TEMPLATE_WITH_GENERATION_LLAMA32
    
    def formulas_preprocessor(formulas_list):
        if process_formulas is not None:
            return process_formulas(formulas_list)
        return formulas_list
    
    def collate_fnc(dataset_items):
        
        all_chats = []
        all_chats_no_assistant_answer = []
        
        latex_processed = formulas_preprocessor([ item[latex_column] for item in dataset_items ])
        
        for i, dataset_item in enumerate(dataset_items):
            pronunciation = dataset_item[whisper_column]
            latex = latex_processed[i]

            user_instruction_prefix = random.choice(user_instructions_prefix)

            chat = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"{user_instruction_prefix}{pronunciation}"},
            ]

            if transcribation_column_name is None:
                chat.append({"role": "assistant", "content": f"{latex}"})
            else:
                transcribation = dataset_item[transcribation_column_name]
                chat.append({"role": "assistant", "content": f"Fixed transcribation: {transcribation}\nLaTex: {latex}"})
            
            all_chats.append(chat)
            all_chats_no_assistant_answer.append(chat[:2])

        output = tokenizer.apply_chat_template(
            all_chats,
            padding=True,
            tokenize=True,
            chat_template=chat_template,
            return_assistant_tokens_mask=True,
            return_dict=True,
            return_tensors='pt',
        )
        
        no_assistant_answer_output = tokenizer.apply_chat_template(
            all_chats_no_assistant_answer,
            padding=True,
            tokenize=True,
            chat_template=chat_template,
            return_assistant_tokens_mask=True,
            return_dict=True,
            return_tensors='pt',
            add_generation_prompt=True,
        )

        output['assistant_masks'] = torch.tensor(output['assistant_masks'])
        no_assistant_answer_output['assistant_masks'] = torch.tensor(no_assistant_answer_output['assistant_masks'])
        
        # merge generation dict with prefix
        for k, v in no_assistant_answer_output.items():
            output[f'generation_{k}'] = v

        return output

    return collate_fnc

def get_dataloader(dataset: Dataset,
                   batch_size: int,
                   collate_fn: Callable,
                   num_workers: int,
                   train: bool = False,
                   sampler=None) -> DataLoader:
    # If a sampler is provided, disable shuffle to satisfy DataLoader constraints
    effective_shuffle = (train and sampler is None)
    return DataLoader(
        dataset=dataset,
        batch_size=batch_size,
        collate_fn=collate_fn,
        num_workers=num_workers,
        shuffle=effective_shuffle,
        drop_last=train,
        pin_memory=True,
        sampler=sampler,
    )
