FROM fedora:42

RUN dnf update -y
RUN dnf install git -y

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV UV_CACHE_DIR="/workspace/.cache/uv"
ENV PATH="/root/.local/bin:${PATH}"
COPY pyproject.toml /workspace/pyproject.toml
COPY .python-version /workspace/.python-version
COPY uv.lock /workspace/uv.lock

WORKDIR /workspace

RUN uv sync