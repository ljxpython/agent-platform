from __future__ import annotations

from fastapi import APIRouter

from .usecases import router as usecases_router
from .workflows import router as workflows_router


router = APIRouter(prefix="/usecase-generation")
router.include_router(workflows_router)
router.include_router(usecases_router)
