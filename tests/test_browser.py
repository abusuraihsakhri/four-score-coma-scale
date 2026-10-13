"""Run against Chromium in the dedicated browser CI job."""
from pathlib import Path
import pytest

playwright = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright, expect


def test_score_export_reset_and_responsive_layout(tmp_path):
    source = Path(__file__).resolve().parents[1] / "web" / "index.html"
    with sync_playwright() as driver:
        browser = driver.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 840}, accept_downloads=True)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(source.as_uri())
        expect(page.locator("#total")).to_have_text("—")
        expect(page.locator("#download")).to_be_disabled()
        for name, value in [("eye", "4"), ("motor", "3"), ("brainstem", "2"), ("respiration", "1")]:
            page.locator("#" + name).select_option(value)
        expect(page.locator("#total")).to_have_text("10")
        with page.expect_download() as download_event:
            page.locator("#download").click()
        download = download_event.value
        assert download.suggested_filename == "four-score.csv"
        destination = tmp_path / download.suggested_filename
        download.save_as(destination)
        assert destination.read_text(encoding="utf-8") == (
            "eye,motor,brainstem,respiration,four_score_total\n4,3,2,1,10\n"
        )
        page.locator("#clear").click()
        expect(page.locator("#total")).to_have_text("—")
        expect(page.locator("#download")).to_be_disabled()
        page.set_viewport_size({"width": 375, "height": 740})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        assert not errors
        browser.close()
