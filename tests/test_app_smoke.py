from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


@pytest.mark.integration
@pytest.mark.parametrize(
    "page", ["Overview", "Map", "Prices", "Availability", "Reviews", "Data Quality"]
)
def test_main_streamlit_views_render(page: str) -> None:
    if not Path("data/processed/listings.parquet").exists():
        pytest.skip("Run `airbnb-analysis all` to create app-test data.")
    app = AppTest.from_file("app.py", default_timeout=45)
    app.run()
    assert not app.exception
    app.sidebar.radio[0].set_value(page)
    app.run()
    assert not app.exception

