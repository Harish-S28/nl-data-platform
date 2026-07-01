from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.nl_to_sql import generate_sql, run_query, generate_insight, UnsafeQueryError
from app.db import list_tables

router = APIRouter()


class QueryRequest(BaseModel):
    table_name: str
    question: str


@router.post("/query")
def query_dataset(req: QueryRequest):
    if req.table_name not in list_tables():
        raise HTTPException(status_code=404, detail="Table not found. Upload a dataset first.")

    try:
        sql_result = generate_sql(req.table_name, req.question)
    except UnsafeQueryError as e:
        raise HTTPException(status_code=400, detail=f"Generated query was rejected: {e}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQL generation failed: {e}")

    try:
        results = run_query(sql_result["sql"])
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Generated SQL failed to execute: {e}. SQL was: {sql_result['sql']}",
        )

    try:
        insight = generate_insight(req.question, sql_result["sql"], results)
    except Exception:
        insight = ""

    return {
        "question": req.question,
        "sql": sql_result["sql"],
        "insight": insight,
        **results,
    }
