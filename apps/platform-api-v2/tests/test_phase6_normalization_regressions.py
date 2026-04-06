from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.modules.runtime_gateway.application.service import RuntimeGatewayService
from app.modules.testcase.application.service import TestcaseService


class RuntimeGatewayNormalizationRegressionTest(unittest.IsolatedAsyncioTestCase):
    async def test_create_global_run_normalizes_assistant_id(self) -> None:
        upstream = SimpleNamespace(create_global_run=AsyncMock(return_value={"ok": True}))
        service = RuntimeGatewayService(
            session_factory=None,
            upstream=upstream,
        )
        service._prepare_project_scope = AsyncMock()  # type: ignore[method-assign]
        service._assert_runtime_target_allowed = AsyncMock()  # type: ignore[method-assign]

        payload = await service.create_global_run(
            actor=SimpleNamespace(),
            project_id="project-1",
            payload={"assistant_id": " assistant-1 "},
        )

        self.assertEqual(payload, {"ok": True})
        service._assert_runtime_target_allowed.assert_awaited_once_with(
            project_id="project-1",
            assistant_id="assistant-1",
        )

    async def test_cancel_runs_ignores_blank_thread_id(self) -> None:
        upstream = SimpleNamespace(cancel_runs=AsyncMock(return_value={"ok": True}))
        service = RuntimeGatewayService(
            session_factory=None,
            upstream=upstream,
        )
        service._prepare_project_scope = AsyncMock()  # type: ignore[method-assign]
        service._load_thread = AsyncMock()  # type: ignore[method-assign]

        payload = await service.cancel_runs(
            actor=SimpleNamespace(),
            project_id="project-1",
            payload={"thread_id": "   ", "status": "pending"},
        )

        self.assertEqual(payload, {"ok": True})
        service._load_thread.assert_not_called()


class TestcaseNormalizationRegressionTest(unittest.TestCase):
    def test_ensure_project_match_normalizes_project_id(self) -> None:
        service = TestcaseService(
            session_factory=None,
            upstream=SimpleNamespace(),
        )

        payload = service._ensure_project_match(
            {"project_id": " project-1 ", "id": "doc-1"},
            project_id="project-1",
            code="document_not_found",
        )

        self.assertEqual(payload["id"], "doc-1")


if __name__ == "__main__":
    unittest.main()
