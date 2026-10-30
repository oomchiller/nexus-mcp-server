FROM python:3.14-slim-bookworm AS build

WORKDIR /src
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip wheel --no-cache-dir --wheel-dir /out .

FROM python:3.14-slim-bookworm

RUN groupadd --system mcp \
    && useradd --system --gid mcp --home-dir /nonexistent --shell /usr/sbin/nologin mcp

COPY --from=build /out /tmp/wheels
RUN pip install --no-cache-dir --no-index --find-links=/tmp/wheels nexus-mcp-server \
    && rm -rf /tmp/wheels

ENV PYTHONUNBUFFERED=1 \
    NEXUS_MCP_MODE=readonly \
    NEXUS_MCP_ENABLE_WRITE_TOOLS=false

WORKDIR /app
USER mcp
ENTRYPOINT ["nexus-mcp-server"]
