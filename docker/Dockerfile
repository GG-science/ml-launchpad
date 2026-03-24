FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY src/ src/
COPY config/ config/
COPY outputs/ outputs/
COPY data/processed/ data/processed/

# Install dependencies
RUN uv pip install --system -r pyproject.toml

EXPOSE 8000

CMD ["uvicorn", "src.serving.api:app", "--host", "0.0.0.0", "--port", "8000"]
