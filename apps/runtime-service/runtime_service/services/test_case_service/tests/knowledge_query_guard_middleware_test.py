from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

from langchain.messages import HumanMessage

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from runtime_service.services.test_case_service.knowledge_query_guard_middleware import (  # noqa: E402
    TestCaseKnowledgeQueryGuardMiddleware,
)


def test_requires_guard_for_plain_business_generation_without_attachments() -> None:
    middleware = TestCaseKnowledgeQueryGuardMiddleware()
    request = SimpleNamespace(
        messages=[HumanMessage(content="请生成支付模块测试用例")],
        state={},
    )

    guarded, latest_user_text = middleware._requires_guard(request)

    assert guarded is True
    assert latest_user_text == "请生成支付模块测试用例"


def test_requires_guard_skips_when_multimodal_state_already_has_attachments() -> None:
    middleware = TestCaseKnowledgeQueryGuardMiddleware()
    request = SimpleNamespace(
        messages=[
            HumanMessage(
                content=[
                    {"type": "text", "text": "请基于这个PDF生成测试用例"},
                    {
                        "type": "text",
                        "text": "[附件: 接口文档.pdf; kind=pdf; status=parsed] 摘要: PDF 已完成文本抽取",
                    },
                ]
            )
        ],
        state={
            "multimodal_attachments": [
                {
                    "attachment_id": "att_1",
                    "kind": "pdf",
                    "status": "parsed",
                    "summary_for_model": "PDF 已完成文本抽取",
                }
            ]
        },
    )

    guarded, latest_user_text = middleware._requires_guard(request)

    assert guarded is False
    assert latest_user_text == ""
