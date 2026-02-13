# -*- encoding: utf-8 -*-
# @Author: SWHL
# @Contact: liekkaskono@163.com
import argparse
import re
import subprocess
from pathlib import Path
from typing import List, Sequence, Union

latex_math_commands = [
    # Greek letters
    "\\alpha", "\\beta", "\\gamma", "\\delta", "\\epsilon", "\\varepsilon", "\\zeta", "\\eta", "\\theta", "\\vartheta", "\\iota", "\\kappa",
    "\\lambda", "\\mu", "\\nu", "\\xi", "\\pi", "\\varpi", "\\rho", "\\varrho", "\\sigma", "\\varsigma", "\\tau", "\\upsilon", "\\phi", "\\varphi",
    "\\chi", "\\psi", "\\omega",
    "\\Gamma", "\\Delta", "\\Theta", "\\Lambda", "\\Xi", "\\Pi", "\\Sigma", "\\Upsilon", "\\Phi", "\\Psi", "\\Omega",

    # Binary operators
    "+", "-", "*", "/", "\\cdot", "\\times", "\\div", "\\pm", "\\mp", "\\cap", "\\cup", "\\sqcap", "\\sqcup",
    "\\vee", "\\wedge", "\\oplus", "\\ominus", "\\otimes", "\\oslash", "\\odot",

    # Relational operators
    "=", "\\ne", "\\neq", "<", ">", "\\leq", "\\geq", "\\ll", "\\gg", "\\approx", "\\cong", "\\sim", "\\simeq", "\\equiv", "\\propto",
    "\\prec", "\\succ", "\\subset", "\\supset", "\\subseteq", "\\supseteq", "\\nsubseteq", "\\nleq", "\\ngeq", "\\in", "\\ni", "\\notin",

    # Arrows
    "\\leftarrow", "\\rightarrow", "\\leftrightarrow", "\\Leftarrow", "\\Rightarrow", "\\Leftrightarrow",
    "\\uparrow", "\\downarrow", "\\updownarrow", "\\longleftarrow", "\\longrightarrow", "\\Longleftarrow",
    "\\Longrightarrow", "\\mapsto", "\\hookrightarrow", "\\to", "\\gets", "\\rightsquigarrow",

    # Large operators
    "\\sum", "\\prod", "\\coprod", "\\int", "\\iint", "\\iiint", "\\oint",
    "\\bigcup", "\\bigcap", "\\bigsqcup", "\\bigvee", "\\bigwedge", "\\bigodot", "\\bigotimes", "\\bigoplus",
    "\\lim", "\\limsup", "\\liminf", "\\sup", "\\inf", "\\max", "\\min",

    # Delimiters
    "\\langle", "\\rangle",
    "\\lfloor", "\\rfloor", "\\lceil", "\\rceil", "\\left", "\\right",

    # Accents & decorations
    "\\bar", "\\hat", "\\tilde", "\\vec", "\\dot", "\\ddot", "\\breve", "\\check",
    "\\overline", "\\underline", "\\overbrace", "\\underbrace",

    # Special constants & symbols
    "\\infty", "\\nabla", "\\partial", "\\forall", "\\exists", "\\Re", "\\Im", "\\top", "\\bot", "\\angle", "\\triangle",
    "\\Box", "\\Diamond", "\\neg", "\\emptyset", "\\aleph", "\\hbar", "\\ell", "\\prime", "\\wp",

    # Functions
    "\\sin", "\\cos", "\\tan", "\\cot", "\\sec", "\\csc", "\\arcsin", "\\arccos", "\\arctan",
    "\\sinh", "\\cosh", "\\tanh", "\\log", "\\ln", "\\exp", "\\max", "\\min", "\\sup", "\\inf",

    # Logic
    "\\land", "\\lor", "\\neg", "\\Rightarrow", "\\Leftarrow", "\\iff", "\\implies", "\\therefore", "\\because",

    # Miscellaneous
    "\\dots", "\\ldots", "\\cdots", "\\vdots", "\\ddots", "\\cases"
]


