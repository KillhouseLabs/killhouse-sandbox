"""Tests for BuildConfig."""

import os

from src.builder.build_config import BuildConfig


class TestBuildConfig:
    """BuildConfig가 BuildKit 환경을 올바르게 설정하는지 검증."""

    def test_buildkit_enabled_by_default(self):
        config = BuildConfig()
        assert config.buildkit_enabled is True

    def test_get_build_env_includes_buildkit(self):
        config = BuildConfig()
        env = config.get_build_env()
        assert env["DOCKER_BUILDKIT"] == "1"

    def test_get_build_env_disabled(self):
        config = BuildConfig(buildkit_enabled=False)
        env = config.get_build_env()
        assert "DOCKER_BUILDKIT" not in env

    def test_apply_env_sets_os_environ(self):
        config = BuildConfig()
        config.apply_env()
        assert os.environ.get("DOCKER_BUILDKIT") == "1"

    def test_timeout_from_settings(self):
        config = BuildConfig()
        assert config.timeout_seconds == 300
