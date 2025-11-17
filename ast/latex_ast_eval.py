#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Оценка близости LaTeX-формул через unified-latex AST.

Требования:
- Node >= 16
- npm install @unified-latex/unified-latex
- рабочий parse_latex.mjs в той же папке

Использование из кода:
    from latex_ast_eval import unified_formulas_equal, evaluate_pair

    res = evaluate_pair(r"\frac{1}{2} + x^2", r"\frac{1}{2}+x^2")
    print(res)

Использование из консоли:
    python latex_ast_eval.py "\\frac{1}{2} + x^2" "\\frac{1}{2}+x^2"
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict


# Путь к Node-скрипту unified-latex
NODE_SCRIPT = Path(__file__).parent / "parse_latex.mjs"


# ---------- Вызов unified-latex (Node) ----------

def latex_to_unified_ast(latex: str) -> Dict[str, Any]:
    """
    Запускает parse_latex.mjs, передаёт LaTeX на stdin,
    возвращает AST (как dict, распарсенный из JSON).
    """
    if not NODE_SCRIPT.exists():
        raise FileNotFoundError(f"Не найден {NODE_SCRIPT}. Убедись, что parse_latex.mjs лежит рядом с этим скриптом.")

    proc = subprocess.run(
        ["node", str(NODE_SCRIPT)],
        input=latex.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(f"unified-latex (parse_latex.mjs) завершился с ошибкой:\n{err}")

    out = proc.stdout.decode("utf-8")
    return json.loads(out)


# ---------- Нормализация AST ----------

def normalize_ast(node: Any) -> Any:
    """
    Упрощаем unified-latex AST:
    - убираем whitespace-ноды
    - убираем position
    - оставляем только type + content (рекурсивно)
    """
    if isinstance(node, dict):
        node_type = node.get("type")

        # Пропускаем whitespace
        if node_type == "whitespace":
            return None

        norm: Dict[str, Any] = {"type": node_type}

        # Если content — список (root, group и т.п.)
        content = node.get("content")
        if isinstance(content, list):
            children = []
            for child in content:
                c = normalize_ast(child)
                if c is not None:
                    children.append(c)
            norm["content"] = children

        # Если content — строка (string-узлы и т.п.)
        elif isinstance(content, str):
            norm["content"] = content

        # Другие поля (position и т.п.) игнорируем
        return norm

    elif isinstance(node, list):
        res = []
        for child in node:
            c = normalize_ast(child)
            if c is not None:
                res.append(c)
        return res

    else:
        # скаляры/прочее возвращаем как есть
        return node


# ---------- Сравнение AST ----------

def ast_equal(a: Any, b: Any) -> bool:
    """
    Примитивное рекурсивное сравнение двух нормализованных AST.
    """
    if type(a) != type(b):
        return False

    if isinstance(a, dict):
        if a.keys() != b.keys():
            return False
        return all(ast_equal(a[k], b[k]) for k in a.keys())

    if isinstance(a, list):
        if len(a) != len(b):
            return False
        return all(ast_equal(x, y) for x, y in zip(a, b))

    return a == b


# ---------- Высокоуровневые функции ----------

def unified_formulas_equal(latex_gt: str, latex_pred: str) -> bool:
    """
    True, если нормализованный AST GT и предсказания совпадают (строгая структурная эквивалентность).
    Сейчас:
        - игнорируются пробелы
        - НЕ учитывается математическая эквивалентность типа 1/2 == \\frac{1}{2}
    """
    ast_gt_raw = latex_to_unified_ast(latex_gt)
    ast_pred_raw = latex_to_unified_ast(latex_pred)

    ast_gt = normalize_ast(ast_gt_raw)
    ast_pred = normalize_ast(ast_pred_raw)

    return ast_equal(ast_gt, ast_pred)


def evaluate_pair(latex_gt: str, latex_pred: str) -> Dict[str, Any]:
    """
    Возвращает информацию по одной паре (GT, pred):
    - raw/norm AST
    - флаг равенства
    """
    ast_gt_raw = latex_to_unified_ast(latex_gt)
    ast_pred_raw = latex_to_unified_ast(latex_pred)

    ast_gt = normalize_ast(ast_gt_raw)
    ast_pred = normalize_ast(ast_pred_raw)

    equal = ast_equal(ast_gt, ast_pred)

    return {
        "equal": equal,
        "gt_norm_ast": ast_gt,
        "pred_norm_ast": ast_pred,
    }


# ---------- CLI ----------

def _main_cli():
    import argparse
    from pprint import pprint

    parser = argparse.ArgumentParser(description="Сравнение LaTeX-формул через unified-latex AST")
    parser.add_argument("gt", help="GT формула (LaTeX)")
    parser.add_argument("pred", help="предсказанная формула (LaTeX)")
    parser.add_argument(
        "--show-asts",
        action="store_true",
        help="распечатать нормализованные AST"
    )
    args = parser.parse_args()

    res = evaluate_pair(args.gt, args.pred)

    print("equal:", res["equal"])
    if args.show_asts:
        print("\nGT AST:")
        pprint(res["gt_norm_ast"])
        print("\nPRED AST:")
        pprint(res["pred_norm_ast"])


if __name__ == "__main__":
    _main_cli()



# from sympy.parsing.latex import parse_latex
# from sympy import Basic

# from pylatexenc.latexwalker import LatexWalker

# # --- SymPy часть --- #

# def latex_to_sympy_safe(latex: str):
#     try:
#         return parse_latex(latex)
#     except Exception:
#         return None

# def sympy_to_simple_ast(expr: Basic):
#     if expr is None:
#         return None
#     if not isinstance(expr, Basic) or len(expr.args) == 0:
#         return {
#             "type": type(expr).__name__,
#             "value": str(expr),
#             "children": []
#         }
#     return {
#         "type": type(expr).__name__,
#         "value": str(expr.func),
#         "children": [sympy_to_simple_ast(a) for a in expr.args]
#     }

# # --- TeX AST через latexwalker --- #

# from pylatexenc.latexwalker import LatexEnvironmentNode, LatexMacroNode, LatexGroupNode, LatexCharsNode

# def latex_to_tex_ast(latex: str):
#     w = LatexWalker(latex)
#     nodes, pos, len_ = w.get_latex_nodes()
#     return [convert_node_tex(n) for n in nodes]

# def convert_node_tex(node):
#     if isinstance(node, LatexCharsNode):
#         return {"type": "chars", "content": node.chars, "children": []}
#     if isinstance(node, LatexMacroNode):
#         children = []
#         if node.nodeoptarg:
#             children.append(convert_node_tex(node.nodeoptarg))
#         for a in node.nodeargs:
#             children.append(convert_node_tex(a))
#         return {"type": "macro", "name": node.macroname, "children": children}
#     if isinstance(node, LatexGroupNode):
#         return {"type": "group",
#                 "children": [convert_node_tex(n) for n in node.nodelist]}
#     if isinstance(node, LatexEnvironmentNode):
#         return {"type": "environment", "name": node.envname,
#                 "children": [convert_node_tex(n) for n in node.nodelist]}
#     d = {"type": type(node).__name__}
#     if hasattr(node, "nodelist") and node.nodelist is not None:
#         d["children"] = [convert_node_tex(n) for n in node.nodelist]
#     else:
#         d["children"] = []
#     return d

# # --- Функция метрики --- #

# def evaluate_pair(gt_latex: str, pred_latex: str):
#     """
#     Возвращает инфу:
#     - parsable_sympy: оба разобраны SymPy
#     - sympy_equal: если разобраны, равны ли математически
#     - tex_ast_equal: равен ли синтаксический LaTeX AST (грубая оценка)
#     """
#     gt_sym = latex_to_sympy_safe(gt_latex)
#     pr_sym = latex_to_sympy_safe(pred_latex)

#     parsable_sympy = gt_sym is not None and pr_sym is not None

#     sympy_equal = None
#     if parsable_sympy:
#         try:
#             sympy_equal = (gt_sym - pr_sym).simplify() == 0
#         except Exception:
#             # не всегда можно вычесть (например, матрицы/некоторые функции)
#             sympy_equal = (gt_sym == pr_sym)

#     # Всегда можем посчитать TeX AST
#     gt_tex_ast = latex_to_tex_ast(gt_latex)
#     pr_tex_ast = latex_to_tex_ast(pred_latex)

#     tex_ast_equal = (gt_tex_ast == pr_tex_ast)

#     return {
#         "parsable_sympy": parsable_sympy,
#         "sympy_equal": sympy_equal,
#         "tex_ast_equal": tex_ast_equal,
#         "gt_sympy": str(gt_sym) if gt_sym is not None else None,
#         "pr_sympy": str(pr_sym) if pr_sym is not None else None,
#     }


# # Пример использования
# if __name__ == "__main__":
#     tests = [
#         (r"\frac{1}{2}", r"1/2"),
#         (r"a+b", r"b+a"),
#         (r"\int_0^1 x^2 \, dx", r"\int_0^1 x^2 dx"),
#         (r"\begin{pmatrix}a&b\\c&d\end{pmatrix}", r"\begin{pmatrix}a&b\\c&d\end{pmatrix}"),
#         (r"\sum_{i=1}^n \frac{a_i}{1+x^2}", r"\sum_{i = 1}^{n} \frac{a_i}{1+x^2}")
#     ]

#     for gt, pr in tests:
#         res = evaluate_pair(gt, pr)
#         print("GT:", gt)
#         print("PR:", pr)
#         print(res)
#         print("-" * 60)
