import time
from fastapi import APIRouter, Response, status
from s3_service import s3_client, IMAGE_BUCKET
from supabase_service import get_supabase_client

router = APIRouter()

@router.get("")
@router.get("/")
def health_check(response: Response):
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {}
    }
    
    # 1. Check Supabase connection
    db_start = time.time()
    try:
        supabase = get_supabase_client()
        # Querying media_metadata table to verify read access and table presence
        supabase.table('media_metadata').select('*').limit(1).execute()
        db_latency = time.time() - db_start
        health_status["services"]["supabase"] = {
            "status": "healthy",
            "latency_ms": round(db_latency * 1000, 2)
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["services"]["supabase"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # 2. Check S3 connection
    s3_start = time.time()
    try:
        # Check S3 access using a fast metadata/listing operation
        s3_client.list_objects_v2(Bucket=IMAGE_BUCKET, MaxKeys=1)
        s3_latency = time.time() - s3_start
        health_status["services"]["s3"] = {
            "status": "healthy",
            "latency_ms": round(s3_latency * 1000, 2)
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["services"]["s3"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    if health_status["status"] == "unhealthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
    return health_status
