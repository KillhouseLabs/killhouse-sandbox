"""Tests for ComposeParser."""

import pytest
import yaml

from src.builder.compose_parser import ComposeParser


class TestComposeParser:
    """ComposeParser가 docker-compose.yml 내용을 올바르게 파싱하는지 검증."""

    def test_parse_target_and_dependencies(self):
        compose = """
services:
  app:
    build: .
    ports:
      - "8080:8080"
    depends_on:
      - db
  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: test
"""
        result = ComposeParser(compose).parse()
        assert result.target_service is not None
        assert result.target_service.name == "app"
        assert result.target_service.build == "."
        assert len(result.dependencies) == 1
        assert result.dependencies[0].name == "db"
        assert result.dependencies[0].image == "postgres:15"

    def test_parse_multiple_dependencies(self):
        compose = """
services:
  app:
    build: .
  db:
    image: postgres:15
  redis:
    image: redis:7
"""
        result = ComposeParser(compose).parse()
        dep_names = [d.name for d in result.dependencies]
        assert "db" in dep_names
        assert "redis" in dep_names

    def test_parse_environment_as_dict(self):
        compose = """
services:
  app:
    build: .
    environment:
      DATABASE_URL: postgres://db:5432/app
      DEBUG: "true"
"""
        result = ComposeParser(compose).parse()
        assert result.target_service.environment["DATABASE_URL"] == "postgres://db:5432/app"

    def test_parse_environment_as_list(self):
        compose = """
services:
  app:
    build: .
    environment:
      - DATABASE_URL=postgres://db:5432/app
      - DEBUG=true
"""
        result = ComposeParser(compose).parse()
        assert result.target_service.environment["DATABASE_URL"] == "postgres://db:5432/app"

    def test_invalid_yaml_raises(self):
        with pytest.raises((ValueError, yaml.YAMLError)):
            ComposeParser("{{invalid yaml").parse()

    def test_missing_services_key_raises(self):
        with pytest.raises(ValueError, match="services"):
            ComposeParser("version: '3'").parse()

    def test_no_target_service(self):
        compose = """
services:
  db:
    image: postgres:15
  redis:
    image: redis:7
"""
        result = ComposeParser(compose).parse()
        assert result.target_service is None
        assert len(result.dependencies) == 2
