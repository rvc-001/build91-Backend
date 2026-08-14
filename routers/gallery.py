import json
import base64
from fastapi import APIRouter, HTTPException, Query
from s3_service import get_available_buckets, list_objects

router = APIRouter()

@router.get("/")
def get_gallery(bucket: str = Query(None), continuation_token: str = Query(None)):
    buckets = get_available_buckets()
    if not buckets:
        raise HTTPException(status_code=500, detail="No S3 buckets configured")
        
    if bucket:
        if bucket not in buckets:
            raise HTTPException(status_code=400, detail="Invalid bucket")
        res = list_objects(bucket, max_keys=20, continuation_token=continuation_token)
        for obj in res["objects"]:
            obj["bucket"] = bucket
        return res

    # Combined mode
    tokens = {}
    if continuation_token:
        try:
            tokens = json.loads(base64.b64decode(continuation_token.encode()).decode())
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid continuation token")
            
    combined_objects = []
    next_tokens = {}
    
    for b in buckets:
        token = tokens.get(b)
        res = list_objects(b, max_keys=15, continuation_token=token)
        for obj in res["objects"]:
            obj["bucket"] = b
        combined_objects.extend(res["objects"])
        if res.get("next_token"):
            next_tokens[b] = res["next_token"]
            
    # Sort by last modified descending
    combined_objects.sort(key=lambda x: x["last_modified"], reverse=True)
    
    next_token_str = None
    if next_tokens:
        next_token_str = base64.b64encode(json.dumps(next_tokens).encode()).decode()
        
    return {
        "objects": combined_objects,
        "next_token": next_token_str
    }

