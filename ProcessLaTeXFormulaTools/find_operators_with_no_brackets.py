# -*- encoding: utf-8 -*-
# @Author: SWHL
# @Contact: liekkaskono@163.com
from process_formula import NormalizeFormula
from process_formula.normalize_formulas import latex_math_commands

normlizer = NormalizeFormula()

no_brackets_operators = []

for operator in latex_math_commands:
    print(operator)

    latex_in = f" {operator} x + y "

    normalized_out = normlizer(latex_in)[0]

    print("latex_in", latex_in)
    print("normalized_out", normalized_out)

    if '{' not in normalized_out:
        no_brackets_operators.append(operator)

print(no_brackets_operators)