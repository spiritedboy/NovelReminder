FROM python:3.12-slim

WORKDIR /app

COPY src ./src
COPY README.md .
COPY .env.example .

ENV PYTHONUNBUFFERED=1

CMD ["python3", "-m", "src.main", "run-loop"]
