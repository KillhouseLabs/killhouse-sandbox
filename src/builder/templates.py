"""Dockerfile templates for various technology stacks."""

PYTHON_DOCKERFILE = """FROM python:{version}-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE {port}

# Run application
CMD {cmd}
"""

PYTHON_POETRY_DOCKERFILE = """FROM python:{version}-slim

WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.create false && \\
    poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . .

EXPOSE {port}

CMD {cmd}
"""

NODEJS_DOCKERFILE = """FROM node:{version}-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN {install_cmd}

# Copy application code
COPY . .

# Build if needed
{build_cmd}

EXPOSE {port}

CMD {cmd}
"""

NEXTJS_DOCKERFILE = """FROM node:{version}-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN {install_cmd}

FROM node:{version}-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:{version}-alpine AS runner
WORKDIR /app
ENV NODE_ENV production

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE {port}
CMD ["node", "server.js"]
"""

GO_DOCKERFILE = """FROM golang:{version}-alpine AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build binary
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/main .

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/main .

EXPOSE {port}
CMD ["./main"]
"""

JAVA_MAVEN_DOCKERFILE = """FROM maven:{maven_version}-openjdk-{version} AS builder

WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline

COPY src ./src
RUN mvn package -DskipTests

FROM openjdk:{version}-slim
WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar

EXPOSE {port}
CMD ["java", "-jar", "app.jar"]
"""

JAVA_GRADLE_DOCKERFILE = """FROM gradle:{gradle_version}-jdk{version} AS builder

WORKDIR /app
COPY build.gradle settings.gradle ./
COPY gradle ./gradle
RUN gradle dependencies --no-daemon

COPY src ./src
RUN gradle bootJar --no-daemon

FROM openjdk:{version}-slim
WORKDIR /app
COPY --from=builder /app/build/libs/*.jar app.jar

EXPOSE {port}
CMD ["java", "-jar", "app.jar"]
"""

RUBY_DOCKERFILE = """FROM ruby:{version}-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Copy Gemfile
COPY Gemfile Gemfile.lock ./
RUN bundle install --without development test

# Copy application code
COPY . .

EXPOSE {port}
CMD {cmd}
"""

DOCKER_COMPOSE_TEMPLATE = """version: '3.8'

services:
{services}

networks:
  killhouse-{env_id}:
    driver: bridge
    internal: true
"""

SERVICE_TEMPLATE = """  {name}:
    image: {image}
    container_name: killhouse-{env_id}-{name}
    networks:
      - killhouse-{env_id}
    {ports}
    {environment}
    {depends_on}
"""
