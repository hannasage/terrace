# Terrace MCP server, for a small public host behind a custom connector.
#
# Deliberately lean: the server needs only mcp, duckdb and pyyaml at runtime, not
# the dbt and polars stack the pipeline uses. The published data is tiny (~32 KB)
# and bundled into the image, so the container is self-contained and serves the
# data as of the last deploy. Build context is the repository root:
#
#   docker build -f mcp_server/Dockerfile -t terrace-mcp .
#
# Runs over streamable-http and requires an API key on every request.
# TERRACE_API_KEY is supplied at run time as a secret, never baked in.

FROM python:3.12-slim

WORKDIR /app

# Pinned to the versions in uv.lock so the image matches local behaviour.
RUN pip install --no-cache-dir \
    "mcp==2.1.1" \
    "duckdb==1.5.5" \
    "pyyaml==6.0.3"

# The server code and the bundled verified data.
COPY mcp_server/ /app/mcp_server/
COPY pipeline/data/published/ /app/data/
COPY pipeline/registry/metrics.yml /app/metrics.yml

# Point the tools at the bundled copies, and serve HTTP on all interfaces.
ENV TERRACE_TRANSPORT=streamable-http \
    TERRACE_DATA_DIR=/app/data \
    TERRACE_METRICS=/app/metrics.yml \
    TERRACE_HTTP_HOST=0.0.0.0 \
    TERRACE_HTTP_PORT=8080

EXPOSE 8080

CMD ["python", "mcp_server/server.py"]
