"""Integration tests: 浩鲸研发云代理 API（dev_iwhalecloud 路由）。

- 校验路由注册与 OpenAPI 暴露
- 校验请求体缺失时的 422 / 业务 errorcode
- 对依赖 httpx 的上游调用使用 mock，避免访问真实 dev.iwhalecloud.com

不默认执行 Playwright 登录类接口（避免拉起浏览器）；仅做入参校验类测试。
"""

from __future__ import annotations

import json

import httpx
import pytest
from unittest.mock import patch

from synapse.api.routes import dev_iwhalecloud
from synapse.api.server import create_app


@pytest.fixture
async def client():
    app = create_app()
    app.state.agent = None
    app.state.session_manager = None
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as c:
        yield c


class TestIwhalecloudOpenAPI:
    async def test_openapi_lists_dev_iwhalecloud_post_routes(self, client):
        resp = await client.get("/openapi.json")
        assert resp.status_code == 200
        spec = resp.json()
        paths = spec.get("paths") or {}
        iwhale = [p for p in paths if p.startswith("/api/dev/iwhalecloud")]
        assert len(iwhale) >= 30, f"expected >=30 iwhalecloud paths, got {len(iwhale)}: {sorted(iwhale)}"
        for path in iwhale:
            post = (paths[path] or {}).get("post")
            assert post is not None, f"missing POST for {path}"

    # 注意：不要对全部路由无脑 POST {} —— 例如 get_product_list 的 body 有默认值，
    # 空对象会触发对 dev.iwhalecloud.com 的真实 HTTP 调用（长超时）。路由存在性以 OpenAPI 为准即可。


class TestGetProjectList:
    async def test_empty_token_returns_business_error(self, client):
        resp = await client.post(
            "/api/dev/iwhalecloud/get_project_list",
            json={"token": "", "cookies": ""},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("errorcode") == 400
        assert "token" in (data.get("message") or "").lower() or "空" in (data.get("message") or "")

    async def test_missing_required_fields_422(self, client):
        resp = await client.post("/api/dev/iwhalecloud/get_project_list", json={})
        assert resp.status_code == 422

    async def test_upstream_json_array_success_simplified(self, client):
        """mock 上游返回 JSON 数组时，路由精简为 projectId/projectName/projectCode。"""

        class _MockClient:
            def __init__(self, *a, **k):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return None

            async def get(self, url, headers=None, params=None):
                class _Resp:
                    status_code = 200
                    url = "https://dev.iwhalecloud.com/portal/zcm-cmdb/v1/projects/all"
                    text = json.dumps(
                        [
                            {"projectId": 1, "projectName": "P1", "projectCode": "C1", "extra": "x"},
                        ],
                        ensure_ascii=False,
                    )

                    def json(self):
                        return json.loads(self.text)

                return _Resp()

        with patch.object(dev_iwhalecloud.httpx, "AsyncClient", _MockClient):
            resp = await client.post(
                "/api/dev/iwhalecloud/get_project_list",
                json={"token": "t", "cookies": "c=1"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("errorcode") == 0
        lst = data.get("data") or []
        assert len(lst) == 1
        assert lst[0].get("projectId") == 1
        assert lst[0].get("projectName") == "P1"
        assert lst[0].get("projectCode") == "C1"
        assert "extra" not in lst[0]


class TestLoginAndTokenHelpers:
    async def test_login_guide_missing_password_422(self, client):
        resp = await client.post(
            "/api/dev/iwhalecloud/login",
            json={"purpose": "guide", "username": "u001"},
        )
        assert resp.status_code == 422

    async def test_get_token_and_cookies_guide_missing_password_422(self, client):
        resp = await client.post(
            "/api/dev/iwhalecloud/get_token_and_cookies",
            json={"purpose": "guide", "username": "u001"},
        )
        assert resp.status_code == 422


class TestCreateTaskValidation:
    async def test_empty_body_422(self, client):
        resp = await client.post("/api/dev/iwhalecloud/create_task", json={})
        assert resp.status_code == 422

    async def test_minimal_invalid_body_returns_business_error(self, client):
        """字段齐全但业务校验失败时返回 errorcode 非 0（不发起外呼）。"""
        body = {
            "taskNo": "",
            "taskTitle": "t",
            "comments": "c",
            "ownerUserCode": "o",
            "projectId": 1,
            "productModuleName": None,
            "branchVersionName": "br",
            "mainBranchVersionTaskNo": "",
            "taskClassification": "FUNCTION",
            "taskPri": 5,
            "patchName": "p",
            "x-csrf-token": "",
            "cookie": "",
            "userId": 1,
            "taskImpactList": [{"taskImpactId": 1, "taskImpactDesc": "d"}],
            "performanceImpact": "a",
            "functionalImpact": "b",
            "cfgChangeDescription": "c",
            "upgradeRisk": "d",
            "securityImpact": "e",
            "compatibilityImpact": "f",
        }
        resp = await client.post("/api/dev/iwhalecloud/create_task", json=body)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("errorcode") != 0
        assert data.get("message")


class TestGetProductVersionList:
    async def test_empty_token_returns_business_error(self, client):
        resp = await client.post(
            "/api/dev/iwhalecloud/get_product_version_list",
            json={"token": "", "cookies": ""},
        )
        assert resp.status_code == 200
        assert resp.json().get("errorcode") == 400
