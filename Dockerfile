FROM python:3.14.1-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
RUN apt-get update && apt-get install -y curl libpq-dev
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY src/requirements.txt .
RUN uv pip install -r requirements.txt --system

COPY . . 

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000" ]