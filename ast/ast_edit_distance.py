#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Оценка близости LaTeX-формул через unified-latex AST.

Требования:
- Node >= 16
- npm install @unified-latex/unified-latex
- рабочий parse_latex.mjs в той же папке

Использование из кода:
    from latex_ast_eval import unified_formulas_equal, evaluate_pair, tree_edit_distance_for_ast

    res = evaluate_pair(r"\\frac{1}{2} + x^2", r"1/2 + x^2")
    print(res["equal"], res["distance"])

Использование из консоли:
    python latex_ast_eval.py "\\frac{1}{2} + x^2" "1/2 + x^2" --show-asts
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

        content = node.get("content")
        # Если content — список (root, group и т.п.)
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

        # Другие поля игнорируем
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


# ---------- Вспомогалки для AST как дерева ----------

def node_children(node: Any) -> list:
    """
    Возвращает список детей для нормализованного AST-узла.
    Предполагается, что node — dict вида {"type": ..., "content": ...}.
    """
    if not isinstance(node, dict):
        return []
    content = node.get("content")
    if isinstance(content, list):
        return content
    return []


def node_label(node: Any) -> str:
    """
    Метка узла для сравнения (подстановка).
    Можно менять стратегию (например, учитывать только type).
    """
    if not isinstance(node, dict):
        return repr(node)
    t = node.get("type", "")
    c = node.get("content", None)
    if isinstance(c, str):
        return f"{t}:{c}"
    return t


def subtree_size(node: Any) -> int:
    """
    Размер поддерева (количество узлов), для стоимости вставки/удаления.
    """
    if node is None:
        return 0
    if not isinstance(node, dict):
        return 1
    children = node_children(node)
    return 1 + sum(subtree_size(ch) for ch in children)


# ---------- Tree edit distance (упрощённый Zhang–Shasha) ----------

def tree_edit_distance_for_ast(ast1: Any, ast2: Any) -> int:
    """
    Расстояние редактирования деревьев между двумя нормализованными AST.
    Операции:
      - вставка поддерева (стоимость = размер поддерева)
      - удаление поддерева (стоимость = размер поддерева)
      - замена метки корня (стоимость 0, если label равны, иначе 1)
    Внутри используется DP по детям (как "Левенштейн по списку детей",
    где стоимость замены = рекурсивное TED по поддеревьям).
    """

    def ted(n1: Any, n2: Any) -> int:
        if n1 is None and n2 is None:
            return 0
        if n1 is None:
            return subtree_size(n2)
        if n2 is None:
            return subtree_size(n1)

        children1 = node_children(n1)
        children2 = node_children(n2)
        m, n = len(children1), len(children2)

        # Стоимость замены корня
        sub_cost_root = 0 if node_label(n1) == node_label(n2) else 1

        # DP-таблица по детям
        # dp[i][j] — стоимость превратить первые i детей n1 в первые j детей n2
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        dp[0][0] = 0

        # Удаляем поддеревья детей n1
        for i in range(1, m + 1):
            dp[i][0] = dp[i - 1][0] + subtree_size(children1[i - 1])

        # Вставляем поддеревья детей n2
        for j in range(1, n + 1):
            dp[0][j] = dp[0][j - 1] + subtree_size(children2[j - 1])

        # Основной цикл
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                cost_del = subtree_size(children1[i - 1])       # удалить i-го ребёнка целиком
                cost_ins = subtree_size(children2[j - 1])       # вставить j-го ребёнка целиком
                cost_subtree = ted(children1[i - 1], children2[j - 1])  # заменить поддерево

                dp[i][j] = min(
                    dp[i - 1][j] + cost_del,          # удаление поддерева
                    dp[i][j - 1] + cost_ins,          # вставка поддерева
                    dp[i - 1][j - 1] + cost_subtree   # сопоставление (замена) поддеревьев
                )

        return sub_cost_root + dp[m][n]

    return ted(ast1, ast2)


# ---------- Сравнение AST булево ----------

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
    - флаг строгого равенства
    - расстояние редактирования деревьев между нормализованными AST
    """
    ast_gt_raw = latex_to_unified_ast(latex_gt)
    ast_pred_raw = latex_to_unified_ast(latex_pred)

    ast_gt = normalize_ast(ast_gt_raw)
    ast_pred = normalize_ast(ast_pred_raw)

    equal = ast_equal(ast_gt, ast_pred)
    distance = tree_edit_distance_for_ast(ast_gt, ast_pred)

    return {
        "equal": equal,
        "distance": distance,
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
    print("tree_edit_distance:", res["distance"])

    if args.show_asts:
        print("\nGT AST:")
        pprint(res["gt_norm_ast"])
        print("\nPRED AST:")
        pprint(res["pred_norm_ast"])


if __name__ == "__main__":
    _main_cli()

# python ast_edit_distance.py "\\frac{1}{2} + x^2" "\\frac{1}{2} + x^2"

# python ast_edit_distance.py "\\frac{1}{2} + x^2" "1/2 + x^2"