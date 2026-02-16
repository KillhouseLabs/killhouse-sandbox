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
            (repo_path / "Dockerfile").write_text("FROM node:20")

            detector = StackDetector(repo_path)
            stack = detector.detect()

            assert stack.has_dockerfile is True

    def test_detect_unknown_raises(self):
        """Test that unknown stack raises ValueError."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            detector = StackDetector(repo_path)

            with pytest.raises(ValueError, match="Unable to detect"):
                detector.detect()
