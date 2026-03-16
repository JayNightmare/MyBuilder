FROM python:3.12-slim

WORKDIR /app

# Install system deps for torch
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ src/
COPY models/ models/

EXPOSE 1298

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "1298"]
