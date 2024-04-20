import os

import pytest

from tdg.pipeline import Pipeline

pytestmark = pytest.mark.skipif(
    val := os.getenv("TDG_E2E", "0") == "1", reason=f"TDG_E2E set to {val}; skipping"
)
