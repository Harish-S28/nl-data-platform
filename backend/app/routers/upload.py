import os
import shutil
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.etl import ingest_file
from app.config import DATA_DIR

router = APIRouter()

ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls", "json"}
UPLOAD_TMP_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOAD_TMP_DIR, exist_ok=True)


@router.get("/tables")
def get_tables():
    from app.db import list_tables, get_table_schema
    tables = list_tables()
    return [{"table_name": t, "columns": get_table_schema(t)} for t in tables]


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    ext = file.filename.lower().rsplit(".", 1)[-1] if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    tmp_path = os.path.join(UPLOAD_TMP_DIR, f"{uuid.uuid4().hex}_{file.filename}")
    try:
        with open(tmp_path, "wb") as out:
            shutil.copyfileobj(file.file, out)

        result = ingest_file(tmp_path, file.filename)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
