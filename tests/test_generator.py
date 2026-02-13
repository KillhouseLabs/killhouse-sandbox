"""Tests for Dockerfile generator."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.detection.detector import DetectedStack
from src.builder.generator import DockerfileGenerator


class TestDockerfileGenerator:
    """Test cases for DockerfileGenerator."""

    def test_generate_python_dockerfile(self):
        """Test Python Dockerfile generation."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            stack = DetectedStack(
                language="python",
                framework="fastapi",
                runtime_version="3.11",
                package_manager="pip",
                port=8000,
            )

            generator = DockerfileGenerator(repo_path, stack)
            dockerfile = generator.generate()

            assert "FROM python:3.11-slim" in dockerfile
            assert "EXPOSE 8000" in dockerfile
            assert "uvicorn" in dockerfile

    def test_generate_nodejs_dockerfile(self):
        """Test Node.js Dockerfile generation."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            stack = DetectedStack(
                language="javascript",
                framework="express",
                runtime_version="20",
                package_manager="npm",
                port=3000,
            )

            generator = DockerfileGenerator(repo_path, stack)
            dockerfile = generator.generate()

            assert "FROM node:20-alpine" in dockerfile
            assert "npm ci" in dockerfile
            assert "EXPOSE 3000" in dockerfile

    def test_generate_nextjs_dockerfile(self):
        """Test Next.js Dockerfile generation."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            stack = DetectedStack(
                language="javascript",
                framework="nextjs",
                runtime_version="20",
                package_manager="npm",
                port=3000,
            )

            generator = DockerfileGenerator(repo_path, stack)
            dockerfile = generator.generate()

            assert "FROM node:20-alpine AS deps" in dockerfile
            assert "npm run build" in dockerfile

    def test_generate_go_dockerfile(self):
        """Test Go Dockerfile generation."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            stack = DetectedStack(
                language="go",
                framework="gin",
                runtime_version="1.21",
                package_manager="go mod",
                port=8080,
            )

            generator = DockerfileGenerator(repo_path, stack)
            dockerfile = generator.generate()

            assert "FROM golang:1.21-alpine" in dockerfile
            assert "go build" in dockerfile
            assert "EXPOSE 8080" in dockerfile

    def test_write_dockerfile(self):
        """Test writing Dockerfile to disk."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            stack = DetectedStack(
                language="python",
                framework="flask",
                runtime_version="3.11",
                package_manager="pip",
                port=5000,
            )

            generator = DockerfileGenerator(repo_path, stack)
            output_path = generator.write_dockerfile()

            assert output_path.exists()
            assert output_path.name == "Dockerfile.killhouse"

            content = output_path.read_text()
            assert "FROM python:3.11-slim" in content

    def test_yarn_package_manager(self):
        """Test Yarn package manager in Dockerfile."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            stack = DetectedStack(
                language="javascript",
                framework="react",
                runtime_version="20",
                package_manager="yarn",
                port=3000,
            )

            generator = DockerfileGenerator(repo_path, stack)
            dockerfile = generator.generate()

            assert "yarn install --frozen-lockfile" in dockerfile
