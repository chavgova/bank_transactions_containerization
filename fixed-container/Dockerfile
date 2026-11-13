FROM python:3.10-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml pyproject.toml
COPY uv.lock uv.lock
COPY main.py main.py
COPY model.pkl model.pkl
COPY data.json data.json

ENTRYPOINT ["uv", "run", "python", "main.py"]