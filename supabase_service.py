import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase credentials not found in environment variables")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_table_name(bucket: str) -> str:
    from s3_service import VIDEO_BUCKET
    return 'video_metadata' if bucket == VIDEO_BUCKET else 'media_metadata'

def get_metadata_from_db(bucket: str, key: str) -> dict:
    try:
        supabase = get_supabase_client()
        table_name = get_table_name(bucket)
        response = supabase.table(table_name).select('*').eq('bucket', bucket).eq('key', key).execute()
        
        if response.data and len(response.data) > 0:
            data = response.data[0]
            url_val = data.get("videolink") if table_name == 'video_metadata' else data.get("url")
            return {
                "alt_text": data.get("alt_text", ""),
                "tags": data.get("tags", ""),
                "expiry_date": data.get("expiry_date", ""),
                "url": url_val or ""
            }
        return {"alt_text": "", "tags": "", "expiry_date": "", "url": ""}
    except Exception as e:
        print(f"Error fetching metadata from Supabase: {e}")
        return {"alt_text": "", "tags": "", "expiry_date": "", "url": ""}

def put_metadata_to_db(bucket: str, key: str, alt_text: str, tags: str, expiry_date: str, url: str) -> bool:
    try:
        supabase = get_supabase_client()
        table_name = get_table_name(bucket)
        
        # Upsert the metadata
        data = {
            "bucket": bucket,
            "key": key,
            "alt_text": alt_text,
            "tags": tags,
            "expiry_date": expiry_date,
        }
        
        if table_name == 'video_metadata':
            data["videolink"] = url
        else:
            data["url"] = url
        
        response = supabase.table(table_name).upsert(data, on_conflict='bucket,key').execute()
        return True
    except Exception as e:
        print(f"Error saving metadata to Supabase: {e}")
        return False

def delete_metadata_from_db(bucket: str, key: str) -> bool:
    try:
        supabase = get_supabase_client()
        table_name = get_table_name(bucket)
        response = supabase.table(table_name).delete().eq('bucket', bucket).eq('key', key).execute()
        return True
    except Exception as e:
        print(f"Error deleting metadata from Supabase: {e}")
        return False
