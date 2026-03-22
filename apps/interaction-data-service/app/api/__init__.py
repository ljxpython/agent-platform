from __future__ import annotations

from fastapi import APIRouter

from .routes import router as routes_router
from .usecase_generation import router as usecase_generation_router

# Keep package-level router assembly consistent with platform-api.
router = APIRouter(prefix="/api")
router.include_router(routes_router)
router.include_router(usecase_generation_router)
