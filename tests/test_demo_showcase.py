"""Snapshot provenance and browser regressions for the curated Pages examples.

Browser tests use Playwright and a Chromium installation, with all requests
intercepted locally. They never download weights or require a running server.
"""

import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def read_json(name):
    return json.loads((DOCS / name).read_text())


def test_sentence_snapshot_provenance_and_showcase():
    original = read_json("demo_results.json")
    sentences = read_json("demo_sentence_results.json")
    assert sentences["input_snapshot_sha256"] == hashlib.sha256(
        (DOCS / "demo_results.json").read_bytes()
    ).hexdigest()
    assert len(sentences["model_revision"]) == 40
    old = {(r["split"], r["sample_id"]): r for r in original["results"]}
    for row in sentences["results"]:
        previous = old[row["split"], row["sample_id"]]
        for field in ("reference_latex", "whisper_transcription", "audio_path"):
            assert row[field] == previous[field]
        assert row["model_id"] == sentences["model_id"]
    combined = {**old, **{(r["split"], r["sample_id"]): r for r in sentences["results"]}}
    seen = set()
    for item in read_json("demo_showcase.json"):
        key = item["split"], item["sample_id"]
        assert key not in seen
        seen.add(key)
        row = combined[key]
        assert (ROOT / row["audio_path"]).is_file()
        assert row["predicted_latex"]
        assert not row.get("hit_token_limit", False)
        if item["split"].startswith("sentences_"):
            assert "sentences_eng_mix" in row["model_id"]
    assert {key[0] for key in seen} == {
        "equations_test", "equations_train", "sentences_test", "sentences_train"
    }


@pytest.fixture
def page():
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()
        vendor = ROOT / "ProcessLaTeXFormulaTools/process_formula/third-party/katex/katex_dist"

        def serve(route):
            parsed = urlparse(route.request.url)
            if parsed.hostname == "demo.test":
                file = DOCS / parsed.path.lstrip("/")
                if file.is_file():
                    route.fulfill(path=str(file))
                else:
                    route.fulfill(status=404, body="missing")
            elif parsed.path.endswith("/katex.min.js"):
                route.fulfill(path=str(vendor / "katex.min.js"))
            else:
                route.abort()

        page.route("**/*", serve)
        yield page
        browser.close()


def load_page(page):
    page.goto("https://demo.test/index.html")
    page.wait_for_selector("#sample:not([disabled])")


def test_all_selected_examples_render_and_switch_models(page):
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    load_page(page)
    assert page.locator("#split option").count() == 4
    for item in read_json("demo_showcase.json"):
        page.select_option("#split", item["split"])
        page.select_option("#sample", item["sample_id"])
        assert page.locator("#demo-results").is_visible()
        assert page.locator(".katex-error").count() == 0
        for field in ("reference", "predicted"):
            assert page.locator(f"#demo-{field} .katex").count() > 0
        if item["split"].startswith("sentences_"):
            assert "sentences_eng_mix" in page.locator("#demo-model").get_attribute("href")
            assert page.locator("#demo-reference").evaluate(
                "el => Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim())"
            )
        else:
            assert "equations_multilingual_mix_full" in page.locator("#demo-model").get_attribute("href")
    assert not errors


def test_sentence_prose_is_text_and_math_stays_inline(page):
    snapshot = read_json("demo_sentence_results.json")
    row = next(r for r in snapshot["results"] if r["split"] == "sentences_test" and r["sample_id"] == "human_eng_00")
    row["predicted_latex"] = r'<img src=x onerror=alert(1)> with $x_i$, \(y^2\), $$z$$ and \[w\].'
    page.route("**/demo_sentence_results.json", lambda route: route.fulfill(json=snapshot))
    load_page(page)
    page.select_option("#split", "sentences_test")
    page.select_option("#sample", "human_eng_00")
    output = page.locator("#demo-predicted")
    assert output.locator("img").count() == 0
    assert "<img src=x onerror=alert(1)> with" in output.inner_text()
    assert output.locator(".katex").count() == 4
    assert output.locator(".katex-display").count() == 2


def test_failed_sentence_snapshot_is_visible(page):
    page.route("**/demo_sentence_results.json", lambda route: route.fulfill(status=503, body="unavailable"))
    page.goto("https://demo.test/index.html")
    page.wait_for_selector("#demo-no-results", state="visible")
    assert page.locator("#split").is_disabled()
    assert page.locator("#sample").is_disabled()
