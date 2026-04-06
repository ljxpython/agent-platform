from __future__ import annotations

import asyncio
import importlib
import sys
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

filesystem_backend = importlib.import_module(
    "runtime_service.runtime.filesystem_backend"
)


def test_abuild_filesystem_backend_uses_to_thread(monkeypatch: Any) -> None:
    calls: list[tuple[Any, tuple[Any, ...], dict[str, Any]]] = []

    class DummyBackend:
        def __init__(self, *, root_dir: str, virtual_mode: bool) -> None:
            self.root_dir = root_dir
            self.virtual_mode = virtual_mode

    async def fake_to_thread(func: Any, /, *args: Any, **kwargs: Any) -> Any:
        calls.append((func, args, kwargs))
        return func(*args, **kwargs)

    monkeypatch.setattr(filesystem_backend, "FilesystemBackend", DummyBackend)
    monkeypatch.setattr(filesystem_backend.asyncio, "to_thread", fake_to_thread)

    backend = asyncio.run(
        filesystem_backend.abuild_filesystem_backend(
            root_dir="/tmp/runtime-service-backend",
            virtual_mode=False,
        )
    )

    assert isinstance(backend, DummyBackend)
    assert backend.root_dir == "/tmp/runtime-service-backend"
    assert backend.virtual_mode is False
    assert calls == [
        (
            DummyBackend,
            (),
            {
                "root_dir": "/tmp/runtime-service-backend",
                "virtual_mode": False,
            },
        )
    ]
