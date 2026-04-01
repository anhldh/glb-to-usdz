import bpy
import os
import uuid
import asyncio
import urllib.request
import boto3
from botocore.client import Config
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from config import settings

# ==========================================
# KHỞI TẠO S3 CLIENT (TÙY CHỌN)
# ==========================================
s3_client = None

# Chỉ khởi tạo boto3 nếu người dùng có cấu hình biến môi trường MINIO
if settings.MINIO_ENDPOINT and settings.MINIO_ACCESS_KEY:
    protocol = "https" if settings.MINIO_USE_SSL else "http"
    full_endpoint_url = f"{protocol}://{settings.MINIO_ENDPOINT}:{settings.MINIO_PORT}"
    
    s3_client = boto3.client(
        's3',
        endpoint_url=full_endpoint_url,
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        config=Config(signature_version='s3v4')
    )

app = FastAPI(title="3D USDZ Converter API")

TEMP_DIR = "/tmp/usdz_converter"
os.makedirs(TEMP_DIR, exist_ok=True)

class ConvertUrlRequest(BaseModel):
    url: str

def convert_glb_to_usdz_sync(input_path: str, output_path: str):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        bpy.ops.import_scene.gltf(filepath=input_path)
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

def upload_to_minio_sync(file_path: str, object_name: str) -> str:
    try:
        s3_client.upload_file(file_path, settings.MINIO_BUCKET, object_name)
        public_url = f"{settings.MINIO_PUBLIC_URL}/{settings.MINIO_BUCKET}/{object_name}"
        return public_url
    except Exception as e:
        raise Exception(f"Lỗi khi upload lên MinIO: {str(e)}")

def cleanup_files(paths: list):
    for path in paths:
        if os.path.exists(path):
            os.remove(path)

# ==========================================
# API 1: NHẬN FILE
# ==========================================
@app.post("/convert")
async def convert_model(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.glb'):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file định dạng .glb")

    job_id = str(uuid.uuid4())
    input_path = os.path.join(TEMP_DIR, f"{job_id}.glb")
    output_path = os.path.join(TEMP_DIR, f"{job_id}.usdz")
    
    original_filename = file.filename.lower().replace('.glb', '')
    minio_object_key = f"{job_id}-{original_filename}.usdz"

    try:
        with open(input_path, "wb") as buffer:
            buffer.write(await file.read())

        convert_glb_to_usdz_sync(input_path, output_path)

        # Kiểm tra xem có kết nối MinIO không
        if s3_client and settings.MINIO_BUCKET:
            public_url = await asyncio.to_thread(upload_to_minio_sync, output_path, minio_object_key)
            background_tasks.add_task(cleanup_files, [input_path, output_path])
            return {
                "status": "success",
                "job_id": job_id,
                "minio_key": minio_object_key,
                "usdz_url": public_url
            }
        else:
            # Nếu không có MinIO, trả thẳng file USDZ về cho user tải
            background_tasks.add_task(cleanup_files, [input_path, output_path])
            return FileResponse(
                path=output_path, 
                filename=f"{original_filename}.usdz",
                media_type="model/vnd.usdz+zip"
            )

    except Exception as e:
        cleanup_files([input_path, output_path])
        raise HTTPException(status_code=500, detail=str(e))
    
# ==========================================
# API 2: NHẬN URL
# ==========================================
@app.post("/convert-from-url")
async def convert_from_url(request: ConvertUrlRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    input_path = os.path.join(TEMP_DIR, f"{job_id}.glb")
    output_path = os.path.join(TEMP_DIR, f"{job_id}.usdz")
    
    original_filename = request.url.split('/')[-1].split('?')[0].replace('.glb', '')
    if not original_filename:
        original_filename = "model"
        
    minio_object_key = f"usdz-models/{job_id}-{original_filename}.usdz"

    try:
        try:
            await asyncio.to_thread(urllib.request.urlretrieve, request.url, input_path)
        except Exception as e:
            raise Exception(f"Không thể tải file từ URL: {str(e)}")

        convert_glb_to_usdz_sync(input_path, output_path)

        # Kiểm tra xem có kết nối MinIO không
        if s3_client and settings.MINIO_BUCKET:
            public_url = await asyncio.to_thread(upload_to_minio_sync, output_path, minio_object_key)
            background_tasks.add_task(cleanup_files, [input_path, output_path])
            return {
                "status": "success",
                "job_id": job_id,
                "minio_key": minio_object_key,
                "usdz_url": public_url
            }
        else:
            # Nếu không có MinIO, trả thẳng file USDZ về cho user tải
            background_tasks.add_task(cleanup_files, [input_path, output_path])
            return FileResponse(
                path=output_path, 
                filename=f"{original_filename}.usdz",
                media_type="model/vnd.usdz+zip"
            )

    except Exception as e:
        cleanup_files([input_path, output_path])
        raise HTTPException(status_code=500, detail=str(e))