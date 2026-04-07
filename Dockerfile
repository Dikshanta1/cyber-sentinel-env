FROM python:3.10-slim

WORKDIR /app

# Install uv to match OpenEnv standards
RUN pip install uv

# Copy EVERYTHING first so the installation can see your files
COPY . .

# Install dependencies and the project
RUN uv pip install --system -e .

# Expose the Hugging Face port
EXPOSE 7860

# Start the server directly
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]