"""Docker Compose content parser."""

from __future__ import annotations

from dataclasses import dataclass, field

import yaml


@dataclass
class ComposeService:
    """Parsed service from docker-compose.yml."""

    name: str
    image: str | None = None
    build: str | None = None
    dockerfile: str | None = None
    ports: list[str] = field(default_factory=list)
    environment: dict[str, str] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)


@dataclass
class ParsedCompose:
    """Result of parsing docker-compose.yml content."""

    target_service: ComposeService | None = None
    dependencies: list[ComposeService] = field(default_factory=list)


class ComposeParser:
    """Parses docker-compose.yml content to extract service configuration."""

    def __init__(self, content: str):
        self.content = content

    def parse(self) -> ParsedCompose:
        """Parse compose content and separate target vs dependency services."""
        data = yaml.safe_load(self.content)
        if not data or "services" not in data:
            raise ValueError("Invalid compose content: 'services' key required")

        services_data = data["services"]
        result = ParsedCompose()

        for name, config in services_data.items():
            service = self._parse_service(name, config or {})

            # Service with 'build' is the target app; others are dependencies
            if service.build is not None:
                result.target_service = service
            else:
                result.dependencies.append(service)

        return result

    def _parse_service(self, name: str, config: dict) -> ComposeService:
        build_val = config.get("build")
        build_str = (
            build_val
            if isinstance(build_val, str)
            else (build_val.get("context", ".") if isinstance(build_val, dict) else None)
        )

        dockerfile = None
        if isinstance(build_val, dict):
            dockerfile = build_val.get("dockerfile")

        env = config.get("environment", {})
        if isinstance(env, list):
            env = dict(item.split("=", 1) for item in env if "=" in item)

        depends = config.get("depends_on", [])
        if isinstance(depends, dict):
            depends = list(depends.keys())

        return ComposeService(
            name=name,
            image=config.get("image"),
            build=build_str,
            dockerfile=dockerfile,
            ports=[str(p) for p in config.get("ports", [])],
            environment=env,
            depends_on=depends,
        )
