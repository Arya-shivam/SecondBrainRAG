FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project definition
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen

# Copy source code and scripts
COPY src/ ./src/
COPY scripts/ ./scripts/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
