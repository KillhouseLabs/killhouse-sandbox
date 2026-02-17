"""Stack detection orchestrator."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import structlog

logger = structlog.get_logger()

EXCLUDED_DIRS = frozenset(
    {
        ".devcontainer",
        "test",
        "tests",
        "example",
        "examples",
        ".github",
        "vendor",
        "node_modules",
        ".venv",
    }
)

PRIORITY_DIRS: dict[str, int] = {
    ".": 0,
    "docker": 1,
    "infra": 1,
    "build": 1,
    "deploy": 1,
}


@dataclass
class DetectedStack:
    """Detected technology stack from source code."""

    language: str
    framework: str | None = None
    runtime_version: str | None = None
    package_manager: str = "unknown"
    dependencies: dict[str, str] = field(default_factory=dict)
    has_dockerfile: bool = False
    has_docker_compose: bool = False
    dockerfile_path: str | None = None
    services: list[str] = field(default_factory=list)
    entry_point: str | None = None
    port: int = 8080


class StackDetector:
    """Detects technology stack from source code."""

    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)

    def detect(self) -> DetectedStack:
        """Analyze repository and detect technology stack."""
        logger.info("Detecting stack", repo_path=str(self.repo_path))

        # Check for existing Docker files (including subdirectories)
        dockerfile_path = self._find_dockerfile()
        has_dockerfile = dockerfile_path is not None
        has_docker_compose = (self.repo_path / "docker-compose.yml").exists() or (
            self.repo_path / "docker-compose.yaml"
        ).exists()

        # Detect by language
        if (self.repo_path / "package.json").exists():
            stack = self._detect_javascript()
        elif (
            (self.repo_path / "requirements.txt").exists()
            or (self.repo_path / "pyproject.toml").exists()
            or (self.repo_path / "setup.py").exists()
        ):
            stack = self._detect_python()
        elif (self.repo_path / "go.mod").exists():
            stack = self._detect_go()
        elif (self.repo_path / "pom.xml").exists():
            stack = self._detect_java_maven()
        elif (self.repo_path / "build.gradle").exists():
            stack = self._detect_java_gradle()
        elif (self.repo_path / "Gemfile").exists():
            stack = self._detect_ruby()
        else:
            raise ValueError(
                "Unable to detect technology stack. No recognized project files found."
            )

        stack.has_dockerfile = has_dockerfile
        stack.dockerfile_path = dockerfile_path
        stack.has_docker_compose = has_docker_compose

        if has_docker_compose:
            stack.services = self._parse_docker_compose_services()

        logger.info(
            "Stack detected",
            language=stack.language,
            framework=stack.framework,
            runtime_version=stack.runtime_version,
            dockerfile_path=dockerfile_path,
        )

        return stack

    def _detect_javascript(self) -> DetectedStack:
        """Detect JavaScript/TypeScript stack."""
        pkg_path = self.repo_path / "package.json"
        pkg = json.loads(pkg_path.read_text())

        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

        # Detect framework
        framework = None
        port = 3000
        entry_point = None

        if "next" in deps:
            framework = "nextjs"
            entry_point = "npm start"
        elif "nuxt" in deps:
            framework = "nuxt"
            entry_point = "npm start"
        elif "@angular/core" in deps:
            framework = "angular"
            port = 4200
        elif "vue" in deps:
            framework = "vue"
            entry_point = "npm run serve"
        elif "express" in deps:
            framework = "express"
            entry_point = "node index.js"
        elif "fastify" in deps:
            framework = "fastify"
            entry_point = "node index.js"
        elif "koa" in deps:
            framework = "koa"
            entry_point = "node index.js"
        elif "react" in deps:
            framework = "react"
            entry_point = "npm start"

        # Detect runtime version
        runtime_version = "20"  # Default to Node 20 LTS
        nvmrc = self.repo_path / ".nvmrc"
        if nvmrc.exists():
            runtime_version = nvmrc.read_text().strip().lstrip("v")

        node_version = self.repo_path / ".node-version"
        if node_version.exists():
            runtime_version = node_version.read_text().strip().lstrip("v")

        # Check engines in package.json
        engines = pkg.get("engines", {})
        if "node" in engines:
            # Parse version like ">=18" or "18.x"
            version_str = engines["node"]
            import re

            match = re.search(r"(\d+)", version_str)
            if match:
                runtime_version = match.group(1)

        # Detect package manager
        package_manager = "npm"
        if (self.repo_path / "yarn.lock").exists():
            package_manager = "yarn"
        elif (self.repo_path / "pnpm-lock.yaml").exists():
            package_manager = "pnpm"
        elif (self.repo_path / "bun.lockb").exists():
            package_manager = "bun"

        return DetectedStack(
            language="javascript",
            framework=framework,
            runtime_version=runtime_version,
            package_manager=package_manager,
            dependencies=deps,
            port=port,
            entry_point=entry_point,
        )

    def _detect_python(self) -> DetectedStack:
        """Detect Python stack."""
        deps = {}

        # Parse requirements.txt
        req_path = self.repo_path / "requirements.txt"
        if req_path.exists():
            for line in req_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-"):
                    # Parse package==version or package>=version
                    import re

                    match = re.match(r"^([a-zA-Z0-9_-]+)", line)
                    if match:
                        pkg_name = match.group(1).lower()
                        deps[pkg_name] = line

        # Parse pyproject.toml
        pyproject = self.repo_path / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib

                data = tomllib.loads(pyproject.read_text())
                project_deps = data.get("project", {}).get("dependencies", [])
                for dep in project_deps:
                    import re

                    match = re.match(r"^([a-zA-Z0-9_-]+)", dep)
                    if match:
                        deps[match.group(1).lower()] = dep
            except Exception:
                pass

        # Detect framework
        framework = None
        port = 8000
        entry_point = None

        if "django" in deps:
            framework = "django"
            entry_point = "python manage.py runserver 0.0.0.0:8000"
        elif "fastapi" in deps:
            framework = "fastapi"
            entry_point = "uvicorn main:app --host 0.0.0.0 --port 8000"
        elif "flask" in deps:
            framework = "flask"
            port = 5000
            entry_point = "flask run --host 0.0.0.0"
        elif "starlette" in deps:
            framework = "starlette"
            entry_point = "uvicorn main:app --host 0.0.0.0 --port 8000"

        # Detect runtime version
        runtime_version = "3.11"
        python_version = self.repo_path / ".python-version"
        if python_version.exists():
            runtime_version = python_version.read_text().strip()

        return DetectedStack(
            language="python",
            framework=framework,
            runtime_version=runtime_version,
            package_manager="pip",
            dependencies=deps,
            port=port,
            entry_point=entry_point,
        )

    def _detect_go(self) -> DetectedStack:
        """Detect Go stack."""
        go_mod = self.repo_path / "go.mod"
        content = go_mod.read_text()

        # Parse go version
        runtime_version = "1.21"
        for line in content.splitlines():
            if line.startswith("go "):
                runtime_version = line.split()[1]
                break

        # Detect framework
        framework = None
        deps = {}

        if "github.com/gin-gonic/gin" in content:
            framework = "gin"
        elif "github.com/labstack/echo" in content:
            framework = "echo"
        elif "github.com/gofiber/fiber" in content:
            framework = "fiber"

        return DetectedStack(
            language="go",
            framework=framework,
            runtime_version=runtime_version,
            package_manager="go mod",
            dependencies=deps,
            port=8080,
            entry_point="go run main.go",
        )

    def _detect_java_maven(self) -> DetectedStack:
        """Detect Java Maven stack."""
        return DetectedStack(
            language="java",
            framework="spring",
            runtime_version="17",
            package_manager="maven",
            port=8080,
            entry_point="mvn spring-boot:run",
        )

    def _detect_java_gradle(self) -> DetectedStack:
        """Detect Java Gradle stack."""
        return DetectedStack(
            language="java",
            framework="spring",
            runtime_version="17",
            package_manager="gradle",
            port=8080,
            entry_point="./gradlew bootRun",
        )

    def _detect_ruby(self) -> DetectedStack:
        """Detect Ruby stack."""
        gemfile = self.repo_path / "Gemfile"
        content = gemfile.read_text()

        framework = None
        port = 3000

        if "rails" in content.lower():
            framework = "rails"
        elif "sinatra" in content.lower():
            framework = "sinatra"
            port = 4567

        return DetectedStack(
            language="ruby",
            framework=framework,
            runtime_version="3.2",
            package_manager="bundler",
            port=port,
            entry_point="bundle exec rails server -b 0.0.0.0" if framework == "rails" else None,
        )

    def _find_dockerfile(self) -> str | None:
        """Find a service Dockerfile using structured 3-phase search."""
        # Phase 1: Check docker-compose.yml references
        result = self._find_dockerfile_from_compose()
        if result:
            return result

        # Phase 2 + 3: Glob search with filtering and content validation
        return self._find_dockerfile_by_glob()

    def _find_dockerfile_from_compose(self) -> str | None:
        """Extract Dockerfile path from docker-compose.yml build config."""
        compose_path = self.repo_path / "docker-compose.yml"
        if not compose_path.exists():
            compose_path = self.repo_path / "docker-compose.yaml"
        if not compose_path.exists():
            return None

        try:
            import yaml

            compose = yaml.safe_load(compose_path.read_text())
            for _name, config in (compose.get("services") or {}).items():
                if not isinstance(config, dict):
                    continue
                build_val = config.get("build")
                if not isinstance(build_val, dict):
                    continue
                dockerfile = build_val.get("dockerfile")
                if not dockerfile:
                    continue
                full_path = self.repo_path / dockerfile
                if full_path.exists() and self._is_service_dockerfile(full_path):
                    return dockerfile
        except Exception:
            pass
        return None

    def _find_dockerfile_by_glob(self) -> str | None:
        """Find Dockerfile by recursive glob with filtering and validation."""
        candidates: list[tuple[int, str]] = []

        for path in self.repo_path.rglob("Dockerfile"):
            relative = path.relative_to(self.repo_path)
            parts = relative.parts

            # Exclude files in blacklisted directories
            if any(part in EXCLUDED_DIRS for part in parts[:-1]):
                continue

            if not self._is_service_dockerfile(path):
                continue

            rel_str = str(relative)
            priority = self._dockerfile_priority(rel_str)
            candidates.append((priority, rel_str))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    @staticmethod
    def _is_service_dockerfile(path: Path) -> bool:
        """Verify a Dockerfile defines a runnable service (FROM + EXPOSE/CMD/ENTRYPOINT)."""
        try:
            content = path.read_text()
        except OSError:
            return False

        has_from = False
        has_runtime = False

        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            upper = stripped.upper()
            if upper.startswith("FROM "):
                has_from = True
            elif re.match(r"^(EXPOSE|CMD|ENTRYPOINT)\s", upper):
                has_runtime = True

        return has_from and has_runtime

    @staticmethod
    def _dockerfile_priority(relative_path: str) -> int:
        """Return priority score for a Dockerfile path (lower is better)."""
        if relative_path == "Dockerfile":
            return 0

        parts = Path(relative_path).parts
        parent_dir = parts[0] if len(parts) > 1 else "."
        return PRIORITY_DIRS.get(parent_dir, 2)

    def _parse_docker_compose_services(self) -> list[str]:
        """Parse services from docker-compose.yml."""
        compose_path = self.repo_path / "docker-compose.yml"
        if not compose_path.exists():
            compose_path = self.repo_path / "docker-compose.yaml"

        if not compose_path.exists():
            return []

        try:
            import yaml

            compose = yaml.safe_load(compose_path.read_text())
            return list(compose.get("services", {}).keys())
        except Exception:
            return []
