# 3D USDZ Converter API

### 1. Introduction

Built with **FastAPI** and powered by the **Blender Python API (`bpy`)**.

### 2. Features

- Converts 3D models from **.glb** format to **.usdz** (Apple's standard AR format).
- **Flexible operation (Optional MinIO/S3):**
  - Without `.env` file: The API receives a GLB file/link and returns the USDZ file directly for download.
  - With `.env` configured: The API automatically uploads the USDZ file to a bucket (MinIO/S3) and returns a public URL as JSON.

### 3. Environment

- **Python 3.13** is required. If you are using a different Python version (higher or lower), you will need to change the `bpy` package version accordingly to match your Python version.

### Run with Docker

**Step 1: Build Image**

```bash
docker build -t usdz-converter .
```

**Step 2: Run Container**

**Without .env**

```bash
docker run -d --name usdz_api -p 8000:8000 usdz-converter
```

**With .env**

```bash
docker run -d --name usdz_api -p 8000:8000 --env-file .env usdz-converter
```

### Run Locally

**Step 1: Create and activate virtual environment (venv)**

```bash
# Create virtual environment
python3 -m venv venv

# Activate on macOS/Linux
source venv/bin/activate

# (Or) Activate on Windows
venv\Scripts\activate
```

**Step 2: Install dependencies**

```bash
pip install -r requirements.txt
```

**Step 3: Run with auto-reload for development**

```bash
uvicorn main:app --reload --port 8000
```

App runs at http://localhost:8000/docs
