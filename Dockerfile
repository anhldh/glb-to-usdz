# Stage 1: Install Node dependencies
FROM --platform=linux/amd64 node:22-slim AS node-deps
WORKDIR /scripts
COPY scripts/package.json scripts/package-lock.json ./
RUN npm install

# Stage 2: Main app
FROM --platform=linux/amd64 python:3.13-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libgl1-mesa-dev \
    libxi6 \
    libxrender1 \
    libxkbcommon-x11-0 \
    libsm6 \
    libxext6 \
    nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Copy node_modules từ stage 1
COPY --from=node-deps /scripts/node_modules /app/scripts/node_modules

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]