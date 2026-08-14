import os
import boto3
from botocore.exceptions import ClientError
from botocore.client import Config
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

IMAGE_BUCKET = os.getenv("IMAGE_BUCKET", "build91matcher-dev")
VIDEO_BUCKET = os.getenv("VIDEO_BUCKET", "build91matcher-prod")

# Use sigv4 for presigned URLs and force virtual hosting to avoid path-style deprecation and CORS issues
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
    config=Config(
        signature_version="s3v4",
        s3={"addressing_style": "virtual"}
    ),
)

def get_available_buckets():
    return [IMAGE_BUCKET, VIDEO_BUCKET]

def generate_presigned_url(bucket_name: str, object_key: str, expiration: int = 3600, content_type: str = None):
    try:
        params = {
            "Bucket": bucket_name,
            "Key": object_key
        }
        if content_type:
            params["ContentType"] = content_type
            
        url = s3_client.generate_presigned_url(
            "put_object",
            Params=params,
            ExpiresIn=expiration
        )
        return url
    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return None

def list_objects(bucket_name: str, max_keys: int = 20, continuation_token: str = None):
    try:
        kwargs = {
            "Bucket": bucket_name,
            "MaxKeys": max_keys
        }
        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token
            
        response = s3_client.list_objects_v2(**kwargs)
        
        # Get signed urls for reading objects (if they are private)
        import mimetypes
        objects = []
        for obj in response.get("Contents", []):
            params = {"Bucket": bucket_name, "Key": obj["Key"]}
            mime_type, _ = mimetypes.guess_type(obj["Key"])
            if mime_type:
                params["ResponseContentType"] = mime_type
                
            objects.append({
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"],
                "url": s3_client.generate_presigned_url(
                    "get_object",
                    Params=params,
                    ExpiresIn=3600
                )
            })
            
        return {
            "objects": objects,
            "next_token": response.get("NextContinuationToken")
        }
    except ClientError as e:
        print(f"Error listing objects: {e}")
        return {"objects": [], "next_token": None}

def copy_object(source_bucket: str, source_key: str, dest_bucket: str, dest_key: str):
    try:
        copy_source = {
            'Bucket': source_bucket,
            'Key': source_key
        }
        s3_client.copy_object(CopySource=copy_source, Bucket=dest_bucket, Key=dest_key)
        return True
    except ClientError as e:
        print(f"Error copying object: {e}")
        return False

def delete_object(bucket_name: str, object_key: str):
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=object_key)
        return True
    except ClientError as e:
        print(f"Error deleting object: {e}")
        return False
