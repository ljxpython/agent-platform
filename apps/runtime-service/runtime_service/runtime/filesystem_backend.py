from __future__ import annotations

import asyncio
from pathlib import Path

from deepagents.backends import FilesystemBackend


async def abuild_filesystem_backend(
    *, root_dir: str | Path, virtual_mode: bool
) -> FilesystemBackend:
    """Construct FilesystemBackend without blocking the event loop."""

    return await asyncio.to_thread(
        FilesystemBackend,
        root_dir=str(root_dir),
        virtual_mode=virtual_mode,
    )
