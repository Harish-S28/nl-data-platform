import os
import re
import csv
import uuid
import pandas as pd

from app.db import get_connection, quote_ident


def _clean_column_name(col: str) -> str:
    """Turn arbitrary header text into a safe SQL identifier."""
    col = str(col).strip()
    col = re.sub(r"[^0-9a-zA-Z_]+", "_", col)
    col = re.sub(r"_+", "_", col).strip("_")
    if not col:
        col = "col"
    if col[0].isdigit():
        col = f"c_{col}"
    return col.lower()


def _read_file(file_path: str, original_filename: str) -> pd.DataFrame:
    ext = original_filename.lower().rsplit(".", 1)[-1]
    if ext == "csv":
        # Auto-detect delimiter (comma, semicolon, tab, pipe) instead of assuming comma
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            sample = f.read(4096)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            sep = dialect.delimiter
        except csv.Error:
            sep = ","
        df = pd.read_csv(file_path, sep=sep)
        # Fallback: if it still parsed as a single column, force comma split
        if df.shape[1] == 1 and ("," in df.columns[0] or ";" in df.columns[0]):
            for fallback_sep in [",", ";", "\t", "|"]:
                trial = pd.read_csv(file_path, sep=fallback_sep)
                if trial.shape[1] > 1:
                    df = trial
                    break
        return df
    elif ext in ("xlsx", "xls"):
        return pd.read_excel(file_path)
    elif ext == "json":
        return pd.read_json(file_path)
    else:
        raise ValueError(f"Unsupported file type: .{ext}")


def _infer_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    # Deduplicate cleaned column names
    seen = {}
    new_cols = []
    for col in df.columns:
        clean = _clean_column_name(col)
        if clean in seen:
            seen[clean] += 1
            clean = f"{clean}_{seen[clean]}"
        else:
            seen[clean] = 0
        new_cols.append(clean)
    df.columns = new_cols

    # Best-effort type coercion: try numeric, then datetime, else leave as text
    for col in df.columns:
        if df[col].dtype == object:
            coerced_numeric = pd.to_numeric(df[col], errors="coerce")
            if coerced_numeric.notna().mean() > 0.9:
                df[col] = coerced_numeric
                continue
            coerced_date = pd.to_datetime(df[col], errors="coerce", format=None)
            if coerced_date.notna().mean() > 0.9:
                df[col] = coerced_date

    return df


def ingest_file(file_path: str, original_filename: str) -> dict:
    """
    Reads an uploaded file, detects/cleans schema, loads it into DuckDB
    as a new table, and returns metadata about the resulting table.
    """
    df = _read_file(file_path, original_filename)
    if df.empty:
        raise ValueError("Uploaded file contains no rows")

    df = _infer_and_clean(df)

    table_name = "t_" + uuid.uuid4().hex[:10]

    con = get_connection()
    try:
        con.register("tmp_df", df)
        con.execute(
            f"CREATE TABLE {quote_ident(table_name)} AS SELECT * FROM tmp_df"
        )
        con.unregister("tmp_df")

        schema_rows = con.execute(f"DESCRIBE {quote_ident(table_name)}").fetchall()
        schema = [{"column": r[0], "type": r[1]} for r in schema_rows]

        row_count = con.execute(
            f"SELECT COUNT(*) FROM {quote_ident(table_name)}"
        ).fetchone()[0]
    finally:
        con.close()

    return {
        "table_name": table_name,
        "original_filename": original_filename,
        "row_count": row_count,
        "columns": schema,
    }
