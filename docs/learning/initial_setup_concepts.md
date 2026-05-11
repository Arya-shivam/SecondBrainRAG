# Initial Setup Concepts: The RAG Infrastructure

This document explains the foundational infrastructure and architectural decisions that power your Second Brain. The initial setup phase focused on creating a robust, containerized environment that can scale from a simple API to a full Retrieval-Augmented Generation (RAG) system.

## 1. Container Orchestration (Docker Compose)
Modern data engineering systems rely on multiple specialized services. Instead of installing each service directly on your computer, we use Docker to run them in isolated environments (containers) that communicate over a virtual network.

### `docker-compose.yaml`
This file is the blueprint for your entire infrastructure. It defines the following services:
- **FastAPI Backend (`fastapi-app`)**: Your custom Python code. It exposes ports to the host machine so you can interact with the API (`localhost:8000`).
- **PostgreSQL (`postgres`)**: The relational database for metadata.
- **OpenSearch (`opensearch`)**: The vector database and search engine.
- **Airflow Ecosystem**: Airflow requires multiple components to run efficiently:
  - `airflow-scheduler`: Decides when tasks should run.
  - `airflow-apiserver` & `airflow-dag-processor`: Manages the UI and parses Python DAG files.
  - `airflow-triggerer`: Handles asynchronous tasks (like waiting for external APIs).
- **Langfuse**: An observability platform specifically built for LLM applications. It helps track prompt performance, generation latency, and user feedback.

### Volumes and Persistence
In Docker, when a container is destroyed, its data is lost. To prevent this, we use **Volumes**.
- In your setup, we map `./data:/app/data` for the FastAPI app. This means any file your code saves to `/app/data` inside the container is permanently written to the `data/` folder on your actual Windows machine. This is how your Obsidian Markdown files are persisted safely.

## 2. Dependency Management (`uv`)
Python dependency management can be notoriously slow and fragile. We opted for **`uv`**, an extremely fast package manager written in Rust.

### `pyproject.toml` & `uv.lock`
- **`pyproject.toml`**: Replaces the old `requirements.txt`. It defines your project metadata and high-level dependencies (like `fastapi`, `pydantic`, `pymupdf`).
- **`uv.lock`**: An auto-generated file that locks every dependency (and sub-dependency) to an exact version and cryptographic hash. This guarantees that your project will build identically on any machine, preventing "it works on my machine" bugs.
- **In Docker**: Our Dockerfile runs `uv sync --frozen`, which tells `uv` to strictly install exactly what is in the lockfile without trying to resolve new versions.

## 3. The FastAPI Application Structure
FastAPI is a modern, high-performance web framework for Python.

### `src/config.py` & `.env`
- We use `pydantic-settings` to manage environment variables. This library reads your `.env` file and strictly validates the variables against Python types. For example, `postgres_url: str` ensures the connection string is a valid string. If a required variable is missing, the app refuses to start, failing fast rather than crashing later in execution.

### `src/main.py`
- This is the entry point of your application.
- **CORS (Cross-Origin Resource Sharing)**: We configured CORS middleware to allow requests from external origins. This is what permits your Chrome Extension to send data to your local backend securely.

## 4. Why This Architecture?
By putting everything in Docker and using `uv` for dependencies, the project is completely portable. If you buy a new computer tomorrow, you only need to run `docker compose up -d` and your entire Second Brain infrastructure will boot perfectly in minutes.
