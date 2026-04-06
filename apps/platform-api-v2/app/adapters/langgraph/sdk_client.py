from __future__ import annotations

from typing import Any, Mapping

import httpx
import langgraph_sdk
from fastapi import HTTPException

from app.core.errors import PlatformApiError, UpstreamServiceError


def get_langgraph_client(
    *,
    base_url: str,
    api_key: str | None = None,
    forwarded_headers: Mapping[str, str] | None = None,
    timeout_seconds: float | None = None,
) -> Any:
    return langgraph_sdk.get_client(
        url=base_url,
        api_key=api_key if api_key else None,
        headers=dict(forwarded_headers or {}),
        timeout=timeout_seconds,
    )


def raise_runtime_upstream_error(exc: Exception, *, fallback_detail: str) -> None:
    if isinstance(exc, HTTPException):
        raise exc

    if isinstance(exc, httpx.TimeoutException):
        raise HTTPException(status_code=504, detail="langgraph_upstream_timeout") from exc

    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    if isinstance(status_code, int):
        try:
            detail: Any = response.json()
        except Exception:
            detail = getattr(response, "text", None) or fallback_detail
        raise HTTPException(status_code=status_code, detail=detail) from exc

    message = str(exc).strip()
    if message.startswith("ValueError:"):
        detail = message.split(":", 1)[1].strip() or fallback_detail
        raise HTTPException(status_code=400, detail=detail) from exc

    raise HTTPException(status_code=502, detail=fallback_detail) from exc


def raise_assistants_upstream_error(exc: Exception, *, upstream_path: str) -> None:
    if isinstance(exc, (PlatformApiError, UpstreamServiceError)):
        raise exc

    if isinstance(exc, httpx.TimeoutException):
        raise UpstreamServiceError(
            upstream="langgraph",
            status_code=504,
            code="langgraph_upstream_timeout",
            message="LangGraph upstream timed out",
        ) from exc

    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    if isinstance(status_code, int):
        raise PlatformApiError(
            code="langgraph_upstream_request_failed",
            status_code=502,
            message=f"LangGraph upstream request failed ({status_code})",
            extra={
                "upstream_status_code": status_code,
                "upstream_path": upstream_path,
            },
        ) from exc

    if isinstance(exc, httpx.HTTPError):
        raise UpstreamServiceError(
            upstream="langgraph",
            status_code=502,
            code="langgraph_upstream_unavailable",
            message="LangGraph upstream is unavailable",
        ) from exc

    raise UpstreamServiceError(
        upstream="langgraph",
        status_code=502,
        code="langgraph_upstream_unavailable",
        message="LangGraph upstream is unavailable",
    ) from exc
