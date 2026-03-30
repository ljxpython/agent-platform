from __future__ import annotations

from fastapi import APIRouter

from .routes import router as routes_router
from .test_case_service import router as test_case_service_router

# Keep package-level router assembly consistent with platform-api.
router = APIRouter(prefix="/api")
router.include_router(routes_router)
router.include_router(test_case_service_router)
