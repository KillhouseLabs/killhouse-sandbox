"""Shared test fixtures for Killhouse Sandbox."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


@pytest.fixture
def tmp_repo_path():
    """Provide a temporary directory as a mock repository path."""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
