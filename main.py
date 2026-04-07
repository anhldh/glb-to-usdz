import bpy
import os
import sys
import io
import uuid
import asyncio
import urllib.request
import boto3
from botocore.client import Config
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import subprocess

# Import 
from config import settings

# Cấu hình MinIO client
protocol = "https" if settings.MINIO_USE_SSL else "http"
full_endpoint_url = f"{protocol}://{settings.MINIO_ENDPOINT}:{settings.MINIO_PORT}"

s3_client = boto3.client(
    's3',
    endpoint_url=full_endpoint_url,
    aws_access_key_id=settings.MINIO_ACCESS_KEY,
    aws_secret_access_key=settings.MINIO_SECRET_KEY,
    config=Config(signature_version='s3v4')
)

app = FastAPI(
    title="3D USDZ Converter API",
    description=" GLB sang USDZ sử dụng Blender Python API"
)

TEMP_DIR = "/tmp/usdz_converter"
os.makedirs(TEMP_DIR, exist_ok=True)

class ConvertUrlRequest(BaseModel):
    url: str

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "scripts")

def preprocess_glb(input_path: str, output_path: str):
    """Chuyển WebP textures sang JPG/PNG bằng gltf-transform"""
    result = subprocess.run(
        ["node", os.path.join(SCRIPTS_DIR, "convertGlb.mjs"), input_path, output_path],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise Exception(f"Preprocess GLB failed: {result.stderr}")
    # print(result.stdout)

def convert_glb_to_usdz_sync(input_path: str, output_path: str):
    preprocessed_path = input_path.replace(".glb", "_processed.glb")
    
    preprocess_glb(input_path, preprocessed_path)

    # Suppress Blender logs
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()

    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        bpy.ops.import_scene.gltf(filepath=preprocessed_path)
    except Exception as e:
        raise Exception(f"Lỗi đọc file GLB: {str(e)}")

    try:
        bpy.ops.wm.usd_export(
            filepath=output_path,
            export_materials=True,
            export_uvmaps=True,
            export_normals=True,
            export_animation=True,
            evaluation_mode='RENDER'
        )
    except Exception as e:
        raise Exception(f"Lỗi xuất file USDZ: {str(e)}")
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        if os.path.exists(preprocessed_path):
            os.remove(preprocessed_path)

def upload_to_minio_sync(file_path: str, object_name: str) -> str:
    """Hàm upload file lên MinIO và trả về Public URL"""
    try:
        # Đẩy file lên bucket
        s3_client.upload_file(file_path, settings.MINIO_BUCKET, object_name)
        
        public_url = f"{settings.MINIO_PUBLIC_URL}/{settings.MINIO_BUCKET}/{object_name}"
        return public_url
    except Exception as e:
        raise Exception(f"Lỗi khi upload lên MinIO: {str(e)}")

def cleanup_files(paths: list):
    """Hàm dọn rác"""
    for path in paths:
        if os.path.exists(path):
            os.remove(path)

@app.get("/health")
def healthcheck() -> dict:
    return {"status": "ok"}

# API upload file
@app.post("/convert")
async def convert_model(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.glb'):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file định dạng .glb")

    job_id = str(uuid.uuid4())
    input_path = os.path.join(TEMP_DIR, f"{job_id}.glb")
    output_path = os.path.join(TEMP_DIR, f"{job_id}.usdz")

    minio_object_key = f"{job_id}.usdz"

    try:
        with open(input_path, "wb") as buffer:
            buffer.write(await file.read())

        convert_glb_to_usdz_sync(input_path, output_path)

        public_url = await asyncio.to_thread(upload_to_minio_sync, output_path, minio_object_key)

        background_tasks.add_task(cleanup_files, [input_path, output_path])

        return {
            "status": "success",
            "usdz_url": public_url
        }

    except Exception as e:
        cleanup_files([input_path, output_path])
        raise HTTPException(status_code=500, detail=str(e))
    
# API Convert from url
@app.post("/convert-from-url")
async def convert_from_url(request: ConvertUrlRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    input_path = os.path.join(TEMP_DIR, f"{job_id}.glb")
    output_path = os.path.join(TEMP_DIR, f"{job_id}.usdz")
    
    minio_object_key = f"{job_id}.usdz"

    try:
        try:
            await asyncio.to_thread(urllib.request.urlretrieve, request.url, input_path)
        except Exception as e:
            raise Exception(f"Không thể tải file từ URL: {str(e)}")

        convert_glb_to_usdz_sync(input_path, output_path)

        public_url = await asyncio.to_thread(upload_to_minio_sync, output_path, minio_object_key)

        background_tasks.add_task(cleanup_files, [input_path, output_path])

        return {
            "status": "success",
            "usdz_url": public_url
        }

    except Exception as e:
        cleanup_files([input_path, output_path])
        raise HTTPException(status_code=500, detail=str(e))

# API Convert from MinIO
class ConvertFromMinioRequest(BaseModel):
    url: str 

@app.post("/convert-from-minio")
async def convert_from_minio(request: ConvertFromMinioRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    input_path = os.path.join(TEMP_DIR, f"{job_id}.glb")
    output_path = os.path.join(TEMP_DIR, f"{job_id}.usdz")

    url = request.url.strip()

    if url.startswith("http://") or url.startswith("https://"):
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path_parts = parsed.path.lstrip("/").split("/", 1)
            if len(path_parts) < 2:
                raise ValueError("URL không hợp lệ")
            source_bucket = path_parts[0]
            object_key = path_parts[1]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Không thể parse URL: {str(e)}")
    else:
        source_bucket = settings.MINIO_BUCKET
        object_key = url

    minio_object_key = f"{job_id}.usdz"

    try:
        try:
            s3_client.download_file(source_bucket, object_key, input_path)
        except Exception as e:
            raise Exception(f"Không thể tải từ MinIO (bucket: {source_bucket}, key: {object_key}): {str(e)}")

        convert_glb_to_usdz_sync(input_path, output_path)

        public_url = await asyncio.to_thread(upload_to_minio_sync, output_path, minio_object_key)

        background_tasks.add_task(cleanup_files, [input_path, output_path])

        return {
            "status": "success",
            "usdz_url": public_url
        }

    except Exception as e:
        cleanup_files([input_path, output_path])
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/convert-local-direct", summary="Convert GLB sang USDZ và tải về trực tiếp")
async def convert_model_local_direct(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.glb'):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file định dạng .glb")

    job_id = str(uuid.uuid4())
    input_path = os.path.join(TEMP_DIR, f"{job_id}.glb")
    output_path = os.path.join(TEMP_DIR, f"{job_id}.usdz")

    try:
        # 1. Lưu file GLB người dùng upload vào thư mục tạm
        with open(input_path, "wb") as buffer:
            buffer.write(await file.read())

        # 2. Chạy hàm convert qua Blender
        convert_glb_to_usdz_sync(input_path, output_path)

        # Lấy tên file gốc (bỏ đuôi .glb) để đặt tên cho file tải về
        original_filename = os.path.splitext(file.filename)[0]
        download_filename = f"{original_filename}.usdz"

        # 3. Lên lịch dọn rác cả 2 file (FastAPI sẽ chạy cái này SAU KHI trả file về)
        background_tasks.add_task(cleanup_files, [input_path, output_path])

        # 4. Trả file trực tiếp về cho client
        return FileResponse(
            path=output_path, 
            filename=download_filename, 
            media_type='model/vnd.usdz+zip'
        )

    except Exception as e:
        # Nếu có lỗi giữa chừng thì dọn rác ngay lập tức
        cleanup_files([input_path, output_path])
        raise HTTPException(status_code=500, detail=str(e))