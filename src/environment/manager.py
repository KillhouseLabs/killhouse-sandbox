"""Environment lifecycle manager."""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import docker
import git
import structlog

from src.config import settings
from src.detection.detector import StackDetector, DetectedStack
from src.builder.generator import DockerfileGenerator
from src.environment.network import NetworkManager
from src.environment.services import ServiceManager
from src.api.schemas import EnvironmentResponse, EnvironmentStatus, DetectedStack as DetectedStackSchema

logger = structlog.get_logger()


@dataclass
class Environment:
    """Represents a running target environment."""

    env_id: str
    repo_url: str
    branch: str
    commit: Optional[str]
    stack: DetectedStack
    container_id: str
    network_id: str
    services: Dict[str, str] = field(default_factory=dict)
    status: str = "creating"
    target_url: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class EnvironmentManager:
    """Manages target environment lifecycle."""

    def __init__(self):
        self.docker = docker.from_env()
        self.network_manager = NetworkManager()
        self.service_manager = ServiceManager()
        self.environments: Dict[str, Environment] = {}
        self.repo_base = Path(settings.repo_clone_path)
        self.repo_base.mkdir(parents=True, exist_ok=True)

    async def create_environment(
        self,
        repo_url: str,
        branch: str = "main",
        commit: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
    ) -> EnvironmentResponse:
        """Create a new target environment."""
        env_id = str(uuid.uuid4())[:8]

        logger.info(
            "Creating environment",
            env_id=env_id,
            repo_url=repo_url,
            branch=branch,
        )

        try:
            # 1. Clone repository
            repo_path = await self._clone_repository(env_id, repo_url, branch, commit)

            # 2. Detect stack
            detector = StackDetector(repo_path)
            stack = detector.detect()

            # 3. Create isolated network
            network_id = self.network_manager.create_network(env_id)
            network_name = f"killhouse-{env_id}"

            # 4. Start required services
            services_info = {}
            required_services = self.service_manager.detect_required_services(
                stack.dependencies
            )

            for service_name in required_services:
                info = self.service_manager.start_service(
                    service_name, env_id, network_name
                )
                services_info[service_name] = info["host"]

            # 5. Generate Dockerfile if needed
            if not stack.has_dockerfile:
                generator = DockerfileGenerator(repo_path, stack)
                generator.write_dockerfile()

            # 6. Build target image
            image_tag = await self._build_image(env_id, repo_path, stack)

            # 7. Start target container
            container_id, target_url = await self._start_container(
                env_id,
                image_tag,
                network_name,
                stack,
                services_info,
                env_vars,
            )

            # 8. Store environment
            expires_at = datetime.utcnow() + timedelta(hours=settings.env_ttl_hours)
            env = Environment(
                env_id=env_id,
                repo_url=repo_url,
                branch=branch,
                commit=commit,
                stack=stack,
                container_id=container_id,
                network_id=network_id,
                services=services_info,
                status="running",
                target_url=target_url,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
            )
            self.environments[env_id] = env

            logger.info(
                "Environment created",
                env_id=env_id,
                target_url=target_url,
            )

            return EnvironmentResponse(
                env_id=env_id,
                target_url=target_url,
                stack=DetectedStackSchema(
                    language=stack.language,
                    framework=stack.framework,
                    runtime_version=stack.runtime_version,
                    package_manager=stack.package_manager,
                    has_dockerfile=stack.has_dockerfile,
                    has_docker_compose=stack.has_docker_compose,
                    services=stack.services,
                ),
                services=services_info,
                status="running",
                created_at=env.created_at,
                expires_at=expires_at,
            )

        except Exception as e:
            logger.exception("Failed to create environment", env_id=env_id, error=str(e))
            # Cleanup on failure
            await self._cleanup_partial(env_id)
            raise

    async def get_environment(self, env_id: str) -> Optional[EnvironmentStatus]:
        """Get environment status."""
        env = self.environments.get(env_id)
        if not env:
            return None

        # Check container status
        try:
            container = self.docker.containers.get(env.container_id)
            container_status = container.status
        except docker.errors.NotFound:
            container_status = "stopped"

        return EnvironmentStatus(
            env_id=env_id,
            status=container_status,
            target_url=env.target_url,
            services=env.services,
            error=env.error,
            created_at=env.created_at,
            expires_at=env.expires_at,
        )

    async def delete_environment(self, env_id: str) -> None:
        """Delete an environment and cleanup resources."""
        env = self.environments.get(env_id)
        if not env:
            raise ValueError(f"Environment not found: {env_id}")

        logger.info("Deleting environment", env_id=env_id)

        # Stop target container
        try:
            container = self.docker.containers.get(env.container_id)
            container.stop(timeout=10)
            container.remove()
        except docker.errors.NotFound:
            pass

        # Stop services
        self.service_manager.stop_all_services(env_id)

        # Remove network
        self.network_manager.delete_network(env_id)

        # Remove cloned repo
        repo_path = self.repo_base / env_id
        if repo_path.exists():
            import shutil
            shutil.rmtree(repo_path)

        # Remove from tracking
        del self.environments[env_id]

        logger.info("Environment deleted", env_id=env_id)

    async def list_environments(self) -> Dict[str, EnvironmentStatus]:
        """List all active environments."""
        result = {}
        for env_id in list(self.environments.keys()):
            status = await self.get_environment(env_id)
            if status:
                result[env_id] = status
        return result

    async def _clone_repository(
        self,
        env_id: str,
        repo_url: str,
        branch: str,
        commit: Optional[str],
    ) -> Path:
        """Clone repository to local path."""
        repo_path = self.repo_base / env_id
        repo_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Cloning repository",
            repo_url=repo_url,
            branch=branch,
            path=str(repo_path),
        )

        # Clone with depth=1 for speed
        repo = git.Repo.clone_from(
            repo_url,
            repo_path,
            branch=branch,
            depth=1,
        )

        # Checkout specific commit if provided
        if commit:
            repo.git.fetch("--depth", "1", "origin", commit)
            repo.git.checkout(commit)

        return repo_path

    async def _build_image(
        self,
        env_id: str,
        repo_path: Path,
        stack: DetectedStack,
    ) -> str:
        """Build Docker image for the target."""
        image_tag = f"killhouse-target:{env_id}"

        logger.info("Building image", tag=image_tag)

        # Use generated Dockerfile or existing one
        dockerfile = "Dockerfile.killhouse" if not stack.has_dockerfile else "Dockerfile"

        # Build image
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.docker.images.build(
                path=str(repo_path),
                dockerfile=dockerfile,
                tag=image_tag,
                rm=True,
            ),
        )

        logger.info("Image built", tag=image_tag)
        return image_tag

    async def _start_container(
        self,
        env_id: str,
        image_tag: str,
        network_name: str,
        stack: DetectedStack,
        services: Dict[str, str],
        env_vars: Optional[Dict[str, str]],
    ) -> tuple[str, str]:
        """Start target container and return container ID and target URL."""
        container_name = f"killhouse-target-{env_id}"
        port = stack.port

        # Build environment variables
        environment = env_vars or {}

        # Add service connection strings
        if "postgres" in services:
            environment["DATABASE_URL"] = (
                f"postgresql://killhouse:killhouse@{services['postgres']}:5432/app"
            )
        if "mysql" in services:
            environment["DATABASE_URL"] = (
                f"mysql://killhouse:killhouse@{services['mysql']}:3306/app"
            )
        if "redis" in services:
            environment["REDIS_URL"] = f"redis://{services['redis']}:6379"
        if "mongodb" in services:
            environment["MONGODB_URL"] = (
                f"mongodb://killhouse:killhouse@{services['mongodb']}:27017"
            )

        logger.info(
            "Starting container",
            name=container_name,
            image=image_tag,
            port=port,
        )

        container = self.docker.containers.run(
            image=image_tag,
            name=container_name,
            detach=True,
            network=network_name,
            environment=environment,
            ports={f"{port}/tcp": None},  # Random host port
            labels={
                "killhouse.env_id": env_id,
                "killhouse.target": "true",
                "killhouse.managed": "true",
            },
        )

        # Get assigned port
        container.reload()
        host_port = container.ports[f"{port}/tcp"][0]["HostPort"]
        target_url = f"http://{settings.host_ip}:{host_port}"

        logger.info(
            "Container started",
            container_id=container.id[:12],
            target_url=target_url,
        )

        return container.id, target_url

    async def _cleanup_partial(self, env_id: str) -> None:
        """Cleanup partial environment on creation failure."""
        try:
            self.service_manager.stop_all_services(env_id)
            self.network_manager.delete_network(env_id)

            repo_path = self.repo_base / env_id
            if repo_path.exists():
                import shutil
                shutil.rmtree(repo_path)
        except Exception as e:
            logger.warning("Cleanup failed", env_id=env_id, error=str(e))
