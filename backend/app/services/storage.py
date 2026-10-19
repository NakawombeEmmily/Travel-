from __future__ import annotations

import contextlib
import os
from typing import Optional

from app.core.config import settings


class LocalStorage:
    """Simple filesystem-backed object store used when STORAGE_BACKEND=local."""

    def __init__(self, base_dir: str) -> None:
        self.base_dir = os.path.abspath(base_dir)

    def _path(self, key: str) -> str:
        safe = key.replace("\\", "/").lstrip("/")
        full = os.path.abspath(os.path.join(self.base_dir, safe))
        if full != self.base_dir and not full.startswith(self.base_dir + os.sep):
            raise ValueError("Invalid storage key")
        return full

    def save(self, key: str, data: bytes) -> None:
        path = self._path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(data)

    def read(self, key: str) -> bytes:
        with open(self._path(key), "rb") as fh:
            return fh.read()

    def delete(self, key: str) -> None:
        with contextlib.suppress(FileNotFoundError):
            os.remove(self._path(key))


_storage: Optional[LocalStorage] = None


def get_storage() -> LocalStorage:
    global _storage
    if _storage is None:
        _storage = LocalStorage(settings.STORAGE_LOCAL_DIR)
    return _storage
