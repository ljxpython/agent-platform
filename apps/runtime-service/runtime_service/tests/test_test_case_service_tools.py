from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from runtime_service.services.test_case_service.schemas import PersistTestCaseItem
from runtime_service.services.test_case_service.tools import (
    _build_test_case_idempotency_keys,
)


def test_build_test_case_idempotency_keys_prefers_case_id() -> None:
    first = PersistTestCaseItem(
        case_id="TC-LOGIN-001",
        title="登录成功",
        module_name="认证中心",
        test_type="functional",
        steps=["输入正确账号密码"],
        expected_results=["登录成功"],
    )
    second = PersistTestCaseItem(
        case_id=" tc-login-001 ",
        title="登录成功-文案调整",
        module_name="账号服务",
        test_type="regression",
        steps=["输入正确账号密码并点击登录"],
        expected_results=["进入首页"],
    )

    first_run_keys = _build_test_case_idempotency_keys([first])
    second_run_keys = _build_test_case_idempotency_keys([second])

    assert len(first_run_keys) == 1
    assert len(second_run_keys) == 1
    assert first_run_keys[0] == second_run_keys[0]


def test_build_test_case_idempotency_keys_falls_back_to_semantic_identity() -> None:
    first = PersistTestCaseItem(
        title="登录失败",
        module_name="认证中心",
        test_type="functional",
        steps=["输入错误密码"],
        expected_results=["提示密码错误"],
    )
    second = PersistTestCaseItem(
        title="  登录失败  ",
        module_name="认证中心",
        test_type="functional",
        steps=["输入错误密码并点击登录"],
        expected_results=["展示失败提示"],
    )

    keys = _build_test_case_idempotency_keys([first, second])

    assert len(keys) == 2
    assert keys[0] != keys[1]

    rerun_keys = _build_test_case_idempotency_keys([first, second])
    assert rerun_keys == keys
