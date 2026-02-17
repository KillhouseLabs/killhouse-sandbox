"""Tests for stack detection."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from src.detection.detector import StackDetector


class TestStackDetector:
    """Test cases for StackDetector."""

    def test_detect_javascript_express(self):
        """Test detection of Express.js project."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create package.json
            package_json = {
                "name": "test-app",
                "dependencies": {
                    "express": "^4.18.0",
                },
            }
            (repo_path / "package.json").write_text(json.dumps(package_json))

            detector = StackDetector(repo_path)
            stack = detector.detect()

            assert stack.language == "javascript"
            assert stack.framework == "express"
            assert stack.package_manager == "npm"

    def test_detect_javascript_nextjs(self):
        """Test detection of Next.js project."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            package_json = {
                "name": "test-app",
                "dependencies": {
                    "next": "^14.0.0",
                    "react": "^18.0.0",
                },
            }
            (repo_path / "package.json").write_text(json.dumps(package_json))

            detector = StackDetector(repo_path)
            stack = detector.detect()

            assert stack.language == "javascript"
            assert stack.framework == "nextjs"

    def test_detect_python_fastapi(self):
        """Test detection of FastAPI project."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            requirements = "fastapi==0.100.0\nuvicorn==0.23.0\n"
            (repo_path / "requirements.txt").write_text(requirements)

            detector = StackDetector(repo_path)
            stack = detector.detect()

            assert stack.language == "python"
            assert stack.framework == "fastapi"
            assert stack.package_manager == "pip"

    def test_detect_python_django(self):
        """Test detection of Django project."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            requirements = "django==4.2.0\n"
            (repo_path / "requirements.txt").write_text(requirements)

            detector = StackDetector(repo_path)
            stack = detector.detect()

            assert stack.language == "python"
            assert stack.framework == "django"

    def test_detect_go_gin(self):
        """Test detection of Go Gin project."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            go_mod = """module example.com/app

go 1.21

