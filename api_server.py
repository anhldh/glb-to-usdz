#!/usr/bin/env python3
"""
HTTP API wrapper for converting GLB files to USDZ via Blender.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from starlette.background import BackgroundTask


BASE_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = BASE_DIR / "glb_to_usdz.py"
STORAGE_ROOT = Path(os.getenv("CONVERT_API_STORAGE", BASE_DIR / "storage")).resolve()
DOWNLOAD_DIR = STORAGE_ROOT / "downloads"
WORK_DIR = STORAGE_ROOT / "work"
BLENDER_TIMEOUT_SECONDS = int(os.getenv("BLENDER_TIMEOUT_SECONDS", "600"))

app = FastAPI(
    title="GLB to USDZ Converter API",
    version="1.0.0",
    description="Upload a GLB file, convert it with Blender, then download the USDZ output.",
)


def ensure_directories() -> None:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)


def find_blender() -> str:
    explicit_path = os.getenv("BLENDER_PATH")
    if explicit_path:
        blender_path = Path(explicit_path)
        if blender_path.exists():
            return str(blender_path)
        raise RuntimeError(f"BLENDER_PATH does not exist: {explicit_path}")

    candidates = [
        Path(r"C:\Program Files\Blender Foundation\Blender\blender.exe"),
        Path(r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe"),
        Path(r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe"),
        Path(r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"),
        Path("/Applications/Blender.app/Contents/MacOS/Blender"),
        Path("/Applications/Blender/Blender.app/Contents/MacOS/Blender"),
    ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    blender_on_path = shutil.which("blender")
    if blender_on_path:
        return blender_on_path

    raise RuntimeError(
        "Blender executable was not found. Set BLENDER_PATH or install Blender in a standard location."
    )


def save_upload(uploaded_file: UploadFile, destination: Path) -> Path:
    suffix = Path(uploaded_file.filename or "model.glb").suffix or ".glb"
    if suffix.lower() != ".glb":
        raise HTTPException(status_code=400, detail="Only .glb files are supported.")

    file_name = Path(uploaded_file.filename or f"upload{suffix}").name
    output_path = destination / file_name

    with output_path.open("wb") as file_handle:
        shutil.copyfileobj(uploaded_file.file, file_handle)

    return output_path


def run_blender_convert(input_dir: Path, output_dir: Path) -> None:
    blender_path = find_blender()
    command = [
        blender_path,
        "--background",
        "--python",
        str(SCRIPT_PATH),
        "--",
        str(input_dir),
        str(output_dir),
    ]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=BLENDER_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail="Conversion timed out.") from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to start Blender: {exc}") from exc

    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        stdout = (completed.stdout or "").strip()
        message = stderr or stdout or "Blender conversion failed."
        raise HTTPException(status_code=500, detail=message)


def build_download_name(source_name: str) -> str:
    safe_stem = Path(source_name).stem or "converted"
    safe_stem = "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in safe_stem)
    return f"{safe_stem}_{uuid.uuid4().hex}.usdz"


def convert_single_file(uploaded_file: UploadFile) -> str:
    ensure_directories()

    job_id = uuid.uuid4().hex
    job_dir = WORK_DIR / job_id
    input_dir = job_dir / "input"
    output_dir = job_dir / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        source_path = save_upload(uploaded_file, input_dir)
        run_blender_convert(input_dir, output_dir)

        generated_files = list(output_dir.glob("*.usdz"))
        if not generated_files:
            raise HTTPException(status_code=500, detail="No USDZ file was produced.")

        generated_file = generated_files[0]
        download_name = build_download_name(source_path.name)
        final_path = DOWNLOAD_DIR / download_name
        shutil.move(str(generated_file), str(final_path))
        return download_name
    finally:
        shutil.rmtree(job_dir, ignore_errors=True)


@app.on_event("startup")
def startup_event() -> None:
    ensure_directories()


@app.get("/health")
def healthcheck() -> dict:
    return {"status": "ok"}


@app.post("/convert")
async def convert_to_usdz(uploaded_file: UploadFile = File(...)) -> JSONResponse:
    if not uploaded_file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    output_path = convert_single_file(uploaded_file)
    payload = {
        "OutputPath": output_path,
        "FileName": Path(output_path).name,
        "DownloadUrl": f"/download/{output_path}",
    }
    return JSONResponse(content=payload)


@app.get("/download/{output_path}")
def download_usdz(output_path: str) -> FileResponse:
    file_name = Path(output_path).name
    file_path = DOWNLOAD_DIR / file_name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Converted file not found.")

    return FileResponse(
        path=file_path,
        media_type="model/vnd.usdz+zip",
        filename=file_name,
        background=BackgroundTask(lambda: file_path.unlink(missing_ok=True)),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api_server:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=False,
    )
