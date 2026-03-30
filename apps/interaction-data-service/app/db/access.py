from __future__ import annotations

import uuid

from app.db.models import TestCaseDocument, TestCaseRecord
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session


def parse_uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(value)
    except (ValueError, TypeError):
        return None


def create_test_case_document(
    session: Session,
    *,
    project_id: uuid.UUID,
    batch_id: str | None,
    filename: str,
    content_type: str,
    storage_path: str | None,
    source_kind: str,
    parse_status: str,
    summary_for_model: str,
    parsed_text: str | None,
    structured_data: dict | None,
    provenance: dict,
    confidence: float | None,
    error: dict | None,
) -> TestCaseDocument:
    row = TestCaseDocument(
        project_id=project_id,
        batch_id=batch_id,
        filename=filename,
        content_type=content_type,
        storage_path=storage_path,
        source_kind=source_kind,
        parse_status=parse_status,
        summary_for_model=summary_for_model,
        parsed_text=parsed_text,
        structured_data=structured_data,
        provenance=provenance,
        confidence=confidence,
        error=error,
    )
    session.add(row)
    session.flush()
    return row


def list_test_case_documents(
    session: Session,
    *,
    project_id: uuid.UUID | None,
    batch_id: str | None,
    limit: int,
    offset: int,
) -> tuple[list[TestCaseDocument], int]:
    base_stmt = select(TestCaseDocument)
    if project_id is not None:
        base_stmt = base_stmt.where(TestCaseDocument.project_id == project_id)
    if isinstance(batch_id, str) and batch_id.strip():
        base_stmt = base_stmt.where(TestCaseDocument.batch_id == batch_id.strip())
    stmt = base_stmt.order_by(desc(TestCaseDocument.created_at)).offset(offset).limit(limit)
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    rows = list(session.scalars(stmt).all())
    total = int(session.scalar(count_stmt) or 0)
    return rows, total


def get_test_case_document(
    session: Session, document_id: uuid.UUID
) -> TestCaseDocument | None:
    return session.get(TestCaseDocument, document_id)


def create_test_case(
    session: Session,
    *,
    project_id: uuid.UUID,
    batch_id: str | None,
    case_id: str | None,
    title: str,
    description: str,
    status: str,
    module_name: str | None,
    priority: str | None,
    source_document_ids: list[str],
    content_json: dict,
) -> TestCaseRecord:
    row = TestCaseRecord(
        project_id=project_id,
        batch_id=batch_id,
        case_id=case_id,
        title=title,
        description=description,
        status=status,
        module_name=module_name,
        priority=priority,
        source_document_ids=source_document_ids,
        content_json=content_json,
    )
    session.add(row)
    session.flush()
    return row


def list_test_cases(
    session: Session,
    *,
    project_id: uuid.UUID | None,
    status: str | None,
    batch_id: str | None,
    limit: int,
    offset: int,
) -> tuple[list[TestCaseRecord], int]:
    base_stmt = select(TestCaseRecord)
    if project_id is not None:
        base_stmt = base_stmt.where(TestCaseRecord.project_id == project_id)
    if isinstance(status, str) and status.strip():
        base_stmt = base_stmt.where(TestCaseRecord.status == status.strip())
    if isinstance(batch_id, str) and batch_id.strip():
        base_stmt = base_stmt.where(TestCaseRecord.batch_id == batch_id.strip())
    stmt = base_stmt.order_by(desc(TestCaseRecord.created_at)).offset(offset).limit(limit)
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    rows = list(session.scalars(stmt).all())
    total = int(session.scalar(count_stmt) or 0)
    return rows, total


def get_test_case(session: Session, test_case_id: uuid.UUID) -> TestCaseRecord | None:
    return session.get(TestCaseRecord, test_case_id)


def update_test_case(
    session: Session,
    row: TestCaseRecord,
    *,
    title: str | None,
    description: str | None,
    status: str | None,
    module_name: str | None,
    priority: str | None,
    source_document_ids: list[str] | None,
    content_json: dict | None,
) -> TestCaseRecord:
    if title is not None:
        row.title = title
    if description is not None:
        row.description = description
    if status is not None:
        row.status = status
    if module_name is not None:
        row.module_name = module_name
    if priority is not None:
        row.priority = priority
    if source_document_ids is not None:
        row.source_document_ids = source_document_ids
    if content_json is not None:
        row.content_json = content_json
    session.flush()
    return row


def delete_test_case(session: Session, row: TestCaseRecord) -> None:
    session.delete(row)
    session.flush()