require github.com/gin-gonic/gin v1.9.1
"""
            (repo_path / "go.mod").write_text(go_mod)

            detector = StackDetector(repo_path)
            stack = detector.detect()

            assert stack.language == "go"
            assert stack.framework == "gin"
            assert stack.runtime_version == "1.21"

    def test_detect_yarn_package_manager(self):
        """Test detection of Yarn package manager."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            package_json = {"name": "test-app", "dependencies": {"react": "^18.0.0"}}
            (repo_path / "package.json").write_text(json.dumps(package_json))
            (repo_path / "yarn.lock").write_text("")

            detector = StackDetector(repo_path)
            stack = detector.detect()

            assert stack.package_manager == "yarn"

    def test_detect_docker_presence(self):
        """Test detection of existing Dockerfile."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            package_json = {"name": "test-app", "dependencies": {"express": "^4.0.0"}}
            (repo_path / "package.json").write_text(json.dumps(package_json))
            (repo_path / "Dockerfile").write_text(
                "FROM node:20\nEXPOSE 3000\nCMD [\"node\", \"server.js\"]\n"
            )

            detector = StackDetector(repo_path)
            stack = detector.detect()

            assert stack.has_dockerfile is True
            assert stack.dockerfile_path == "Dockerfile"

    def test_detect_unknown_raises(self):
        """Test that unknown stack raises ValueError."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            detector = StackDetector(repo_path)

            with pytest.raises(ValueError, match="Unable to detect"):
                detector.detect()

    def test_detect_dockerfile_in_subdirectory(self):
        """Test that detect() finds Dockerfile in subdirectory."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            (repo_path / "package.json").write_text(
                json.dumps({"name": "app", "dependencies": {"express": "^4.0.0"}})
            )
            infra = repo_path / "infra"
            infra.mkdir()
            (infra / "Dockerfile").write_text(
                "FROM node:20\nEXPOSE 3000\nCMD [\"node\", \"server.js\"]\n"
            )

            detector = StackDetector(repo_path)
            stack = detector.detect()

            assert stack.has_dockerfile is True
            assert stack.dockerfile_path == "infra/Dockerfile"


class TestDockerfileDiscovery:
    """Tests for _find_dockerfile() and related methods."""

    def test_find_dockerfile_root(self):
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / "Dockerfile").write_text(
                "FROM node:20\nEXPOSE 3000\nCMD [\"node\", \"server.js\"]\n"
            )
            detector = StackDetector(repo_path)
            assert detector._find_dockerfile() == "Dockerfile"

    def test_find_dockerfile_from_compose_reference(self):
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            compose = (
                "services:\n"
                "  app:\n"
                "    build:\n"
                "      context: .\n"
                "      dockerfile: infra/Dockerfile\n"
                "  db:\n"
                "    image: postgres:15\n"
            )
            (repo_path / "docker-compose.yml").write_text(compose)
            infra = repo_path / "infra"
            infra.mkdir()
            (infra / "Dockerfile").write_text(
                "FROM openjdk:17\nEXPOSE 8080\nCMD [\"java\", \"-jar\", \"app.jar\"]\n"
            )
            detector = StackDetector(repo_path)
            assert detector._find_dockerfile() == "infra/Dockerfile"

    def test_find_dockerfile_compose_without_dockerfile_key(self):
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            compose = "services:\n  app:\n    build: .\n"
            (repo_path / "docker-compose.yml").write_text(compose)
            detector = StackDetector(repo_path)
            assert detector._find_dockerfile_from_compose() is None

    def test_find_dockerfile_glob_infra_directory(self):
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            infra = repo_path / "infra"
            infra.mkdir()
            (infra / "Dockerfile").write_text(
                "FROM openjdk:17\nEXPOSE 8080\nENTRYPOINT [\"java\", \"-jar\", \"app.jar\"]\n"
            )
            detector = StackDetector(repo_path)
            assert detector._find_dockerfile() == "infra/Dockerfile"

    def test_find_dockerfile_glob_docker_directory(self):
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            docker_dir = repo_path / "docker"
            docker_dir.mkdir()
            (docker_dir / "Dockerfile").write_text(
                "FROM python:3.11\nEXPOSE 8000\nCMD [\"python\", \"app.py\"]\n"
            )
            detector = StackDetector(repo_path)
            assert detector._find_dockerfile() == "docker/Dockerfile"

    def test_find_dockerfile_excludes_devcontainer(self):
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            devcontainer = repo_path / ".devcontainer"
            devcontainer.mkdir()
            (devcontainer / "Dockerfile").write_text(
                "FROM ubuntu:22.04\nRUN apt-get update\nEXPOSE 3000\nCMD [\"bash\"]\n"
            )
            detector = StackDetector(repo_path)
            assert detector._find_dockerfile() is None

    def test_find_dockerfile_excludes_test_directory(self):
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            test_dir = repo_path / "tests"
            test_dir.mkdir()
            (test_dir / "Dockerfile").write_text(
                "FROM python:3.11\nEXPOSE 8000\nCMD [\"pytest\"]\n"
            )
            detector = StackDetector(repo_path)
            assert detector._find_dockerfile() is None

    def test_find_dockerfile_root_priority_over_subdirectory(self):
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / "Dockerfile").write_text(
                "FROM node:20\nEXPOSE 3000\nCMD [\"node\", \"server.js\"]\n"
            )
            infra = repo_path / "infra"
            infra.mkdir()
            (infra / "Dockerfile").write_text(
                "FROM nginx:latest\nEXPOSE 80\nCMD [\"nginx\"]\n"
            )
            detector = StackDetector(repo_path)
            assert detector._find_dockerfile() == "Dockerfile"

    def test_find_dockerfile_no_dockerfile_anywhere(self):
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / "package.json").write_text("{}")
            detector = StackDetector(repo_path)
            assert detector._find_dockerfile() is None

    def test_is_service_dockerfile_with_expose_and_cmd(self):
        with TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "Dockerfile"
            p.write_text("FROM node:20\nEXPOSE 3000\nCMD [\"node\", \"app.js\"]\n")
            assert StackDetector._is_service_dockerfile(p) is True

    def test_is_service_dockerfile_with_entrypoint(self):
        with TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "Dockerfile"
            p.write_text("FROM openjdk:17\nEXPOSE 8080\nENTRYPOINT [\"java\", \"-jar\", \"app.jar\"]\n")
            assert StackDetector._is_service_dockerfile(p) is True

    def test_is_service_dockerfile_without_expose_or_cmd(self):
        with TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "Dockerfile"
            p.write_text("FROM ubuntu:22.04\nRUN apt-get update\n")
            assert StackDetector._is_service_dockerfile(p) is False

    def test_is_service_dockerfile_without_from(self):
        with TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "Dockerfile"
            p.write_text("EXPOSE 3000\nCMD [\"node\", \"app.js\"]\n")
            assert StackDetector._is_service_dockerfile(p) is False

    def test_dockerfile_priority_root(self):
        assert StackDetector._dockerfile_priority("Dockerfile") == 0

    def test_dockerfile_priority_infra(self):
        assert StackDetector._dockerfile_priority("infra/Dockerfile") == 1

    def test_dockerfile_priority_docker(self):
        assert StackDetector._dockerfile_priority("docker/Dockerfile") == 1

    def test_dockerfile_priority_unknown_dir(self):
        assert StackDetector._dockerfile_priority("src/Dockerfile") == 2
