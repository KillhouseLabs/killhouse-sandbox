"""API routes for Killhouse Sandbox."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict
import structlog

from src.api.schemas import (
    CreateEnvironmentRequest,
    EnvironmentResponse,
    EnvironmentStatus,
    DeleteResponse,
)
from src.environment.manager import EnvironmentManager


router = APIRouter()
logger = structlog.get_logger()

# Global environment manager instance
env_manager = EnvironmentManager()


@router.post("/environments", response_model=EnvironmentResponse)
async def create_environment(
    request: CreateEnvironmentRequest,
    background_tasks: BackgroundTasks,
):
    """
    Create a new target environment.

    1. Clone the repository
    2. Detect technology stack
    3. Build container image
    4. Start environment with dependencies
    5. Return target URL
    """
    logger.info(
        "Creating environment",
        repo_url=request.repo_url,
        branch=request.branch,
    )

    try:
        result = await env_manager.create_environment(
            repo_url=request.repo_url,
            branch=request.branch,
            commit=request.commit,
            env_vars=request.env_vars,
        )

        return result

    except ValueError as e:
        logger.error("Invalid request", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.exception("Failed to create environment", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create environment: {e}")


@router.get("/environments/{env_id}", response_model=EnvironmentStatus)
async def get_environment(env_id: str):
    """Get environment status."""
    logger.info("Getting environment status", env_id=env_id)

    result = await env_manager.get_environment(env_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Environment not found")

    return result


@router.delete("/environments/{env_id}", response_model=DeleteResponse)
async def delete_environment(env_id: str):
    """Delete an environment and cleanup all resources."""
    logger.info("Deleting environment", env_id=env_id)

    try:
        await env_manager.delete_environment(env_id)
        return DeleteResponse(
            env_id=env_id,
            deleted=True,
            message="Environment deleted successfully",
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.exception("Failed to delete environment", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/environments", response_model=Dict[str, EnvironmentStatus])
async def list_environments():
    """List all active environments."""
    return await env_manager.list_environments()
