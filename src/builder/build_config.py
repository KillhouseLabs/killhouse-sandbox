"""BuildKit build configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass

from src.config import settings


@dataclass
class BuildConfig:
    """Configuration for Docker image builds with BuildKit."""

    buildkit_enabled: bool = True
    timeout_seconds: int = settings.build_timeout_seconds

    def apply_env(self) -> None:
        """Set DOCKER_BUILDKIT=1 environment variable."""
        if self.buildkit_enabled:
            os.environ["DOCKER_BUILDKIT"] = "1"

    def get_build_env(self) -> dict[str, str]:
        """Return environment variables for the build process."""
        env = {}
        if self.buildkit_enabled:
            env["DOCKER_BUILDKIT"] = "1"
        return env
