FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ARG UID=1000
ARG GID=1000
ARG USERNAME=dev

RUN groupadd --gid ${GID} ${USERNAME} \
    && useradd --uid ${UID} --gid ${GID} --create-home --shell /bin/bash ${USERNAME} \
    && mkdir -p /home/${USERNAME}/.cache/uv \
    && chown -R ${UID}:${GID} /home/${USERNAME}

WORKDIR /workspace

ENV HOME=/home/${USERNAME}
ENV UV_CACHE_DIR=/home/${USERNAME}/.cache/uv

USER ${USERNAME}
