import json
import sys
import pandas as pd
# from s2l.eval import LatexInContextMetrics

import datasets

# python -m pdb -c continue eval_mathspeech_s2l_eq_test.py ./s2l_equations_test_full_normalized_normalized.csv

if __name__ == "__main__":

    file_path = sys.argv[1]

    math_speech_bench = False

    latex_true_column = 'LaTeX'
    latex_pred_column = 'MathSpeech_LaTeX_result'

    dataset_orig = datasets.load_dataset('marsianin500/Speech2Latex', split='equations_test', num_proc=8)

    dataset_orig_is_tts = dataset_orig['is_tts']
    dataset_orig_language = dataset_orig['language']

    df = pd.read_csv(file_path)

    df['is_tts'] = dataset_orig_is_tts
    df['language'] = dataset_orig_language

    joined_csv = file_path.replace('.csv', '_is_tts_lang.csv')
    print("joined_csv", joined_csv)
    breakpoint()
    df.to_csv(joined_csv)
    breakpoint()

    # if not math_speech_bench:
    df[latex_pred_column] = df[latex_pred_column].apply(lambda x: x.replace(' ', '').replace('\displaystyle', '').replace('\operatorname', ''))
    df[latex_true_column] = df[latex_true_column].apply(lambda x: x.replace(' ', '').replace('\displaystyle', '').replace('\operatorname', ''))
    # else:
    #     df[latex_true_column] = df[latex_true_column].apply(lambda x: f"${x}$")
    #     df[latex_pred_column] = df[latex_pred_column].apply(lambda x: x.replace(' ', '').replace('\displaystyle', '').replace('\operatorname', ''))
    #     df[latex_true_column] = df[latex_true_column].apply(lambda x: x.replace(' ', '').replace('\displaystyle', '').replace('\operatorname', ''))

    predicted_latex = []

    for x, y in zip(df[latex_pred_column], df[latex_true_column]):
        x = x.removesuffix('$').removeprefix('$')
        predicted_latex.append(x)
        print(x)
        print(y)
        print("-"*30)

    df[latex_pred_column] = predicted_latex

    df = df[ df['language'] == 'eng' ]

    df_human = df[ df['is_tts'] == 0 ]
    df_tts = df[ df['is_tts'] == 1 ]
    df_mix = df

    print("len df_mix  ", len(df_mix))
    print("len df_human", len(df_human))
    print("len df_tts  ", len(df_tts))


    in_context_metrics = LatexInContextMetrics()
    metrics_values = in_context_metrics.compute_all(df_mix[latex_pred_column].values.tolist(), df_mix[latex_true_column].values.tolist(), compute_text_only=False, compute_formulas_only=False)

    print("\n\nMix Metrics")
    in_context_metrics.dump(metrics_values)
    with open("mix_metrics.json", 'w') as f:
        json.dump(metrics_values, f)

    in_context_metrics = LatexInContextMetrics()
    metrics_values = in_context_metrics.compute_all(df_human[latex_pred_column].values.tolist(), df_human[latex_true_column].values.tolist(), compute_text_only=False, compute_formulas_only=False)
    print("\n\nHuman Metrics")
    in_context_metrics.dump(metrics_values)
    with open("humans_metrics.json", 'w') as f:
        json.dump(metrics_values, f)

    in_context_metrics = LatexInContextMetrics()
    metrics_values = in_context_metrics.compute_all(df_tts[latex_pred_column].values.tolist(), df_tts[latex_true_column].values.tolist(), compute_text_only=False, compute_formulas_only=False)
    print("\n\nTTS Metrics")
    in_context_metrics.dump(metrics_values)
    with open("artificial_metrics.json", 'w') as f:
        json.dump(metrics_values, f)
