import ast
import functools
from pathlib import Path

import pytest
from _pytest._py.path import LocalPath
from _pytest.python import Function

from pytest_asyncio import is_async_test


@functools.lru_cache(maxsize=None)
def get_text(file_path: LocalPath) -> str:
    return file_path.read_text("utf-8")


def is_async(item: Function) -> bool:
    content = get_text(item.fspath)
    if f"async def {item.name}" in content:
        return True
    return False


def pytest_collection_modifyitems(items):
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(scope="session")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker, append=False)
