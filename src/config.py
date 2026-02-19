"""Configuration management for Killhouse Sandbox."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Server
    host: str = "0.0.0.0"
    port: int = 8081
    debug: bool = False

    # Docker
    docker_host: str = "unix:///var/run/docker.sock"

    # Environment settings
    environment_ttl_minutes: int = 30
    max_concurrent_environments: int = 5

    # Network
    isolated_network_prefix: str = "killhouse-target"
    isolated_network_subnet: str = "172.28.0.0/16"

    # Resource limits
    container_memory_limit: str = "1g"
    container_cpu_limit: float = 1.0
    container_pids_limit: int = 100

    # Paths
    work_dir: Path = Path("/tmp/killhouse-sandbox")
    repo_clone_path: Path = Path("/tmp/killhouse-sandbox/repos")

    # Host
    host_ip: str = "127.0.0.1"

    # TTL
    env_ttl_hours: int = 1

    # Timeouts
    build_timeout_seconds: int = 300
    startup_timeout_seconds: int = 60

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""

    class Config:
        env_file = ".env"
        env_prefix = "SANDBOX_"


settings = Settings()
