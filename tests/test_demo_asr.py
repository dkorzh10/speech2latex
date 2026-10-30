"""Exercise notebook ASR calls and sample manifests without downloading weights."""

import ast
import json
import os
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


def notebook_helpers(monkeypatch):
    notebook = json.loads((ROOT / "demo_speech2latex.ipynb").read_text())
    source = next(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if "def transcribe_whisper(" in "".join(cell["source"])
    )
    tree = ast.parse(source)
    keep = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        or isinstance(node, ast.ImportFrom)
        and node.module == "functools"
        or isinstance(node, ast.FunctionDef)
        and node.name in ("load_whisper_model", "transcribe_whisper")
    ]
    model = Mock()
    model.transcribe.return_value = {"text": "  один плюс один  "}
    loader = Mock(return_value=model)
    monkeypatch.setitem(
        __import__("sys").modules, "whisper", SimpleNamespace(load_model=loader)
    )
    namespace = {"device": "cpu"}
    exec(
        compile(ast.Module(body=keep, type_ignores=[]), "<notebook-asr>", "exec"),
        namespace,
    )
    return namespace, loader, model


def test_notebook_auto_for_samples_and_recordings_reuses_model(monkeypatch):
    helpers, loader, model = notebook_helpers(monkeypatch)
    for path in ("/tmp/sample.wav", "/tmp/recording.webm"):
        assert helpers["transcribe_whisper"](path) == "один плюс один"
    loader.assert_called_once_with("large-v3", device="cpu")
    assert all(
        call.kwargs["language"] is None for call in model.transcribe.call_args_list
    )
    assert all(call.kwargs["fp16"] is False for call in model.transcribe.call_args_list)


@pytest.mark.parametrize("language", ["en", "ru"])
def test_notebook_explicit_hint_and_invalid_language(monkeypatch, language):
    helpers, _, model = notebook_helpers(monkeypatch)
    helpers["transcribe_whisper"]("sample.wav", language=language)
    assert model.transcribe.call_args.kwargs["language"] == language
    with pytest.raises(ValueError):
        helpers["transcribe_whisper"]("sample.wav", language="invalid")
    assert model.transcribe.call_count == 1


def test_manifest_auto_ignores_legacy_cache_and_separates_configs(
    monkeypatch, tmp_path
):
    source = ast.parse((ROOT / "ASRPostCorrection/run_qwen_demo.py").read_text())
    functions = [
        node
        for node in source.body
        if isinstance(node, ast.FunctionDef)
        and node.name
        in (
            "_manifest_cache_path",
            "_ensure_latex_with_dollars",
            "build_manifest_from_hf",
        )
    ]
    namespace = {
        "os": os,
        "pd": pd,
        "torch": SimpleNamespace(
            cuda=SimpleNamespace(is_available=lambda: False), no_grad=nullcontext
        ),
        "tqdm": lambda iterable, **kwargs: iterable,
        "SAMPLE_IDS": {"equations_test": ["human_eng_00", "human_ru_00"]},
    }
    exec(
        compile(ast.Module(body=functions, type_ignores=[]), "<demo-manifest>", "exec"),
        namespace,
    )
    samples = tmp_path / "sample_datasets"
    (samples / "equations_test").mkdir(parents=True)
    for sample in namespace["SAMPLE_IDS"]["equations_test"]:
        (samples / "equations_test" / (sample + ".wav")).touch()
    # Legacy base cache must not suppress a Large-v3 run.
    (tmp_path / ".demo_manifest_cache_marsianin500_Speech2Latex.csv").write_text(
        "stale cache"
    )
    model = Mock()
    model.transcribe.return_value = {"text": "one plus one"}
    loader = Mock(return_value=model)
    import sys

    monkeypatch.setitem(sys.modules, "whisper", SimpleNamespace(load_model=loader))
    monkeypatch.setitem(
        sys.modules,
        "datasets",
        SimpleNamespace(
            load_dataset=lambda *args, **kwargs: [
                {"is_tts": False, "language": lang, "sentence": "1+1"}
                for lang in ("eng", "ru")
            ]
        ),
    )
    audio = SimpleNamespace(
        squeeze=lambda: SimpleNamespace(numpy=lambda: np.zeros(160, dtype="float32"))
    )
    monkeypatch.setitem(
        sys.modules, "torchaudio", SimpleNamespace(load=lambda path: (audio, 16000))
    )
    result = namespace["build_manifest_from_hf"](str(samples))
    assert len(result) == 2
    loader.assert_called_once_with("large-v3", device="cpu")
    assert all(
        call.kwargs["language"] is None for call in model.transcribe.call_args_list
    )
    path = namespace["_manifest_cache_path"]
    assert (
        len(
            {
                path(str(samples), "dataset", name, language)
                for name in ("base", "large-v3")
                for language in ("auto", "ru")
            }
        )
        == 4
    )
    pd.testing.assert_frame_equal(
        namespace["build_manifest_from_hf"](str(samples)), result
    )
    assert model.transcribe.call_count == 2
