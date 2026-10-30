FROM ghcr.io/astral-sh/uv:0.13.5 AS uv

FROM python:3.14-slim-bookworm AS build

COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /src
COPY pyproject.toml uv.lock README.md LICENSE ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
RUN uv sync --locked --no-dev --no-editable

FROM python:3.14-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/oomchiller/nexus-mcp-server" \
      org.opencontainers.image.description="MCP server for Sonatype Nexus Repository Manager" \
      org.opencontainers.image.licenses="MIT"

RUN groupadd --system mcp \
    && useradd --system --gid mcp --home-dir /nonexistent --shell /usr/sbin/nologin mcp

COPY --from=build /opt/venv /opt/venv

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    NEXUS_MCP_MODE=readonly \
    NEXUS_MCP_ENABLE_WRITE_TOOLS=false

WORKDIR /app
USER mcp
ENTRYPOINT ["nexus-mcp-server"]
