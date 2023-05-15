import importlib
import sys

PYTEST_COLLECT = False


def reimport(module):
    importlib.reload(sys.modules[module])
