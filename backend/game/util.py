from pathlib import Path
from typing import Callable


class FileCache:
    def __init__(self, cacheDirectory, suffix):
        self.cacheDirectory = Path(cacheDirectory).resolve()
        self.cacheDirectory.mkdir(exist_ok=True, parents=True)
        self.suffix = suffix

    def path(self, ident: str, renderer: Callable[[str], None]) -> Path:
        """
        Given an identifier and renderer (function that will fill content in the
        give file) return path to a file populated with the content.
        """
        cFile = self._cacheFile(ident)
        if not cFile.exists():
            renderer(str(cFile))
        return cFile

    def content(self, ident, renderer: Callable[[str], None]) -> bytes:
        cFile = self.path(ident, renderer)
        with open(cFile, "wb") as f:
            return f.read()

    def _cacheFile(self, ident):
        return self.cacheDirectory / f"{ident}.{self.suffix}"