class NormalizeFormula:
    def __init__(self, check_node: bool = True):
        self.root_dir = Path(__file__).resolve().parent
        if check_node and not self.check_node():
            raise NormalizeFormulaError("Node.js was not installed correctly!")

    def __call__(
        self,
        input_content: Union[str, Path, Sequence[Union[str, Path]]],
        out_path: Union[str, Path, None] = None,
        mode: str = "normalize",
    ) -> List[str]:
        input_data = self.load_data(input_content)

        # 将hskip 替换为hspace{}
        after_content = [
            self.preprocessing(str(v)).replace("\r", " ").strip()
            for v in input_data
        ]

        # 借助KaTeX获得规范化后的公式
        normalized_formulas = self.get_normalize_formulas(after_content, mode)

        # 去除非ascii得字符
        final_content = self.post_processing(normalized_formulas)

        if out_path is not None:
            self.write_txt(out_path, final_content)
        return final_content

    def load_data(
        self, input_content: Union[str, Path, Sequence[Union[str, Path]]]
    ) -> Sequence[Union[str, Path]]:
        if isinstance(input_content, list):
            return input_content

        if isinstance(input_content, (str, Path)):
            if len(str(input_content)) > 255:
                return [input_content]

            if Path(input_content).is_file():
                return self.read_txt(input_content)
            return [input_content]

        raise NormalizeFormulaError("The format of input content is not supported!")

    def check_node(self) -> bool:
        if self.run_cmd("node -v"):
            return True
        return False

    def preprocessing(self, input_string: str) -> str:
        pattern = r"hskip(.*?)(cm|in|pt|mm|em)"
        replacement = r"hspace{\1\2}"

        output_string = re.sub(pattern, replacement, input_string)
        output_string = re.sub(r'(?<!\\)\\\s+([\{\}])', r'\1', output_string)
        output_string = re.sub(r'\\\s+%', r'\\%', output_string)

        return output_string

    @staticmethod
    def read_txt(txt_path: Union[Path, str]) -> List[str]:
        with open(txt_path, "r", encoding="utf-8") as f:
            data = [v.rstrip("\n") for v in f]
        return data

    @staticmethod
    def write_txt(
        save_path: Union[str, Path], content: Union[List[str], str], mode: str = "w"
    ) -> None:
        if not isinstance(content, list):
            content = [content]

        with open(save_path, mode, encoding="utf-8") as f:
            for value in content:
                f.write(f"{value}\n")

    def get_normalize_formulas(self, after_content, mode) -> List[str]:
        latex_js_path = self.root_dir / "preprocess_latex.js"
        cmd = ["node", latex_js_path, mode]

        # print("after_content", after_content)

        try:
            result = subprocess.run(
                cmd,
                input="\n".join(after_content),
                capture_output=True,
                text=True,
                check=True,
            )

            if result.stderr != "":
                # print("result.stdout", result.stdout)
                # print("result.stderr", result.stderr)
                if 'Undefined control sequence' not in result.stderr:
                    print("ERROR:", result.stderr)

            # TODO
            # print("result.stderr", result.stderr)
            if 'FULL_TREE' in result.stdout:
                print("result.stdout", result.stdout)

            return result.stdout.splitlines()
        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e.stderr}")
            raise NormalizeFormulaError(
                "Error occurred while normalizing formulas."
            ) from e

    def post_processing(self, normalized_formulas: List[str]) -> List[str]:
        valid_symbols_content = self.remove_invalid_symbols(normalized_formulas)
        final_content = []

        no_need_escape_after_symbol = [ '=', '=:', ',', '}', '{', '(', ')', '>', '<', '-', '+', '*', '|', '%']

        for content in valid_symbols_content:
            # print("content 1", content)

            content = re.sub(r'(?<!\\)([a-zA-Z0-9]+)\s{2,}([a-zA-Z0-9])', r'\1\\\\\2', content)

            content = re.sub(r'(?<!\\)\s+(?!\\)', '', content)
            content = re.sub(r'\\\s+(?!\\)', r'\\', content)
            content = re.sub(r'(?<!\\)\s+\\', r'\\', content)
            content = content.replace('\\\\\\', '\\')
            content = content.removesuffix('\\\\')
            content = content.replace('.\\\\.\\\\.\\\\', '...')
            content = content.replace('\\mathrm\\\\{', '\\mathrm{')
            content = content.replace('\\\\}', '}')
            content = content.replace('\\\\)', ')')

            # print("content 2", content)
            # content = content.replace(" ", "")
            #  {\operator\\} -> {\operator}
            content = re.sub(r'\{\\([a-zA-Z]+)\\\\\}', r'{\\\1}', content)
            content = re.sub(r'(?<!\\)\s*\\([a-zA-Z]+)\\\\(?![a-zA-Z0-9])', r'\\\1', content)

            content = re.sub(r'(\\hspace{[^\\]+)\\\\([^}]+})', r'\1\2', content)

            for symbol in no_need_escape_after_symbol:
                content = content.replace(f'{symbol}\\\\', symbol)

            content = content.replace('= \\', '=\\')
            content = content.replace('\\\\=', '=')
            # print("content 3", content)

            content = re.sub(r'(?<!\\)\s+(?!\\)', '', content)
            content = re.sub(r'\\\s+(?!\\)', r'\\', content)
            content = re.sub(r'(?<!\\)\s+\\', r'\\', content)

            for chars_to_no_spaces_escape in [ ',', '!' ]:
                content = re.sub(r'(?<!\\)\\\s+\\\\' + chars_to_no_spaces_escape, r'\\' + chars_to_no_spaces_escape, content)
                content = re.sub(r'(?<!\\)\\\\\s+\\' + chars_to_no_spaces_escape, r'\\' + chars_to_no_spaces_escape, content)

            content  = content.replace('{\\}', '\\')

            final_content.append(content)

        return final_content

    def remove_invalid_symbols(self, normalized_formulas: List[str]) -> List[str]:
        final_content = []
        for content in normalized_formulas:
            tokens = content.strip()
            tokens_out = [t for t in tokens if self.is_ascii(t)]
            tokens_str = "".join(tokens_out)

            final_content.append(tokens_str)

        return final_content

    @staticmethod
    def is_ascii(txt: str) -> bool:
        if txt == ' ':
            return True
        try:
            txt.encode("ascii").decode("ascii")
            return True
        except UnicodeError:
            return False

    @staticmethod
    def run_cmd(cmd: str) -> bool:
        try:
            ret = subprocess.run(
                cmd,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Run {cmd} meets error. \n{e.stderr}")
            return False
        return True


class NormalizeFormulaError(Exception):
    pass


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess (tokenize or normalize) latex formulas"
    )
    parser.add_argument(
        "--input_content",
        dest="input_content",
        type=str,
        required=True,
        help="Str / List / file path which contains multi-lines formulas.",
    )
    parser.add_argument(
        "--out_path",
        dest="out_path",
        type=str,
        default=None,
        help="Output file. Default is None",
    )
    parser.add_argument(
        "--mode",
        dest="mode",
        choices=["tokenize", "normalize"],
        default="normalize",
        help=(
            "Tokenize (split to tokens separated by space) or normalize (further translate to an equivalent standard form)."
        ),
    )
    args = parser.parse_args()

    processor = NormalizeFormula()
    result = processor(
        input_content=args.input_content,
        out_path=args.out_path,
        mode=args.mode,
    )
    print(result)


if __name__ == "__main__":
    main()
