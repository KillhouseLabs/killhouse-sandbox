"""Common service containers (databases, caches, etc.)."""

from dataclasses import dataclass
from typing import Dict, List, Optional
import docker
import structlog

logger = structlog.get_logger()


@dataclass
class ServiceConfig:
    """Configuration for a service container."""

    image: str
    port: int
    environment: Dict[str, str]
    healthcheck_cmd: Optional[str] = None
    volumes: Optional[Dict[str, str]] = None


# Common service configurations
SERVICES: Dict[str, ServiceConfig] = {
    "postgres": ServiceConfig(
        image="postgres:15-alpine",
        port=5432,
        environment={
            "POSTGRES_USER": "killhouse",
            "POSTGRES_PASSWORD": "killhouse",
            "POSTGRES_DB": "app",
        },
        healthcheck_cmd="pg_isready -U killhouse",
    ),
    "mysql": ServiceConfig(
        image="mysql:8",
        port=3306,
        environment={
            "MYSQL_ROOT_PASSWORD": "killhouse",
            "MYSQL_DATABASE": "app",
            "MYSQL_USER": "killhouse",
            "MYSQL_PASSWORD": "killhouse",
        },
        healthcheck_cmd="mysqladmin ping -h localhost",
    ),
    "redis": ServiceConfig(
        image="redis:7-alpine",
        port=6379,
        environment={},
        healthcheck_cmd="redis-cli ping",
    ),
    "mongodb": ServiceConfig(
        image="mongo:7",
        port=27017,
        environment={
            "MONGO_INITDB_ROOT_USERNAME": "killhouse",
            "MONGO_INITDB_ROOT_PASSWORD": "killhouse",
        },
    ),
    "rabbitmq": ServiceConfig(
        image="rabbitmq:3-management-alpine",
        port=5672,
        environment={
            "RABBITMQ_DEFAULT_USER": "killhouse",
            "RABBITMQ_DEFAULT_PASS": "killhouse",
        },
    ),
    "elasticsearch": ServiceConfig(
        image="elasticsearch:8.11.0",
        port=9200,
        environment={
            "discovery.type": "single-node",
            "xpack.security.enabled": "false",
        },
    ),
}


class ServiceManager:
    """Manages auxiliary service containers."""

    def __init__(self):
        self.client = docker.from_env()

    def start_service(
        self,
        service_name: str,
        env_id: str,
        network_name: str,
    ) -> Dict[str, str]:
        """Start a service container and return connection info."""
        if service_name not in SERVICES:
            raise ValueError(f"Unknown service: {service_name}")

        config = SERVICES[service_name]
        container_name = f"killhouse-{env_id}-{service_name}"

        logger.info(
            "Starting service",
            service=service_name,
            container=container_name,
        )

        # Check if already running
        try:
            existing = self.client.containers.get(container_name)
            if existing.status == "running":
                logger.info("Service already running", container=container_name)
                return self._get_connection_info(existing, config)
            else:
                existing.remove(force=True)
        except docker.errors.NotFound:
            pass

        # Start container
        container = self.client.containers.run(
            image=config.image,
            name=container_name,
            detach=True,
            environment=config.environment,
            network=network_name,
            labels={
                "killhouse.env_id": env_id,
                "killhouse.service": service_name,
                "killhouse.managed": "true",
            },
        )

        logger.info(
            "Service started",
            service=service_name,
            container_id=container.id[:12],
        )

        return self._get_connection_info(container, config)

    def stop_service(self, env_id: str, service_name: str) -> bool:
        """Stop a service container."""
        container_name = f"killhouse-{env_id}-{service_name}"

        try:
            container = self.client.containers.get(container_name)
            container.stop(timeout=10)
            container.remove()
            logger.info("Service stopped", container=container_name)
            return True
        except docker.errors.NotFound:
            return False

    def stop_all_services(self, env_id: str) -> int:
        """Stop all services for an environment."""
        stopped = 0
        containers = self.client.containers.list(
            filters={"label": f"killhouse.env_id={env_id}"}
        )

        for container in containers:
            if container.labels.get("killhouse.service"):
                container.stop(timeout=10)
                container.remove()
                stopped += 1

        logger.info("Stopped all services", env_id=env_id, count=stopped)
        return stopped

    def _get_connection_info(
        self,
        container: docker.models.containers.Container,
        config: ServiceConfig,
    ) -> Dict[str, str]:
        """Get connection info for a service container."""
        container.reload()

        # Get IP address from first network
        networks = container.attrs["NetworkSettings"]["Networks"]
        ip_address = next(iter(networks.values()))["IPAddress"]

        return {
            "host": ip_address,
            "port": str(config.port),
            "container_id": container.id[:12],
        }

    def detect_required_services(self, dependencies: Dict[str, str]) -> List[str]:
        """Detect required services from project dependencies."""
        services = []

        # Python packages
        if any(pkg in dependencies for pkg in ["psycopg2", "psycopg", "asyncpg"]):
            services.append("postgres")
        if any(pkg in dependencies for pkg in ["mysqlclient", "pymysql", "aiomysql"]):
            services.append("mysql")
        if any(pkg in dependencies for pkg in ["redis", "aioredis"]):
            services.append("redis")
        if any(pkg in dependencies for pkg in ["pymongo", "motor"]):
            services.append("mongodb")
        if any(pkg in dependencies for pkg in ["pika", "aio-pika", "celery"]):
            services.append("rabbitmq")
        if any(pkg in dependencies for pkg in ["elasticsearch"]):
            services.append("elasticsearch")

        # Node.js packages
        if any(pkg in dependencies for pkg in ["pg", "postgres", "sequelize", "prisma"]):
            if "postgres" not in services:
                services.append("postgres")
        if any(pkg in dependencies for pkg in ["mysql", "mysql2"]):
            if "mysql" not in services:
                services.append("mysql")
        if any(pkg in dependencies for pkg in ["redis", "ioredis"]):
            if "redis" not in services:
                services.append("redis")
        if any(pkg in dependencies for pkg in ["mongoose", "mongodb"]):
            if "mongodb" not in services:
                services.append("mongodb")
        if any(pkg in dependencies for pkg in ["amqplib"]):
            if "rabbitmq" not in services:
                services.append("rabbitmq")

        return services
