"""Exercise the HTTP boundary hidden by the old get_api_prices test double."""
import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def scraper(monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "scraper_search", ROOT / "playwright_function/search/__init__.py",
        submodule_search_locations=[str(ROOT / "playwright_function/search")],
    )
    search = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "scraper_search", search)
    spec.loader.exec_module(search)
    monkeypatch.setitem(sys.modules, "search", search)
    spec = importlib.util.spec_from_file_location("scraper_app", ROOT / "playwright_function/app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    from scraper_search.matching import store_result

    for cls, price in [(app.BandcampSearch, 0.99), (app.BeatportSearch, 1.49)]:
        monkeypatch.setattr(cls, "search_song", lambda self, track, artist, price=price: store_result(
            price, f"https://store.example/{track}", artist, track))
    return app

