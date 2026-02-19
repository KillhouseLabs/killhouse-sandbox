"""API schemas for Killhouse Sandbox."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class CreateEnvironmentRequest(BaseModel):
    """Request to create a new target environment."""

    repo_url: Optional[str] = Field(None, description="Git repository URL")
    branch: str = Field(default="main", description="Branch to checkout")
    commit: Optional[str] = Field(None, description="Specific commit hash")
    env_vars: Optional[Dict[str, str]] = Field(
        default=None, description="Additional environment variables"
    )
    dockerfile_content: Optional[str] = Field(None, description="Custom Dockerfile content")
    compose_content: Optional[str] = Field(
        None, description="docker-compose.yml content for service configuration"
    )
    plan_id: str = Field(default="free", description="Subscription plan ID for resource limits")


class DetectedStack(BaseModel):
    """Detected technology stack."""

    language: str = Field(..., description="Primary language (javascript, python, go)")
    framework: Optional[str] = Field(None, description="Framework (nextjs, fastapi, etc)")
    runtime_version: Optional[str] = Field(None, description="Runtime version")
    package_manager: str = Field(..., description="Package manager (npm, pip, etc)")
    has_dockerfile: bool = Field(default=False)
    has_docker_compose: bool = Field(default=False)
    services: List[str] = Field(default_factory=list, description="Detected services")


class ServiceInfo(BaseModel):
    """Information about a running service."""

    name: str
    container_id: str
    internal_ip: str
    port: int


class EnvironmentResponse(BaseModel):
    """Response for environment creation."""

    env_id: str = Field(..., description="Environment identifier")
    target_url: str = Field(..., description="URL to access the target application")
    network_name: str = Field(..., description="Docker network name for scanner connectivity")
    stack: DetectedStack = Field(..., description="Detected technology stack")
    services: Dict[str, str] = Field(..., description="Service name to IP mapping")
    status: str = Field(..., description="Environment status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(..., description="Auto-expiration time")


class EnvironmentStatus(BaseModel):
    """Environment status response."""

    env_id: str
    status: str  # creating, running, stopped, error
    target_url: Optional[str] = None
    services: Dict[str, str] = Field(default_factory=dict)
    logs: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    expires_at: datetime


class DeleteResponse(BaseModel):
    """Response for environment deletion."""

    env_id: str
    deleted: bool
    message: str
