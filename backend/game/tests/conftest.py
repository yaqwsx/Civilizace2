from pytest import Collector
from typing import Optional, Any
from pathlib import Path

import testing


def pytest_collect_file(
    file_path: Path, path: Any, parent: Collector
) -> Optional[Collector]:
    testing.PYTEST_COLLECT = True
    from _pytest.python import pytest_collect_file as original

    return original(file_path, parent)


def pytest_collection_modifyitems(*args, **kwargs):
    testing.PYTEST_COLLECT = False
