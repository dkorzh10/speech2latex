from typing import List
from tqdm import tqdm
import pandas as pd

import evaluate

from process_formula import NormalizeFormula

class LatexInContextMetrics:

    """
    Computes in context metrics values

    Example usage:
    ```
    from s2l.eval import LatexInContextMetrics
    in_context_metrics = LatexInContextMetrics()
    metrics_values = in_context_metrics.compute_all(outputs['latex_pred'], outputs['latex_true'])
    in_context_metrics.dump(metrics_values)
    ```
    """

    def __init__(self):

        self.wer = evaluate.load('wer')
        self.cer = evaluate.load('cer')

        self.wer_lower = evaluate.load('wer')
        self.cer_lower = evaluate.load('cer')

        self.bleu = evaluate.load('bleu')
        self.meteor = evaluate.load('meteor')
        self.sacrebleu = evaluate.load("sacrebleu")
        self.rouge1 = evaluate.load("rouge")
        self.chrf = evaluate.load("chrf")

    def compute_tex_bleu(self, predictions, references):

        # Late import for faster startup
        # This library initializes global variables
        from tex_bleu import texbleu

        all_scores = []

        for pred, ref in zip(predictions, references):
        # for pred, ref in tqdm(zip(predictions, references)):
            if pred == '':
                all_scores.append(0)
                continue
            all_scores.append(texbleu(ref, pred))

        return sum(all_scores) / len(all_scores)

    def compute(self, predictions, references):

        predictions_lower = [ x.lower() for x in predictions ]
        references_lower = [ x.lower() for x in references ]

        result = dict()
        try:
            result['wer'] = self.wer.compute(predictions=predictions, references=references)
            result['wer_lower'] = self.wer_lower.compute(predictions=predictions_lower, references=references_lower)
        except Exception as e:
            print(f"Error computing wer: {e}")
            result['wer'] = -1
            result['wer_lower'] = -1

        result['cer'] = self.cer.compute(predictions=predictions, references=references)
        result['cer_lower'] = self.cer_lower.compute(predictions=predictions_lower, references=references_lower)
        result['bleu'] = self.bleu.compute(predictions=predictions, references=references)['bleu']
        result['sacrebleu'] = self.sacrebleu.compute(predictions=predictions, references=references)['score'] / 100
        result['meteor'] = self.meteor.compute(predictions=predictions, references=references)['meteor']
        result['rouge1'] = self.rouge1.compute(predictions=predictions, references=references)['rouge1']
        result['chrf'] = self.chrf.compute(predictions=predictions, references=references)['score'] / 100
        result['chrfpp'] = self.chrf.compute(predictions=predictions, references=references, word_order=2)['score'] / 100

        result['tex_bleu'] = self.compute_tex_bleu(predictions, references)

        return result

    def compute_formulas_only(self, prediction, references, compile_with_katex=False):
        """
        Extracts all formulas from predictions and references,
        concatenate all formulas. And computes metrics for formulas-only string.
        """
        prediction_formulas_only, formulas_content_list = self.extract_in_context_formulas_bulk(prediction)
        references_formulas_only, _ = self.extract_in_context_formulas_bulk(references)
        metrics = self.compute(prediction_formulas_only, references_formulas_only)

        if compile_with_katex:
            normlizer = NormalizeFormula()
            normalized_formulas = normlizer(formulas_content_list)
            invalid_count = sum(1 for x in normalized_formulas if x == '')

            metrics['invalid_latex'] = invalid_count / len(formulas_content_list)

        return metrics

    def extract_in_context_formulas_bulk(self, text_lines: List[str]):
        result = []
        formulas_content_list = []
        for text_line in text_lines:
            formulas_content = text_line.split('$')
            if len(formulas_content) < 2:
                formulas_content = [ '' ]
            else:
                formulas_content = formulas_content[1::2]

            formulas_content_list.extend(formulas_content)
            result.append("$" + "$ $".join(formulas_content) + "$")
        
        return result, formulas_content_list

    def extract_in_context_text_bulk(self, text_lines: List[str]):
        result = []
        for text_line in text_lines:
            formulas_content = text_line.split('$')
            if len(formulas_content) < 2:
                formulas_content = [ text_line ]
            else:
                formulas_content = formulas_content[0::2]

            result.append(" ".join(formulas_content))

        return result


    def compute_text_only(self, prediction, references):
        """
        Extracts all formulas from predictions and references,
        concatenate all formulas. And computes metrics for formulas-only string.
        """
        prediction_text_only = self.extract_in_context_text_bulk(prediction)
        references_text_only = self.extract_in_context_text_bulk(references)
        metrics = self.compute(prediction_text_only, references_text_only)

        return metrics

    def compute_all(self, prediction, references, compile_with_katex=False, compute_text_only=True, compute_formulas_only=True):
        
        if isinstance(prediction, pd.Series):
            prediction = prediction.values.tolist()
        if isinstance(references, pd.Series):
            references = references.values.tolist()

        metrics = self.compute(prediction, references)

        if compute_formulas_only:
            metrics_formulas_only = self.compute_formulas_only(prediction, references, compile_with_katex=compile_with_katex)
            for k, v in metrics_formulas_only.items():
                metrics['formulas_only_'+k] = v

        if compute_text_only:
            metrics_text_only = self.compute_text_only(prediction, references)
            for k, v in metrics_text_only.items():
                metrics['text_only_'+k] = v

        return metrics

    @classmethod
    def dump(self, metrics: dict):
        print("Metrics")
        print("                   Value \tValue (formulas only) \tValue (text only)")
        print("tex_bleu           {value:.4f}\t{value_furmulas:.4f}\t\t{value_text:.4f}".format(value=metrics['tex_bleu'],               value_furmulas=metrics.get('formulas_only_tex_bleu', 0.0),       value_text=metrics.get('text_only_tex_bleu', 0.0)))
        print("wer (l)            {value:.4f}\t{value_furmulas:.4f}\t\t{value_text:.4f}".format(value=metrics['wer'],                    value_furmulas=metrics.get('formulas_only_wer', 0.0),            value_text=metrics.get('text_only_wer', 0.0)))
        print("cer (l)            {value:.4f}\t{value_furmulas:.4f}\t\t{value_text:.4f}".format(value=metrics['cer'],                    value_furmulas=metrics.get('formulas_only_cer', 0.0),            value_text=metrics.get('text_only_cer', 0.0)))
        print("wer_lower (l)      {value:.4f}\t{value_furmulas:.4f}\t\t{value_text:.4f}".format(value=metrics['wer_lower'],              value_furmulas=metrics.get('formulas_only_wer_lower', 0.0),      value_text=metrics.get('text_only_wer_lower', 0.0)))
        print("cer_lower (l)      {value:.4f}\t{value_furmulas:.4f}\t\t{value_text:.4f}".format(value=metrics['cer_lower'],              value_furmulas=metrics.get('formulas_only_cer_lower', 0.0),      value_text=metrics.get('text_only_cer_lower', 0.0)))
        print("bleu (h)           {value:.4f}\t{value_furmulas:.4f}\t\t{value_text:.4f}".format(value=metrics['bleu'],                   value_furmulas=metrics.get('formulas_only_bleu', 0.0),           value_text=metrics.get('text_only_bleu', 0.0)))
        print("sacrebleu (h)      {value:.4f}\t{value_furmulas:.4f}\t\t{value_text:.4f}".format(value=metrics['sacrebleu'],              value_furmulas=metrics.get('formulas_only_sacrebleu', 0.0),      value_text=metrics.get('text_only_sacrebleu', 0.0)))
        print("meteor (h)         {value:.4f}\t{value_furmulas:.4f}\t\t{value_text:.4f}".format(value=metrics['meteor'],                 value_furmulas=metrics.get('formulas_only_meteor', 0.0),         value_text=metrics.get('text_only_meteor', 0.0)))
        print("rouge1 (h)         {value:.4f}\t{value_furmulas:.4f}\t\t{value_text:.4f}".format(value=metrics['rouge1'],                 value_furmulas=metrics.get('formulas_only_rouge1', 0.0),         value_text=metrics.get('text_only_rouge1', 0.0)))
        print("chrf (h)           {value:.4f}\t{value_furmulas:.4f}\t\t{value_text:.4f}".format(value=metrics['chrf'],                   value_furmulas=metrics.get('formulas_only_chrf', 0.0),           value_text=metrics.get('text_only_chrf', 0.0)))
        print("chrfpp (h)         {value:.4f}\t{value_furmulas:.4f}\t\t{value_text:.4f}".format(value=metrics['chrfpp'],                 value_furmulas=metrics.get('formulas_only_chrfpp', 0.0),         value_text=metrics.get('text_only_chrfpp', 0.0)))
        print("invalid_latex (l)  {value:.4f}\t{value_furmulas:.4f}\t\t{value_text:.4f}".format(value=metrics.get('invalid_latex', 0.0), value_furmulas=metrics.get('formulas_only_invalid_latex', 0.0),  value_text=metrics.get('text_only_invalid_latex', 0.0)))

        print("\n")


if __name__ == "__main__":

    import argparse
    import pandas as pd

    parser = argparse.ArgumentParser(
        description="""
        Script evaluates metrics for S2L-sentences dataset.
        As prediction as target columns should contain inline
        latex formulas wrapped in `$ ... $`
        """
    )
    parser.add_argument('--csv-data', type=str, help="Path to csv file with predictions and targets", required=True)
    parser.add_argument('--pred-column', type=str, help="Column name of model predictions", required=True)
    parser.add_argument('--target-column', type=str, help="Column name of target", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.csv_data)

    prediction = df[args.pred_column]
    target = df[args.target_column]

    in_context_metrics = LatexInContextMetrics()
    metrics_values = in_context_metrics.compute_all(prediction, target)
    in_context_metrics.dump(metrics_values)
