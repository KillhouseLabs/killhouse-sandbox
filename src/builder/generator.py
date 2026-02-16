"""Dockerfile generator based on detected stack."""

from __future__ import annotations

from pathlib import Path

import structlog

from src.builder.templates import (
    GO_DOCKERFILE,
    JAVA_GRADLE_DOCKERFILE,
    JAVA_MAVEN_DOCKERFILE,
    NEXTJS_DOCKERFILE,
    NODEJS_DOCKERFILE,
    PYTHON_DOCKERFILE,
    PYTHON_POETRY_DOCKERFILE,
    RUBY_DOCKERFILE,
)
from src.detection.detector import DetectedStack

logger = structlog.get_logger()


class DockerfileGenerator:
    """Generates Dockerfiles based on detected technology stack."""

    def __init__(self, repo_path: Path, stack: DetectedStack):
        self.repo_path = Path(repo_path)
        self.stack = stack

    def generate(self) -> str:
        """Generate Dockerfile content based on stack."""
        logger.info(
            "Generating Dockerfile",
            language=self.stack.language,
            framework=self.stack.framework,
        )

        if self.stack.language == "python":
            return self._generate_python()
        elif self.stack.language == "javascript":
            return self._generate_javascript()
        elif self.stack.language == "go":
            return self._generate_go()
        elif self.stack.language == "java":
            return self._generate_java()
        elif self.stack.language == "ruby":
            return self._generate_ruby()
        else:
            raise ValueError(f"Unsupported language: {self.stack.language}")

    def write_dockerfile(self, output_path: Path | None = None) -> Path:
        """Write Dockerfile to disk."""
        dockerfile_content = self.generate()
        target_path = output_path or (self.repo_path / "Dockerfile.killhouse")
        target_path.write_text(dockerfile_content)
        logger.info("Dockerfile written", path=str(target_path))
        return target_path

    def _generate_python(self) -> str:
        """Generate Python Dockerfile."""
        version = self.stack.runtime_version or "3.11"
        port = self.stack.port

        # Determine command based on framework
        if self.stack.framework == "django":
            cmd = '["python", "manage.py", "runserver", "0.0.0.0:8000"]'
        elif self.stack.framework == "fastapi":
            cmd = '["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]'
        elif self.stack.framework == "flask":
            cmd = '["flask", "run", "--host", "0.0.0.0"]'
        else:
            cmd = '["python", "main.py"]'

        # Check for poetry
        if (self.repo_path / "pyproject.toml").exists() and (
            self.repo_path / "poetry.lock"
        ).exists():
            return PYTHON_POETRY_DOCKERFILE.format(
                version=version,
                port=port,
                cmd=cmd,
            )

        return PYTHON_DOCKERFILE.format(
            version=version,
            port=port,
            cmd=cmd,
        )

    def _generate_javascript(self) -> str:
        """Generate JavaScript/Node.js Dockerfile."""
        version = self.stack.runtime_version or "20"
        port = self.stack.port

        # Determine install command based on package manager
        if self.stack.package_manager == "yarn":
            install_cmd = "yarn install --frozen-lockfile"
        elif self.stack.package_manager == "pnpm":
            install_cmd = "npm install -g pnpm && pnpm install --frozen-lockfile"
        elif self.stack.package_manager == "bun":
            install_cmd = "npm install -g bun && bun install"
        else:
            install_cmd = "npm ci"

        # Use Next.js specific Dockerfile for Next.js projects
        if self.stack.framework == "nextjs":
            return NEXTJS_DOCKERFILE.format(
                version=version,
                port=port,
                install_cmd=install_cmd,
            )

        # Determine build and run commands
        build_cmd = ""
        if self.stack.framework in ["react", "vue", "angular", "nuxt"]:
            build_cmd = "RUN npm run build"

        if self.stack.framework in ["express", "fastify", "koa"]:
            cmd = '["node", "index.js"]'
        else:
            cmd = '["npm", "start"]'

        return NODEJS_DOCKERFILE.format(
            version=version,
            port=port,
            install_cmd=install_cmd,
            build_cmd=build_cmd,
            cmd=cmd,
        )

    def _generate_go(self) -> str:
        """Generate Go Dockerfile."""
        version = self.stack.runtime_version or "1.21"
        port = self.stack.port

        return GO_DOCKERFILE.format(
            version=version,
            port=port,
        )

    def _generate_java(self) -> str:
        """Generate Java Dockerfile."""
        version = self.stack.runtime_version or "17"
        port = self.stack.port

        if self.stack.package_manager == "maven":
            return JAVA_MAVEN_DOCKERFILE.format(
                version=version,
                maven_version="3.9",
                port=port,
            )
        else:
            return JAVA_GRADLE_DOCKERFILE.format(
                version=version,
                gradle_version="8.5",
                port=port,
            )

    def _generate_ruby(self) -> str:
        """Generate Ruby Dockerfile."""
        version = self.stack.runtime_version or "3.2"
        port = self.stack.port

        if self.stack.framework == "rails":
            cmd = '["bundle", "exec", "rails", "server", "-b", "0.0.0.0"]'
        else:
            cmd = '["bundle", "exec", "ruby", "app.rb"]'

        return RUBY_DOCKERFILE.format(
            version=version,
            port=port,
            cmd=cmd,
        )
