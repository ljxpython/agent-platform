from __future__ import annotations

from io import BytesIO
from typing import Any

from app.api.management.common import require_project_role
from app.api.management.schemas import (
    CreateTestCaseRecordRequest,
    UpdateTestCaseRecordRequest,
)
from app.db.access import parse_uuid
from app.services.interaction_data_service import InteractionDataService
from app.services.testcase_case_export import (
    MAX_TESTCASE_EXPORT_ROWS,
    _EXPORT_MEDIA_TYPE,
    build_content_disposition,
    build_testcase_cases_workbook,
    resolve_testcase_export_columns,
)
from app.services.testcase_document_export import (
    MAX_TESTCASE_DOCUMENT_EXPORT_ROWS,
    TESTCASE_DOCUMENT_EXPORT_MEDIA_TYPE,
    build_content_disposition as build_document_content_disposition,
    build_testcase_documents_workbook,
)
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["management-testcase"])


def _parse_project_id(project_id: str):
    project_uuid = parse_uuid(project_id)
    if project_uuid is None:
        raise HTTPException(status_code=400, detail="invalid_project_id")
    return project_uuid


def _cleanup_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _payload_to_dict(payload: Any) -> dict[str, Any]:
    return payload.model_dump(exclude_none=True) if hasattr(payload, "model_dump") else dict(payload)


def _normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    seen: set[str] = set()
    for item in value:
        normalized = _cleanup_optional_text(item)
        if normalized and normalized not in seen:
            seen.add(normalized)
            items.append(normalized)
    return items


def _normalize_testcase_payload(payload: dict[str, Any]) -> dict[str, Any]:
    next_payload = dict(payload)
    for key in ("batch_id", "case_id", "module_name", "priority"):
        if key in next_payload:
            next_payload[key] = _cleanup_optional_text(next_payload.get(key))
    if "title" in next_payload:
        title = _cleanup_optional_text(next_payload.get("title"))
        if title is not None:
            next_payload["title"] = title
    if "description" in next_payload and next_payload.get("description") is None:
        next_payload["description"] = ""
    if "source_document_ids" in next_payload:
        next_payload["source_document_ids"] = _normalize_string_list(
            next_payload.get("source_document_ids")
        )
    return next_payload


@router.get("/projects/{project_id}/testcase/overview")
async def get_testcase_overview(request: Request, project_id: str) -> dict[str, Any]:
    project_uuid = _parse_project_id(project_id)
    require_project_role(request, project_uuid, allowed_roles={"admin", "editor", "executor"})
    service = InteractionDataService(request)
    return await service.get_overview(project_id)


@router.get("/projects/{project_id}/testcase/role")
async def get_testcase_role(request: Request, project_id: str) -> dict[str, Any]:
    project_uuid = _parse_project_id(project_id)
    _, role = require_project_role(
        request,
        project_uuid,
        allowed_roles={"admin", "editor", "executor"},
    )
    return {
        "project_id": project_id,
        "role": role,
        "can_write_testcase": role in {"admin", "editor"},
    }


