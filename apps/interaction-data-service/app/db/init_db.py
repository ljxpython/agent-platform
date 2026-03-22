from __future__ import annotations

from typing import Any

from app.db import models  # noqa: F401
from app.db.base import Base


def create_core_tables(engine: Any) -> None:
    Base.metadata.create_all(bind=engine)
