from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from langchain.tools import ToolRuntime
from langchain_core.tools import tool
from runtime_service.integrations import (
    InteractionDataServiceClient,
    build_interaction_data_service_config,
)
from runtime_service.runtime.context import RuntimeContext
from runtime_service.runtime.options import context_to_mapping, read_configurable
from runtime_service.services.test_case_service.schemas import (
    PersistTestCaseItem,
    TestCaseServiceConfig,
)

TEST_CASE_DOCUMENTS_PATH = "/api/test-case-service/documents"
TEST_CASES_PATH = "/api/test-case-service/test-cases"


def _coerce_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_mapping(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    return {str(key): item for key, item in value.items()}


def _coerce_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = _coerce_optional_text(item)
        if text:
            items.append(text)
    return items


def _get_runtime_state(
    runtime: ToolRuntime[RuntimeContext | Mapping[str, Any] | None, dict[str, Any]],
) -> dict[str, Any]:
    state = runtime.state if hasattr(runtime, "state") else {}
    return state if isinstance(state, dict) else {}


def _get_runtime_context_mapping(
    runtime: ToolRuntime[RuntimeContext | Mapping[str, Any] | None, dict[str, Any]],
) -> Mapping[str, Any]:
    return context_to_mapping(runtime.context)


def _resolve_project_id(
    runtime: ToolRuntime[RuntimeContext | Mapping[str, Any] | None, dict[str, Any]],
    service_config: TestCaseServiceConfig,
) -> str:
    context_data = _get_runtime_context_mapping(runtime)
    configurable = read_configurable(runtime.config)
    metadata = runtime.config.get("metadata")
    metadata_map = metadata if isinstance(metadata, Mapping) else {}
    state = _get_runtime_state(runtime)
    for candidate in (
        context_data.get("project_id"),
        configurable.get("project_id"),
        configurable.get("x-project-id"),
        metadata_map.get("project_id"),
        state.get("project_id"),
    ):
        text = _coerce_optional_text(candidate)
        if text:
            return text
    return service_config.default_project_id


def _resolve_batch_id(
    runtime: ToolRuntime[RuntimeContext | Mapping[str, Any] | None, dict[str, Any]],
) -> str:
    configurable = read_configurable(runtime.config)
    metadata = runtime.config.get("metadata")
    metadata_map = metadata if isinstance(metadata, Mapping) else {}
    state = _get_runtime_state(runtime)
    thread_id = _coerce_optional_text(configurable.get("thread_id") or state.get("thread_id"))
    run_id = _coerce_optional_text(runtime.config.get("run_id"))
    explicit = _coerce_optional_text(
        configurable.get("batch_id") or metadata_map.get("batch_id") or state.get("batch_id")
    )
    if explicit:
        return explicit
    suffix = thread_id or run_id or "default"
    return f"test-case-service:{suffix}"


def _resolve_runtime_meta(
    runtime: ToolRuntime[RuntimeContext | Mapping[str, Any] | None, dict[str, Any]],
) -> dict[str, Any]:
    configurable = read_configurable(runtime.config)
    state = _get_runtime_state(runtime)
    return {
        "thread_id": _coerce_optional_text(configurable.get("thread_id") or state.get("thread_id")),
        "run_id": _coerce_optional_text(runtime.config.get("run_id")),
        "agent_key": "test_case_service",
    }


def _build_document_payloads(
    *,
    state: dict[str, Any],
    project_id: str,
    batch_id: str,
) -> list[dict[str, Any]]:
    attachments = state.get("multimodal_attachments")
    if not isinstance(attachments, list):
        return []
    multimodal_summary = _coerce_optional_text(state.get("multimodal_summary")) or ""
    payloads: list[dict[str, Any]] = []
    for attachment in attachments:
        if not isinstance(attachment, Mapping):
            continue
        filename = (
            _coerce_optional_text(attachment.get("name"))
            or _coerce_optional_text(attachment.get("attachment_id"))
            or "attachment"
        )
        content_type = _coerce_optional_text(attachment.get("mime_type")) or "application/octet-stream"
        source_kind = (
            _coerce_optional_text(attachment.get("kind"))
            or _coerce_optional_text(attachment.get("source_type"))
            or "upload"
        )
        parse_status = _coerce_optional_text(attachment.get("status")) or "parsed"
        payloads.append(
            {
                "project_id": project_id,
                "batch_id": batch_id,
                "filename": filename,
                "content_type": content_type,
                "storage_path": None,
                "source_kind": source_kind,
                "parse_status": parse_status,
                "summary_for_model": (
                    _coerce_optional_text(attachment.get("summary_for_model"))
                    or multimodal_summary
                    or f"Parsed {source_kind} attachment."
                ),
                "parsed_text": _coerce_optional_text(attachment.get("parsed_text")),
                "structured_data": _coerce_mapping(attachment.get("structured_data")),
                "provenance": _coerce_mapping(attachment.get("provenance")) or {},
                "confidence": attachment.get("confidence")
                if isinstance(attachment.get("confidence"), (int, float))
                else None,
                "error": _coerce_mapping(attachment.get("error")),
            }
        )
    return payloads


def _persist_documents(
    *,
    client: InteractionDataServiceClient,
    state: dict[str, Any],
    project_id: str,
    batch_id: str,
) -> tuple[str, list[dict[str, Any]]]:
    payloads = _build_document_payloads(state=state, project_id=project_id, batch_id=batch_id)
    if not payloads:
        return "no_attachments", []
    persisted: list[dict[str, Any]] = []
    for payload in payloads:
        persisted.append(client.post_json(TEST_CASE_DOCUMENTS_PATH, payload))
    return "persisted", persisted


def _merge_content_json(
    item: PersistTestCaseItem,
    *,
    bundle_title: str,
    bundle_summary: str,
    quality_review: dict[str, Any],
    export_format: str | None,
    runtime_meta: dict[str, Any],
    batch_id: str,
    source_document_ids: list[str],
) -> dict[str, Any]:
    content = dict(item.content_json)
    content.setdefault("case_id", item.case_id)
    content.setdefault("title", item.title)
    content.setdefault("description", item.description)
    content.setdefault("module_name", item.module_name)
    content.setdefault("priority", item.priority)
    content.setdefault("test_type", item.test_type)
    content.setdefault("design_technique", item.design_technique)
    content.setdefault("preconditions", list(item.preconditions))
    content.setdefault("steps", list(item.steps))
    content.setdefault("test_data", dict(item.test_data))
    content.setdefault("expected_results", list(item.expected_results))
    content.setdefault("remarks", item.remarks)
    meta = content.get("meta") if isinstance(content.get("meta"), dict) else {}
    meta.update(
        {
            "bundle_title": bundle_title,
            "bundle_summary": bundle_summary,
            "quality_review": quality_review,
            "export_format": export_format,
            "batch_id": batch_id,
            "source_document_ids": source_document_ids,
            **runtime_meta,
        }
    )
    content["meta"] = meta
    return content


def _build_test_case_payloads(
    *,
    items: list[PersistTestCaseItem],
    project_id: str,
    batch_id: str,
    source_document_ids: list[str],
    bundle_title: str,
    bundle_summary: str,
    quality_review: dict[str, Any],
    export_format: str | None,
    runtime_meta: dict[str, Any],
) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for item in items:
        content_json = _merge_content_json(
            item,
            bundle_title=bundle_title,
            bundle_summary=bundle_summary,
            quality_review=quality_review,
            export_format=export_format,
            runtime_meta=runtime_meta,
            batch_id=batch_id,
            source_document_ids=source_document_ids,
        )
        payloads.append(
            {
                "project_id": project_id,
                "batch_id": batch_id,
                "case_id": item.case_id,
                "title": item.title,
                "description": item.description,
                "status": item.status,
                "module_name": item.module_name,
                "priority": item.priority,
                "source_document_ids": source_document_ids,
                "content_json": content_json,
            }
        )
    return payloads


def build_test_case_service_tools(service_config: TestCaseServiceConfig) -> list[Any]:
    @tool(
        "persist_test_case_results",
        description=(
            "Persist the final formatted test cases and uploaded requirement documents to "
            "interaction-data-service. Use this only after requirement analysis, strategy, "
            "test-case design, quality review, and output formatting are complete."
        ),
    )
    def persist_test_case_results(
        bundle_title: str,
        runtime: ToolRuntime[RuntimeContext | Mapping[str, Any] | None, dict[str, Any]],
        bundle_summary: str = "",
        test_cases: list[PersistTestCaseItem] | None = None,
        quality_review: dict[str, Any] | None = None,
        export_format: str | None = None,
    ) -> str:
        if not service_config.persistence_enabled:
            return json.dumps(
                {
                    "status": "skipped_persistence_disabled",
                    "reason": "test_case_persistence_enabled=false",
                },
                ensure_ascii=False,
            )
        normalized_cases = test_cases or []
        if not normalized_cases:
            return json.dumps(
                {
                    "status": "skipped_empty_test_cases",
                    "reason": "no_test_cases",
                },
                ensure_ascii=False,
            )
        project_id = _resolve_project_id(runtime, service_config)
        batch_id = _resolve_batch_id(runtime)
        runtime_meta = _resolve_runtime_meta(runtime)
        state = _get_runtime_state(runtime)
        client = InteractionDataServiceClient(build_interaction_data_service_config(runtime.config))
        if not client.is_configured:
            return json.dumps(
                {
                    "status": "skipped_remote_not_configured",
                    "project_id": project_id,
                    "batch_id": batch_id,
                    "test_case_count": len(normalized_cases),
                },
                ensure_ascii=False,
            )

        document_status, persisted_documents = _persist_documents(
            client=client,
            state=state,
            project_id=project_id,
            batch_id=batch_id,
        )
        source_document_ids = _coerce_string_list([item.get("id") for item in persisted_documents])
        quality_payload = quality_review or {}
        test_case_payloads = _build_test_case_payloads(
            items=normalized_cases,
            project_id=project_id,
            batch_id=batch_id,
            source_document_ids=source_document_ids,
            bundle_title=bundle_title,
            bundle_summary=bundle_summary,
            quality_review=quality_payload,
            export_format=export_format,
            runtime_meta=runtime_meta,
        )
        persisted_test_cases = [client.post_json(TEST_CASES_PATH, payload) for payload in test_case_payloads]
        return json.dumps(
            {
                "status": "persisted",
                "project_id": project_id,
                "batch_id": batch_id,
                "document_status": document_status,
                "persisted_document_count": len(persisted_documents),
                "persisted_document_ids": source_document_ids,
                "persisted_test_case_count": len(persisted_test_cases),
                "persisted_test_case_ids": _coerce_string_list(
                    [item.get("id") for item in persisted_test_cases]
                ),
            },
            ensure_ascii=False,
        )

    return [persist_test_case_results]


__all__ = ["build_test_case_service_tools"]