@router.get("/projects/{project_id}/testcase/batches")
async def list_testcase_batches(
    request: Request,
    project_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    project_uuid = _parse_project_id(project_id)
    require_project_role(request, project_uuid, allowed_roles={"admin", "editor", "executor"})
    service = InteractionDataService(request)
    return await service.list_batches(project_id, limit=limit, offset=offset)


@router.get("/projects/{project_id}/testcase/cases")
async def list_testcase_cases(
    request: Request,
    project_id: str,
    status: str | None = Query(default=None),
    batch_id: str | None = Query(default=None),
    query: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    project_uuid = _parse_project_id(project_id)
    require_project_role(request, project_uuid, allowed_roles={"admin", "editor", "executor"})
    service = InteractionDataService(request)
    return await service.list_cases(
        project_id,
        status=_cleanup_optional_text(status),
        batch_id=_cleanup_optional_text(batch_id),
        query=_cleanup_optional_text(query),
        limit=limit,
        offset=offset,
    )


@router.get("/projects/{project_id}/testcase/cases/export")
async def export_testcase_cases(
    request: Request,
    project_id: str,
    status: str | None = Query(default=None),
    batch_id: str | None = Query(default=None),
    query: str | None = Query(default=None),
    columns: str | None = Query(default=None),
) -> StreamingResponse:
    project_uuid = _parse_project_id(project_id)
    require_project_role(request, project_uuid, allowed_roles={"admin", "editor", "executor"})
    service = InteractionDataService(request)
    normalized_status = _cleanup_optional_text(status)
    normalized_batch_id = _cleanup_optional_text(batch_id)
    normalized_query = _cleanup_optional_text(query)
    resolved_columns = resolve_testcase_export_columns(
        [
            item
            for item in (columns or "").split(",")
            if isinstance(item, str) and item.strip()
        ]
    )
    items, _total = await service.list_all_cases_for_export(
        project_id,
        status=normalized_status,
        batch_id=normalized_batch_id,
        query=normalized_query,
        max_items=MAX_TESTCASE_EXPORT_ROWS,
    )
    filename, workbook_bytes = build_testcase_cases_workbook(
        project_id=project_id,
        cases=items,
        filters={
            "status": normalized_status,
            "batch_id": normalized_batch_id,
            "query": normalized_query,
        },
        columns=resolved_columns,
    )
    return StreamingResponse(
        BytesIO(workbook_bytes),
        media_type=_EXPORT_MEDIA_TYPE,
        headers={"Content-Disposition": build_content_disposition(filename)},
    )


@router.get("/projects/{project_id}/testcase/cases/{case_id}")
async def get_testcase_case(request: Request, project_id: str, case_id: str) -> dict[str, Any]:
    project_uuid = _parse_project_id(project_id)
    require_project_role(request, project_uuid, allowed_roles={"admin", "editor", "executor"})
    service = InteractionDataService(request)
    payload = await service.get_case(project_id, case_id)
    source_document_ids = _normalize_string_list(payload.get("source_document_ids"))
    source_documents: list[dict[str, Any]] = []
    missing_source_document_ids: list[str] = []
    for document_id in source_document_ids:
        try:
            source_documents.append(await service.get_document(project_id, document_id))
        except HTTPException as exc:
            if exc.status_code == 404:
                missing_source_document_ids.append(document_id)
                continue
            raise
    return {
        **payload,
        "source_documents": source_documents,
        "missing_source_document_ids": missing_source_document_ids,
    }


@router.post("/projects/{project_id}/testcase/cases")
async def create_testcase_case(
    request: Request,
    project_id: str,
    payload: CreateTestCaseRecordRequest,
) -> dict[str, Any]:
    project_uuid = _parse_project_id(project_id)
    require_project_role(request, project_uuid, allowed_roles={"admin", "editor"})
    service = InteractionDataService(request)
    return await service.create_case(
        project_id,
        _normalize_testcase_payload(_payload_to_dict(payload)),
    )


@router.patch("/projects/{project_id}/testcase/cases/{case_id}")
async def update_testcase_case(
    request: Request,
    project_id: str,
    case_id: str,
    payload: UpdateTestCaseRecordRequest,
) -> dict[str, Any]:
    project_uuid = _parse_project_id(project_id)
    require_project_role(request, project_uuid, allowed_roles={"admin", "editor"})
    service = InteractionDataService(request)
    return await service.update_case(
        project_id,
        case_id,
        _normalize_testcase_payload(_payload_to_dict(payload)),
    )


@router.delete("/projects/{project_id}/testcase/cases/{case_id}")
async def delete_testcase_case(request: Request, project_id: str, case_id: str) -> dict[str, Any]:
    project_uuid = _parse_project_id(project_id)
    require_project_role(request, project_uuid, allowed_roles={"admin", "editor"})
    service = InteractionDataService(request)
    return await service.delete_case(project_id, case_id)


@router.get("/projects/{project_id}/testcase/documents")
async def list_testcase_documents(
    request: Request,
    project_id: str,
    batch_id: str | None = Query(default=None),
    parse_status: str | None = Query(default=None),
    query: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    project_uuid = _parse_project_id(project_id)
    require_project_role(request, project_uuid, allowed_roles={"admin", "editor", "executor"})
    service = InteractionDataService(request)
    return await service.list_documents(
        project_id,
        batch_id=_cleanup_optional_text(batch_id),
        parse_status=_cleanup_optional_text(parse_status),
        query=_cleanup_optional_text(query),
        limit=limit,
        offset=offset,
    )


@router.get("/projects/{project_id}/testcase/documents/export")
async def export_testcase_documents(
    request: Request,
    project_id: str,
    batch_id: str | None = Query(default=None),
    parse_status: str | None = Query(default=None),
    query: str | None = Query(default=None),
) -> StreamingResponse:
    project_uuid = _parse_project_id(project_id)
    require_project_role(request, project_uuid, allowed_roles={"admin", "editor", "executor"})
    service = InteractionDataService(request)
    normalized_batch_id = _cleanup_optional_text(batch_id)
    normalized_parse_status = _cleanup_optional_text(parse_status)
    normalized_query = _cleanup_optional_text(query)
    items, _total = await service.list_all_documents_for_export(
        project_id,
        batch_id=normalized_batch_id,
        parse_status=normalized_parse_status,
        query=normalized_query,
        max_items=MAX_TESTCASE_DOCUMENT_EXPORT_ROWS,
    )
    enriched_items: list[dict[str, Any]] = []
    for item in items:
        document_id = _cleanup_optional_text(item.get("id"))
        related_cases_count = 0
        if document_id:
            relations = await service.get_document_relations(project_id, document_id)
            related_cases_count = int(relations.get("related_cases_count") or 0)
        enriched_items.append({**item, "related_cases_count": related_cases_count})
    filename, workbook_bytes = build_testcase_documents_workbook(
        project_id=project_id,
        documents=enriched_items,
        filters={
            "batch_id": normalized_batch_id,
            "parse_status": normalized_parse_status,
            "query": normalized_query,
        },
    )
    return StreamingResponse(
        BytesIO(workbook_bytes),
        media_type=TESTCASE_DOCUMENT_EXPORT_MEDIA_TYPE,
        headers={"Content-Disposition": build_document_content_disposition(filename)},
    )


@router.get("/projects/{project_id}/testcase/documents/{document_id}")
async def get_testcase_document(
    request: Request,
    project_id: str,
    document_id: str,
) -> dict[str, Any]:
    project_uuid = _parse_project_id(project_id)
    require_project_role(request, project_uuid, allowed_roles={"admin", "editor", "executor"})
    service = InteractionDataService(request)
    return await service.get_document(project_id, document_id)


@router.get("/projects/{project_id}/testcase/documents/{document_id}/relations")
async def get_testcase_document_relations(
    request: Request,
    project_id: str,
    document_id: str,
) -> dict[str, Any]:
    project_uuid = _parse_project_id(project_id)
    require_project_role(request, project_uuid, allowed_roles={"admin", "editor", "executor"})
    service = InteractionDataService(request)
    return await service.get_document_relations(project_id, document_id)


@router.get("/projects/{project_id}/testcase/batches/{batch_id}")
async def get_testcase_batch_detail(
    request: Request,
    project_id: str,
    batch_id: str,
    document_limit: int = Query(default=100, ge=1, le=500),
    document_offset: int = Query(default=0, ge=0),
    case_limit: int = Query(default=50, ge=1, le=500),
    case_offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    project_uuid = _parse_project_id(project_id)
    require_project_role(request, project_uuid, allowed_roles={"admin", "editor", "executor"})
    normalized_batch_id = _cleanup_optional_text(batch_id)
    if not normalized_batch_id:
        raise HTTPException(status_code=400, detail="invalid_batch_id")
    service = InteractionDataService(request)
    return await service.get_batch_detail(
        project_id,
        normalized_batch_id,
        document_limit=document_limit,
        document_offset=document_offset,
        case_limit=case_limit,
        case_offset=case_offset,
    )


@router.get("/projects/{project_id}/testcase/documents/{document_id}/preview")
async def preview_testcase_document(
    request: Request,
    project_id: str,
    document_id: str,
) -> StreamingResponse:
    project_uuid = _parse_project_id(project_id)
    require_project_role(request, project_uuid, allowed_roles={"admin", "editor", "executor"})
    service = InteractionDataService(request)
    payload, headers = await service.get_document_binary(project_id, document_id, inline=True)
    response_headers = {}
    for key in ("content-disposition",):
        value = headers.get(key)
        if value:
            response_headers["Content-Disposition"] = value
    return StreamingResponse(
        BytesIO(payload),
        media_type=headers.get("content-type", "application/octet-stream"),
        headers=response_headers,
    )


@router.get("/projects/{project_id}/testcase/documents/{document_id}/download")
async def download_testcase_document(
    request: Request,
    project_id: str,
    document_id: str,
) -> StreamingResponse:
    project_uuid = _parse_project_id(project_id)
    require_project_role(request, project_uuid, allowed_roles={"admin", "editor", "executor"})
    service = InteractionDataService(request)
    payload, headers = await service.get_document_binary(project_id, document_id, inline=False)
    response_headers = {}
    for key in ("content-disposition",):
        value = headers.get(key)
        if value:
            response_headers["Content-Disposition"] = value
    return StreamingResponse(
        BytesIO(payload),
        media_type=headers.get("content-type", "application/octet-stream"),
        headers=response_headers,
    )
