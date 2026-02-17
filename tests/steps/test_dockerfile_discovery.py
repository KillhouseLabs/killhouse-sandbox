"""BDD step definitions for Dockerfile discovery."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from src.detection.detector import StackDetector

FEATURE = "../features/detection/dockerfile_discovery.feature"

SERVICE_DOCKERFILE = 'FROM node:20\nEXPOSE 3000\nCMD ["node", "server.js"]\n'
BUILDER_DOCKERFILE = "FROM ubuntu:22.04\nRUN apt-get update && apt-get install -y build-essential\n"
COMPOSE_WITH_DOCKERFILE_REF = (
    "services:\n"
    "  app:\n"
    "    build:\n"
    "      context: .\n"
    "      dockerfile: infra/Dockerfile\n"
    "  db:\n"
    "    image: postgres:15\n"
)


@scenario(FEATURE, "루트 Dockerfile 감지")
def test_root_dockerfile():
    pass


@scenario(FEATURE, "하위 디렉토리 Dockerfile 감지")
def test_subdirectory_dockerfile():
    pass


@scenario(FEATURE, "루트 Dockerfile이 하위 디렉토리보다 우선")
def test_root_priority():
    pass


@scenario(FEATURE, ".devcontainer Dockerfile은 제외")
def test_devcontainer_excluded():
    pass


@scenario(FEATURE, "EXPOSE/CMD 없는 빌더 이미지 제외")
def test_builder_image_excluded():
    pass


@scenario(FEATURE, "docker-compose.yml에서 Dockerfile 경로 참조")
def test_compose_reference():
    pass


@scenario(FEATURE, "Dockerfile이 아예 없는 레포")
def test_no_dockerfile():
    pass


@pytest.fixture
def context():
    """Shared context between steps."""
    ctx = {}
    yield ctx
    if "tmpdir" in ctx:
        ctx["tmpdir"].cleanup()


@given("레포가 클론되어 있다")
def repo_cloned(context):
    td = TemporaryDirectory()
    context["tmpdir"] = td
    context["repo_path"] = Path(td.name)


@given("루트에 서비스 Dockerfile이 있다")
def root_service_dockerfile(context):
    (context["repo_path"] / "Dockerfile").write_text(SERVICE_DOCKERFILE)


@given(parsers.parse('"{dirname}" 디렉토리에 서비스 Dockerfile이 있다'))
def subdirectory_service_dockerfile(context, dirname):
    dirpath = context["repo_path"] / dirname
    dirpath.mkdir(parents=True, exist_ok=True)
    (dirpath / "Dockerfile").write_text(SERVICE_DOCKERFILE)


@given(parsers.parse('"{dirname}" 디렉토리에 빌더 전용 Dockerfile이 있다'))
def subdirectory_builder_dockerfile(context, dirname):
    dirpath = context["repo_path"] / dirname
    dirpath.mkdir(parents=True, exist_ok=True)
    (dirpath / "Dockerfile").write_text(BUILDER_DOCKERFILE)


@given("docker-compose.yml에 Dockerfile 경로가 참조되어 있다")
def compose_with_dockerfile_ref(context):
    (context["repo_path"] / "docker-compose.yml").write_text(COMPOSE_WITH_DOCKERFILE_REF)


@given("루트에 소스 파일만 있다")
def only_source_files(context):
    (context["repo_path"] / "package.json").write_text("{}")


@when("Dockerfile을 탐색한다")
def find_dockerfile(context):
    detector = StackDetector(context["repo_path"])
    context["result"] = detector._find_dockerfile()


@then(parsers.parse('"{path}" 경로가 반환된다'))
def path_returned(context, path):
    assert context["result"] == path


@then("Dockerfile이 발견되지 않는다")
def no_dockerfile_found(context):
    assert context["result"] is None
