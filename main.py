from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import upload, gallery

app = FastAPI(title="S3 Upload System API")

# Allow requests from the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(gallery.router, prefix="/api/gallery", tags=["Gallery"])

@app.get("/")
def read_root():
    return {"message": "S3 Upload System API is running"}
