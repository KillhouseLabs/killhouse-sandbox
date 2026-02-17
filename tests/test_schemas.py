"""Tests for API schema extensions."""

from src.api.schemas import CreateEnvironmentRequest, DetectedStack, EnvironmentResponse


class TestCreateEnvironmentRequest:
    """CreateEnvironmentRequest에 dockerfile_content, compose_content 필드 추가 검증."""

    def test_request_with_repo_url_only(self):
        req = CreateEnvironmentRequest(repo_url="https://github.com/test/repo")
        assert req.repo_url == "https://github.com/test/repo"
        assert req.dockerfile_content is None
        assert req.compose_content is None

    def test_request_with_dockerfile_content(self):
        req = CreateEnvironmentRequest(
            repo_url="https://github.com/test/repo",
            dockerfile_content='FROM python:3.11-slim\nCMD ["python", "app.py"]',
        )
        assert req.dockerfile_content is not None
        assert "FROM" in req.dockerfile_content

    def test_request_with_compose_content(self):
        compose = "services:\n  db:\n    image: postgres:15\n"
        req = CreateEnvironmentRequest(
            repo_url="https://github.com/test/repo",
            compose_content=compose,
        )
        assert req.compose_content is not None
        assert "postgres" in req.compose_content

    def test_request_with_dockerfile_and_compose(self):
        req = CreateEnvironmentRequest(
            repo_url="https://github.com/test/repo",
            dockerfile_content='FROM node:20\nCMD ["node", "index.js"]',
            compose_content="services:\n  redis:\n    image: redis:7\n",
        )
        assert req.dockerfile_content is not None
        assert req.compose_content is not None

    def test_request_without_repo_url(self):
        req = CreateEnvironmentRequest(
            dockerfile_content='FROM python:3.11\nCMD ["python", "main.py"]',
        )
        assert req.repo_url is None
        assert req.dockerfile_content is not None


class TestEnvironmentResponse:
    """EnvironmentResponse에 network_name 필드 추가 검증."""

    def test_environment_response_includes_network_name(self):
        from datetime import datetime, timedelta

        response = EnvironmentResponse(
            env_id="test1234",
            target_url="http://killhouse-target-test1234:8080",
            network_name="killhouse-test1234",
            stack=DetectedStack(
                language="python",
                framework=None,
                runtime_version=None,
                package_manager="pip",
            ),
            services={},
            status="running",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        assert response.network_name == "killhouse-test1234"
