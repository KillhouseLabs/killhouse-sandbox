"""Unit tests for EnvironmentManager."""

from unittest.mock import MagicMock, patch

import pytest

from src.environment.manager import EnvironmentManager


class TestStartContainer:
    """Tests for EnvironmentManager._start_container"""

    def setup_method(self):
        with patch("src.environment.manager.docker.from_env") as mock_docker:
            self.mock_docker = mock_docker.return_value
            self.manager = EnvironmentManager()

    @pytest.mark.asyncio
    async def test_target_url_uses_container_name_not_host_ip(self):
        """target_url should use container name, not host IP."""
        mock_container = MagicMock()
        mock_container.id = "abc123def456"
        self.mock_docker.containers.run.return_value = mock_container

        stack = MagicMock()
        stack.port = 8080

        _container_id, target_url = await self.manager._start_container(
            env_id="test1234",
            image_tag="killhouse-target:test1234",
            network_name="killhouse-test1234",
            stack=stack,
            services={},
            env_vars=None,
        )

        assert target_url == "http://killhouse-target-test1234:8080"
        assert "127.0.0.1" not in target_url

    @pytest.mark.asyncio
    async def test_container_starts_on_isolated_network(self):
        """Container should start directly on the isolated network."""
        mock_container = MagicMock()
        mock_container.id = "abc123def456"
        self.mock_docker.containers.run.return_value = mock_container

        stack = MagicMock()
        stack.port = 3000

        await self.manager._start_container(
            env_id="test1234",
            image_tag="killhouse-target:test1234",
            network_name="killhouse-test1234",
            stack=stack,
            services={},
            env_vars=None,
        )

        call_kwargs = self.mock_docker.containers.run.call_args[1]
        assert call_kwargs["network"] == "killhouse-test1234"

    @pytest.mark.asyncio
    async def test_no_host_port_binding(self):
        """Container should NOT have host port bindings."""
        mock_container = MagicMock()
        mock_container.id = "abc123def456"
        self.mock_docker.containers.run.return_value = mock_container

        stack = MagicMock()
        stack.port = 8080

        await self.manager._start_container(
            env_id="test1234",
            image_tag="killhouse-target:test1234",
            network_name="killhouse-test1234",
            stack=stack,
            services={},
            env_vars=None,
        )

        call_kwargs = self.mock_docker.containers.run.call_args[1]
        assert "ports" not in call_kwargs


class TestStartContainerEnvVars:
    """Tests for environment variable injection in _start_container."""

    def setup_method(self):
        with patch("src.environment.manager.docker.from_env") as mock_docker:
            self.mock_docker = mock_docker.return_value
            self.manager = EnvironmentManager()

    @pytest.mark.asyncio
    async def test_postgres_connection_string_injected(self):
        """DATABASE_URL should be set when postgres service exists."""
        mock_container = MagicMock()
        mock_container.id = "abc123def456"
        self.mock_docker.containers.run.return_value = mock_container

        stack = MagicMock()
        stack.port = 8080

        await self.manager._start_container(
            env_id="test1234",
            image_tag="killhouse-target:test1234",
            network_name="killhouse-test1234",
            stack=stack,
            services={"postgres": "172.18.0.2"},
            env_vars=None,
        )

        call_kwargs = self.mock_docker.containers.run.call_args[1]
        env = call_kwargs["environment"]
        assert "DATABASE_URL" in env
        assert "postgresql://" in env["DATABASE_URL"]
