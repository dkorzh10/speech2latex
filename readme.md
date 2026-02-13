# Speech2Latex

# ProcessLaTeXFormulaTools

In `./ProcessLaTeXFormulaTools` there is code for latex normalization.

And main python code `ProcessLaTeXFormulaTools/process_formula/normalize_formulas.py`

```python
from ProcessLaTeXFormulaTools.process_formula import NormalizeFormula

norm = NormalizeFormula(check_node=False)

print(norm(" \sum_i^n i ")) # [ '\\sum_{i}^{n}i' ]
```


## Gemma for Speech2LaTeX

To run this code, create a copy of conda environment from `envs/multimodal/gemma_env.yml` file and activate it.

```shell
conda env create -f envs/multimodal/gemma_env.yml
conda activate gemma_s2l
```

If you encounter problems with PyTorch installation, install it using the following command:
```shell
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
```

Open Gemma directory `Multimodal/Gemma`.
This directory contains code for Gemma 3n fine-tuning for Speech2LaTeX task.

Create `train.csv` and `test.csv` files with `audio_path` and `formula_normalized` columns.
And run scripts:

```shell
python gemma_ft.py
python gemma_inf.py
```

Supports multi GPU training with `torchrun`:
```shell
torchrun --nproc_per_node="3" gemma_ft.py
```

## SALMONN for Speech2LaTeX

To run this code, create a copy of conda environment from `envs/multimodal/salmonn_env.yml` file and activate it.

```shell
conda env create -f envs/multimodal/salmonn_env.yml
conda activate salmonn_s2l
```

If you encounter problems with PyTorch installation, install it using the following command:
```shell
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
```

Open SALMONN directory `Multimodal/Salmonn/SALMONN`.
This directory contains code for SALMONN fine-tuning for Speech2LaTeX task.

You need to download checkpoints for model from original SALMONN repository to the `checkpoints` folder.
You can look at the example for names in `Multimodal/Salmonn/SALMONN/configs/config.yaml`.

Create `train.csv` and `test.csv` files with `audio_path` and `formula_normalized` columns.
Convert .csv to .json with `convert_csv_to_json_annot.py`
```shell
python convert_csv_to_json_annot.py
```

You can run training with:
```shell
python train.py --cfg-path configs/config.yaml
```
Or, if you want to run multi GPU training:
```shell
torchrun \
  --nproc_per_node=3 \
  --master_port=29700 \
  train.py \
  --cfg-path configs/config.yaml
```

For ineference run:
```shell
python inference.py \
  --cfg-path "./configs/decode_config.yaml" \
  --test_table "test.csv"
```

## Install dependencies for formula normalization

```
pip install -r requirements.txt
```


## ASRPostCorrection

### Training

```
cd ASRPostCorrection
PYTHONPATH=. python -m pdb -c continue train_qwen.py --config ./config-qwen2.5-in_context_training.json --train_df ../Data/latex_in_context_tts/latex_in_context_tts_v2_train.csv --val_df ../Data/latex_in_context_tts/latex_in_context_tts_v2_test.csv
```

### Testing trained model

```
cd ASRPostCorrection
python test_qwen.py --cuda 0 --test_file_csv ../Data/latex_in_context_tts/latex_in_context_tts_v2_test.csv --batch_size 20 --ckpt ./ckpts/tts-in-context/version_9/
```

### Evaluation

Its also possible to compute metrics from file without model.

Example usage:
```python
from s2l.eval import LatexInContextMetrics
in_context_metrics = LatexInContextMetrics()
metrics_values = in_context_metrics.compute_all(outputs['latex_pred'], outputs['latex_true'])
in_context_metrics.dump(metrics_values)
```

Example CLI-usage:
```
python src/s2l/eval.py --csv-data ./Data/latex_in_context_tts/latex_in_context_tts_v2_train.csv --pred-column model_prediction --target-column target_text
```

## Pronunciation generation
To generate pronunciation with xTTS v2 model, you can create an environment with `envs/tts/tts_env.yml`
```shell
conda env create -f envs/tts/tts_env.yml
conda activate tts_s2l
```
Then create an .csv or .jsonl files with `id`, `pronunciation` and `language` columns.
Set `path` and `output_dir` in `EngTTS/tts.py` and run the script:
```shell
python EngTTS/tts.py
```