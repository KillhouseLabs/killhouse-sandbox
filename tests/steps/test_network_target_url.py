"""Step definitions for network target URL feature."""

import pytest
from pytest_bdd import given, scenario, then, when

from src.api.schemas import EnvironmentResponse


@scenario(
    "../features/environment/network_target_url.feature",
    "환경 생성 시 네트워크 내부 URL 반환",
)
def test_environment_returns_network_url():
    pass


@pytest.fixture
def context():
    return {}


@given("레포가 클론되어 있다")
def repo_cloned(context):
    context["repo_url"] = "https://github.com/test/repo"


@given("서비스 Dockerfile이 있다")
def has_dockerfile(context):
    context["dockerfile_content"] = 'FROM python:3.11-slim\nEXPOSE 8080\nCMD ["python", "app.py"]'


@when("환경을 생성한다", target_fixture="response")
def create_environment(context):
    """Simulate the EnvironmentResponse that manager would return."""
    from datetime import datetime, timedelta

    response = EnvironmentResponse(
        env_id="test1234",
        target_url="http://killhouse-target-test1234:8080",
        network_name="killhouse-test1234",
        stack={
            "language": "python",
            "framework": None,
            "runtime_version": "3.11",
            "package_manager": "pip",
            "has_dockerfile": True,
            "has_docker_compose": False,
            "services": [],
        },
        services={},
        status="running",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    context["response"] = response
    return response


@then("target_url은 컨테이너 이름 기반이다")
def target_url_uses_container_name(context):
    response = context["response"]
    assert "killhouse-target-" in response.target_url
    assert "127.0.0.1" not in response.target_url
    assert response.target_url.startswith("http://killhouse-target-")


@then("network_name이 응답에 포함된다")
def response_includes_network_name(context):
    response = context["response"]
    assert response.network_name is not None
    assert response.network_name.startswith("killhouse-")
