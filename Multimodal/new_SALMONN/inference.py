# Copyright (2024) Tsinghua University, Bytedance Ltd. and/or its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse

import torch
from transformers import WhisperFeatureExtractor

from config import Config
from models.salmonn import SALMONN
from utils import prepare_one_sample

import pandas as pd
# from collections import defaultdict

# import evaluate
import os
import time
import tqdm

import wave
from metrics import LatexInContextMetrics

def get_wav_duration(file_path):
    with wave.open(file_path, 'r') as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        duration = frames / float(rate)
    return duration

BASE_DIR = "/mnt/shared_ru.ml.SZ-2_000049/antispoofing_datasets/S2L_full_dataset"
parser = argparse.ArgumentParser()
parser.add_argument("--cfg-path", type=str, required=True, help='path to configuration file')
parser.add_argument("--device", type=str, default="cuda")
parser.add_argument(
    "--options",
    nargs="+",
    help="override some settings in the used config, the key-value pair "
    "in xxx=yyy format will be merged into config file (deprecate), "
    "change to --cfg-options instead.",
)

parser.add_argument("--test-table-path", type=str, required=True)
parser.add_argument(
    "--metrics-path",
    "--mertics-path",
    dest="metrics_path",
    type=str,
    default="metrics_out.xlsx",
    help="Where to write the metrics Excel file (--mertics-path is a deprecated alias)",
)
args = parser.parse_args()

def main(path, promt):

    cfg = Config(args)

    model = SALMONN.from_config(cfg.config.model)
    model.to(args.device)
    model.eval()

    wav_processor = WhisperFeatureExtractor.from_pretrained(cfg.config.model.whisper_path)

    df = pd.read_csv(path)

    dict_output = {
        "gt_latex":[],
        "pr_latex":[],
        "pron":[],
        "audio_path":[]
    }

    _times = []
    mega_time = time.time()
    for i, row in tqdm.tqdm(df.iterrows(), total=len(df)):
        start_time = time.time()
        try:
            wav_path = os.path.join(BASE_DIR, row["audio_path"])
            gt_latex = row["sentence_normalized"]
            pron = row["pronunciation"]
            
            samples = prepare_one_sample(wav_path, wav_processor)
            _prompt = [
                cfg.config.model.prompt_template.format("<Speech><SpeechHere></Speech> " + promt.strip())
            ]

            print(f"prompt: {_prompt}")

            predict_latex = ""
            with torch.cuda.amp.autocast(dtype=torch.float16):
                predict_latex = model.generate(samples, cfg.config.generate, prompts=_prompt)[0].replace("</s>", "").replace("<s>", "").strip()
            if predict_latex.startswith("$") and predict_latex.endswith("$") and len(predict_latex) > 1:
                predict_latex = predict_latex[1:-1].strip()

            dict_output["gt_latex"].append(gt_latex)
            dict_output["pr_latex"].append(predict_latex)
            dict_output["pron"].append(pron)
            dict_output["audio_path"].append(wav_path)

            if i % 10 == 0:
                print(f"ground truth: {gt_latex}. prediction: {predict_latex}")
        except Exception as e:
            print(e)
        _times.append(time.time() - start_time )

        # if i % 3 == 0:
        #     break
        
    dur = time.time() -  mega_time
    print(sum(_times),dur) 
    print(sum(_times)/dur)

    # pd.DataFrame(dict_output).to_csv(output_test_path,index=False)
    return dict_output["pr_latex"], dict_output["gt_latex"]

if __name__ == "__main__":
    # test_table_path = ""
    # output_metrics_path = ""
    prompt = "Recognize the speech and convert the content into text. Any mathematical expressions should be transcribed in LaTeX format."
    

    test_table_path = args.test_table_path
    output_metrics_path = args.metrics_path

    print("\nStart working")
    print("test table path",test_table_path)
    print("output metrics path",output_metrics_path)

    prediction, target = main(test_table_path, prompt)

    in_context_metrics = LatexInContextMetrics()
    metrics_values = in_context_metrics.compute_all(prediction, target)
    in_context_metrics.dump(metrics_values)
    
    df_metrics = in_context_metrics.dump_to_dataframe(metrics_values)
    df_metrics.to_excel(output_metrics_path, index = False)