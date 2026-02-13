# Killhouse Sandbox

Target environment builder for KILLHOUSE security platform. Detects tech stack from source code and spins up isolated containers for dynamic testing.

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Killhouse Sandbox                         │
│                                                              │
│   Source Code ──▶ Stack Detection ──▶ Container Build       │
│                         │                   │                │
│                         ▼                   ▼                │
│                  ┌─────────────────────────────────┐        │
│                  │     Isolated Network             │        │
│                  │  ┌─────────┐  ┌─────────┐       │        │
│                  │  │   App   │  │   DB    │       │        │
│                  │  │  :3000  │  │  :5432  │       │        │
│                  │  └─────────┘  └─────────┘       │        │
│                  │       172.28.x.x (internal)     │        │
│                  └─────────────────────────────────┘        │
│                                   │                          │
│                                   ▼                          │
│                          Target URL returned                 │
│                     (for Exploit Agent to attack)            │
└─────────────────────────────────────────────────────────────┘
```

## Features

- **Auto Stack Detection**: Analyzes `package.json`, `requirements.txt`, `go.mod`, etc.
- **Dynamic Dockerfile Generation**: Creates Dockerfile if not present
- **Dependency Services**: Auto-provisions PostgreSQL, Redis, etc. based on dependencies
- **Network Isolation**: Containers run in internal-only Docker network
- **Resource Limits**: Memory, CPU, PID limits enforced
- **Auto Cleanup**: Environments expire after configurable TTL

## Supported Stacks

| Language | Frameworks | Detection |
|----------|------------|-----------|
| JavaScript/TypeScript | Next.js, React, Vue, Express, Fastify | `package.json` |
| Python | FastAPI, Django, Flask | `requirements.txt`, `pyproject.toml` |
| Go | Gin, Echo, Fiber | `go.mod` |
| Java | Spring Boot | `pom.xml`, `build.gradle` |
| Ruby | Rails, Sinatra | `Gemfile` |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn src.main:app --host 0.0.0.0 --port 8081

# Create environment
curl -X POST http://localhost:8081/api/environments \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/repo", "branch": "main"}'
```

## API

### Create Environment

```http
POST /api/environments
Content-Type: application/json

{
  "repo_url": "https://github.com/user/repo",
  "branch": "main",
  "commit": "abc123"  // optional
}
```

Response:
```json
{
  "env_id": "env-abc123",
  "target_url": "http://172.28.0.10:3000",
  "stack": {
    "language": "javascript",
    "framework": "nextjs",
    "runtime_version": "20"
  },
  "services": {
    "web": "172.28.0.10",
    "db": "172.28.0.11"
  },
  "expires_at": "2025-01-15T12:00:00Z"
}
```

### Get Environment Status

```http
GET /api/environments/{env_id}
```

### Delete Environment

```http
DELETE /api/environments/{env_id}
```

## Configuration

```bash
# .env
DOCKER_HOST=unix:///var/run/docker.sock
ENVIRONMENT_TTL_MINUTES=30
MAX_CONCURRENT_ENVIRONMENTS=5
ISOLATED_NETWORK_SUBNET=172.28.0.0/16
```

## Directory Structure

```
.
├── src/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration
│   ├── api/
│   │   ├── routes.py           # API endpoints
│   │   └── schemas.py          # Pydantic models
│   ├── detection/
│   │   ├── detector.py         # Stack detection orchestrator
│   │   ├── javascript.py       # JS/TS detection
│   │   ├── python.py           # Python detection
│   │   └── golang.py           # Go detection
│   ├── builder/
│   │   ├── dockerfile.py       # Dockerfile generation
│   │   ├── templates/          # Dockerfile templates
│   │   └── builder.py          # Image builder
│   └── environment/
│       ├── manager.py          # Environment lifecycle
│       ├── network.py          # Network management
│       └── services.py         # Dependency services (DB, Redis)
├── tests/
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## License

Private - All rights reserved
