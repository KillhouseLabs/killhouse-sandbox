"""Docker network management for isolated environments."""

from typing import Optional
import docker
import structlog

logger = structlog.get_logger()


class NetworkManager:
    """Manages isolated Docker networks for target environments."""

    def __init__(self):
        self.client = docker.from_env()

    def create_network(self, env_id: str, internal: bool = True) -> str:
        """Create an isolated network for the environment."""
        network_name = f"killhouse-{env_id}"

        logger.info("Creating network", name=network_name, internal=internal)

        network = self.client.networks.create(
            name=network_name,
            driver="bridge",
            internal=internal,
            labels={
                "killhouse.env_id": env_id,
                "killhouse.managed": "true",
            },
        )

        logger.info("Network created", name=network_name, id=network.id)
        return network.id

    def delete_network(self, env_id: str) -> bool:
        """Delete the environment's network."""
        network_name = f"killhouse-{env_id}"

        try:
            network = self.client.networks.get(network_name)
            network.remove()
            logger.info("Network deleted", name=network_name)
            return True
        except docker.errors.NotFound:
            logger.warning("Network not found", name=network_name)
            return False
        except docker.errors.APIError as e:
            logger.error("Failed to delete network", name=network_name, error=str(e))
            raise

    def get_network(self, env_id: str) -> Optional[docker.models.networks.Network]:
        """Get the network for an environment."""
        network_name = f"killhouse-{env_id}"

        try:
            return self.client.networks.get(network_name)
        except docker.errors.NotFound:
            return None

    def connect_container(self, env_id: str, container_id: str) -> None:
        """Connect a container to the environment network."""
        network = self.get_network(env_id)
        if network:
            network.connect(container_id)
            logger.info(
                "Container connected to network",
                container_id=container_id,
                network=f"killhouse-{env_id}",
            )

    def disconnect_container(self, env_id: str, container_id: str) -> None:
        """Disconnect a container from the environment network."""
        network = self.get_network(env_id)
        if network:
            network.disconnect(container_id)
            logger.info(
                "Container disconnected from network",
                container_id=container_id,
                network=f"killhouse-{env_id}",
            )

    def cleanup_orphaned_networks(self) -> int:
        """Remove networks without running containers."""
        removed = 0
        networks = self.client.networks.list(
            filters={"label": "killhouse.managed=true"}
        )

        for network in networks:
            if not network.containers:
                try:
                    network.remove()
                    removed += 1
                    logger.info("Removed orphaned network", name=network.name)
                except docker.errors.APIError:
                    pass

        return removed
