from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
import uuid
from s3_service import get_available_buckets, generate_presigned_url, copy_object, delete_object

router = APIRouter()

class UploadRequest(BaseModel):
    filename: str
    content_type: str
    bucket: Optional[str] = None

class ReplaceRequest(BaseModel):
    bucket: str
    original_key: str
    filename: str
    content_type: str

class ConfirmReplaceRequest(BaseModel):
    bucket: str
    original_key: str
    temp_key: str

def get_bucket_for_mime(content_type: str) -> str:
    from s3_service import IMAGE_BUCKET, VIDEO_BUCKET
    is_video = content_type.lower().startswith("video/")
    if is_video:
        return VIDEO_BUCKET
    else:
        return IMAGE_BUCKET

@router.get("/buckets")
def list_buckets():
    buckets = get_available_buckets()
    return {"buckets": buckets}

@router.post("/presigned-url")
def get_presigned_url(request: UploadRequest):
    bucket = request.bucket
    if not bucket:
        bucket = get_bucket_for_mime(request.content_type)
        
    if bucket not in get_available_buckets():
        raise HTTPException(status_code=400, detail="Invalid bucket")
        
    # Generate a unique key for the new upload to avoid collisions
    ext = request.filename.split('.')[-1] if '.' in request.filename else ''
    object_key = f"{uuid.uuid4().hex}_{request.filename}" if not ext else f"{uuid.uuid4().hex}.{ext}"
    
    url = generate_presigned_url(bucket, object_key, content_type=request.content_type)
    if not url:
        raise HTTPException(status_code=500, detail="Failed to generate presigned URL")
        
    return {"url": url, "key": object_key, "bucket": bucket}

@router.post("/replace-url")
def get_replace_url(request: ReplaceRequest):
    if request.bucket not in get_available_buckets():
        raise HTTPException(status_code=400, detail="Invalid bucket")
        
    orig_ext = request.original_key.split('.')[-1] if '.' in request.original_key else ''
    new_ext = request.filename.split('.')[-1] if '.' in request.filename else ''

    # Generate a temp key for the replacement upload
    temp_key = f"temp_replace_{uuid.uuid4().hex}.{new_ext}"
    
    url = generate_presigned_url(request.bucket, temp_key, content_type=request.content_type)
    if not url:
        raise HTTPException(status_code=500, detail="Failed to generate presigned URL")
        
    return {"url": url, "temp_key": temp_key, "original_key": request.original_key}

@router.post("/confirm-replace")
def confirm_replace(request: ConfirmReplaceRequest):
    if request.bucket not in get_available_buckets():
        raise HTTPException(status_code=400, detail="Invalid bucket")
        
    # Copy the temp object over the original object
    success = copy_object(request.bucket, request.temp_key, request.bucket, request.original_key)
    
    if success:
        # Delete the temp object
        delete_object(request.bucket, request.temp_key)
        return {"message": "Replacement confirmed successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to replace object in S3")

@router.delete("/")
def delete_item(bucket: str, object_key: str):
    if bucket not in get_available_buckets():
        raise HTTPException(status_code=400, detail="Invalid bucket")
        
    success = delete_object(bucket, object_key)
    if success:
        return {"message": "Object deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete object in S3")
