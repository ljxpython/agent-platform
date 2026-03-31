from __future__ import annotations

from app.api.common import require_db_session_factory
from app.db.access import (
    get_test_case_batch_detail,
    get_test_case_overview,
    list_test_case_batches,
    parse_uuid,
)
from app.db.session import session_scope
from app.schemas.test_case_service import (
    TestCaseBatchDetailResponse,
    TestCaseBatchListResponse,
    TestCaseOverviewResponse,
)
from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter(tags=["test-case-service"])


def _serialize_batch_summary(item: dict[str, object]) -> dict[str, object]:
    return {
        "batch_id": str(item["batch_id"]),
        "documents_count": int(item["documents_count"]),
        "test_cases_count": int(item["test_cases_count"]),
        "latest_created_at": (
            item["latest_created_at"].isoformat()
            if item.get("latest_created_at") is not None
            else None
        ),
        "parse_status_summary": dict(item.get("parse_status_summary") or {}),
    }


def _serialize_document(row) -> dict[str, object]:
    return {
        "id": str(row.id),
        "project_id": str(row.project_id),
        "batch_id": row.batch_id,
        "idempotency_key": row.idempotency_key,
        "filename": row.filename,
        "content_type": row.content_type,
        "storage_path": row.storage_path,
        "source_kind": row.source_kind,
        "parse_status": row.parse_status,
        "summary_for_model": row.summary_for_model,
        "parsed_text": row.parsed_text,
        "structured_data": row.structured_data,
        "provenance": row.provenance,
        "confidence": row.confidence,
        "error": row.error,
        "created_at": row.created_at.isoformat(),
    }


def _serialize_batch_case(row) -> dict[str, object]:
    return {
        "id": str(row.id),
        "case_id": row.case_id,
        "title": row.title,
        "status": row.status,
        "batch_id": row.batch_id,
        "module_name": row.module_name,
        "priority": row.priority,
        "updated_at": row.updated_at.isoformat() if row.updated_at is not None else None,
    }


@router.get("/overview", response_model=TestCaseOverviewResponse)
async def get_overview(
    request: Request,
    project_id: str | None = Query(None),
):
    project_uuid = parse_uuid(project_id) if project_id else None
    if project_id and project_uuid is None:
        raise HTTPException(status_code=400, detail="invalid_project_id")
    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        overview = get_test_case_overview(session, project_id=project_uuid)
        return {
            "project_id": project_id,
            "documents_total": overview["documents_total"],
            "parsed_documents_total": overview["parsed_documents_total"],
            "failed_documents_total": overview["failed_documents_total"],
            "test_cases_total": overview["test_cases_total"],
            "latest_batch_id": overview["latest_batch_id"],
            "latest_activity_at": (
                overview["latest_activity_at"].isoformat()
                if overview["latest_activity_at"] is not None
                else None
            ),
        }


@router.get("/batches", response_model=TestCaseBatchListResponse)
async def list_batches(
    request: Request,
    project_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    project_uuid = parse_uuid(project_id) if project_id else None
    if project_id and project_uuid is None:
        raise HTTPException(status_code=400, detail="invalid_project_id")
    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        rows, total = list_test_case_batches(
            session,
            project_id=project_uuid,
            limit=limit,
            offset=offset,
        )
        return {
            "items": [_serialize_batch_summary(item) for item in rows],
            "total": total,
        }


@router.get("/batches/{batch_id}", response_model=TestCaseBatchDetailResponse)
async def get_batch_detail(
    request: Request,
    batch_id: str,
    project_id: str | None = Query(None),
    document_limit: int = Query(100, ge=1, le=500),
    document_offset: int = Query(0, ge=0),
    case_limit: int = Query(50, ge=1, le=500),
    case_offset: int = Query(0, ge=0),
):
    project_uuid = parse_uuid(project_id) if project_id else None
    if project_id and project_uuid is None:
        raise HTTPException(status_code=400, detail="invalid_project_id")
    normalized_batch_id = batch_id.strip()
    if not normalized_batch_id:
        raise HTTPException(status_code=400, detail="invalid_batch_id")
    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        payload = get_test_case_batch_detail(
            session,
            project_id=project_uuid,
            batch_id=normalized_batch_id,
            document_limit=document_limit,
            document_offset=document_offset,
            case_limit=case_limit,
            case_offset=case_offset,
        )
        if payload is None:
            raise HTTPException(status_code=404, detail="batch_not_found")
        batch = payload["batch"]
        documents = payload["documents"]
        test_cases = payload["test_cases"]
        return {
            "batch": _serialize_batch_summary(batch),
            "documents": {
                "items": [_serialize_document(row) for row in documents["items"]],
                "total": int(documents["total"]),
            },
            "test_cases": {
                "items": [_serialize_batch_case(row) for row in test_cases["items"]],
                "total": int(test_cases["total"]),
            },
        }
