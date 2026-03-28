# Dockerfile
#
# This packages your entire project into a container.
# Judges run: docker build + docker run to verify it works.
# Hugging Face Spaces also uses this to run your environment.
#
# KEY RULE: HF Spaces requires port 7860. Never change this.

# Start from official Python image (slim = smaller size)
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements first (Docker caches this layer — speeds up rebuilds)
COPY requirements.txt .

# Install all Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy your entire project into the container
COPY . .

# Tell Docker this container listens on port 7860
EXPOSE 7860

# Command to start the server when container runs
CMD ["python", "server/app.py"]