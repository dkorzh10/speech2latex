# -*- encoding: utf-8 -*-
# @Author: SWHL
# @Contact: liekkaskono@163.com
from process_formula import NormalizeFormula
from tqdm.auto import tqdm

normlizer = NormalizeFormula()


math_str = [
    ('in 58', 'in\\\\58'),

    ('\\sqrt T', '\\sqrt{T}'),
    ('i\\sqrt 2 \\sqrt {2 + 3}', 'i\\sqrt{2}\\sqrt{2+3}'),

    ('\\ , \\ , \\=\\ , \\ ,', '\\,\\,\\=\\,\\,'),

    ('\\ \\rm', '\\ \\mathrm{}'),
    ("\\underset { \\xi\\in \\Xi^0 } { \\max } \\ : f ( \\xi ) ", "\\max_{\\xi\\in\\Xi^{0}}\ \\\\:\\\\f(\\xi) "),

    ('r\ ! \ ! =\ ! \ ! 1000', 'r\\!\\!=\\!\\!\\\\1000'),

    ('=1061~days and', '=1061~\\\\days\\\\and'),
    ('0.5079 - 0.1258 i ( 0.06\\ % , 0.16\\ % )', '0.5079-0.1258i(0.06\\%,0.16\\%)'),

    ('87.73\\ %', '87.73\\%'),
    ('2 \\ , \\rm{}', '2\\,\\mathrm{}'),
    ('4.3 \\% /5.7 \\%', '4.3\\%/5.7\\%'),

    ('h \\in \\ { 1 , \\ldots , n\\ } , k \\geq K', 'h\in{1,\\ldots,n},k\\geq\\\\K'),
    ('\\text { \\emph { Recall } } =TP / ( TP+FN ) ', '\\text{\\emph{Recall}}=TP/(TP+FN)'),

    ('x \sim 19.6-21.1', 'x\sim\\\\19.6-21.1'),
    ('\\emph { \\text { FFNN } }', '\\emph{\\text{FFNN}}'),
    ('\\bigl\langle x \\big| \hat { f } \\big| y\\bigr\\rangle', '\\langle\\\\x|\\hat{f}|y\\rangle'),

    ('\Delta z\sim1', '\Delta\\\\z\sim\\\\1'),
    ('1000', '1000'),
    ('\\nu t', '\\nu\\\\t'),
    # TODO numbers detokenization checkout!
    ('\\hskip 5mm', '\\hspace{5mm}'),
    ('\\left\\langle x\\right\\rangle', '\\left\\langle\\\\x\\right\\rangle'),
    ("\\sum_i^n i = \\frac{n(n+1)}{2}", "\\sum_{i}^{n}i=\\frac{n(n+1)}{2}"),
    ('\lim_{x\\to\\\\0} \\frac{1}{x} = \infty', '\\lim_{x\\to\\\\0}\\frac{1}{x}=\infty'),
    ('x\\to\\\\0', 'x\\to\\\\0'),
    ('\\textrm { PXP }', '\\textrm{PXP}'),
    ('ball~wrt', 'ball~\\\\wrt'),
    ('\\log p', '\\log\\\\p'),
    ('\\dots', '\\dots'),
    ('\\notin', '\\notin'),
    ('x \\notin T', 'x\\notin\\\\T'),
    ('T_ { \epsilon }', 'T_{\epsilon}'),
    ('tractrix', 'tractrix'),
    ('\\text { tractrix }', '\\text{tractrix}'),
    ('\mathcal { F }', '\mathcal\\\\F'),

    # Bad sample
    # ('\\Phi_r ( \\underline\\ X )', '\\Phi_r(\\underline{X})'),
]

# math_str = math_str[:1]

errors = 0

for latex_in, expected_output in tqdm(math_str):
    normalized_out = normlizer(latex_in)[0]
    # print("normalized_out", normalized_out)
    if normalized_out.strip() != expected_output.strip():
        errors += 1
        print(f"expected_output: {expected_output}")
        print(f"normalized_out:  {normalized_out}")
        print("-"*10)

print(f"errors {errors}")