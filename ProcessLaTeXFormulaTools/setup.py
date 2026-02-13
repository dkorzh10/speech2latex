# -*- encoding: utf-8 -*-
# @Author: SWHL
# @Contact: liekkaskono@163.com
import sys
from pathlib import Path
from typing import List, Union

import setuptools
from setuptools import find_namespace_packages


def read_txt(txt_path: Union[Path, str]) -> List[str]:
    with open(txt_path, "r", encoding="utf-8") as f:
        data = [v.rstrip("\n") for v in f]
    return data


def get_readme() -> str:
    root_dir = Path(__file__).resolve().parent
    readme_path = str(root_dir / "docs" / "doc_whl.md")
    with open(readme_path, "r", encoding="utf-8") as f:
        readme = f.read()
    return readme


MODULE_NAME = "process_formula"

latest_version = "0.0.0"

VERSION_NUM = latest_version

packages = find_namespace_packages()
print("install packages", packages)

setuptools.setup(
    name=MODULE_NAME,
    version=VERSION_NUM,
    platforms="Any",
    description="Tools for processing LaTeX formulas.",
    long_description=get_readme(),
    long_description_content_type="text/markdown",
    author="SWHL",
    author_email="liekkaskono@163.com",
    url="https://github.com/SWHL/ProcessLaTeXFormulaTools",
    license="MIT",
    include_package_data=True,
    install_requires=read_txt("requirements.txt"),
    package_dir={"process_formula": "process_formula"},
    packages=packages,
    package_data={"": ["*.js", "*.json", "*.txt", "*.md"]},
    keywords=["formula,KaTeX,LaTeX,im2markup"],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.6,<3.12",
    entry_points={
        "console_scripts": [
            f"process_formula={MODULE_NAME}.normalize_formulas:main",
        ],
    },
)
