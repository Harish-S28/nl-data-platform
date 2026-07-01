import re
import math

from app.config import groq_client, GROQ_MODEL
from app.db import get_table_schema, get_sample_rows, get_connection, quote_ident


class UnsafeQueryError(Exception):
    pass


def _build_schema_context(table_name: str) -> str:
    schema = get_table_schema(table_name)
    samples = get_sample_rows(table_name, limit=3)
    schema_lines = "\n".join(f"- {c['column']} ({c['type']})" for c in schema)
    sample_lines = "\n".join(str(row) for row in samples)
    return f"""Table name: {table_name}\n\nColumns:\n{schema_lines}\n\nSample rows:\n{sample_lines}\n"""


def _extract_sql(raw_text: str) -> str:
    match = re.search(r"```(?:sql)?\s*(.*?)```", raw_text, re.DOTALL | re.IGNORECASE)
    sql = match.group(1) if match else raw_text
    return sql.strip().rstrip(";")


def _validate_sql(sql: str, table_name: str):
    lowered = sql.strip().lower()
    if not lowered.startswith("select"):
        raise UnsafeQueryError("Only SELECT queries are allowed.")
    if ";" in sql.strip().rstrip(";"):
        raise UnsafeQueryError("Multiple statements are not allowed.")
    forbidden = ["insert","update","delete","drop","alter","create","truncate","attach","copy","pragma","exec","call"]
    for word in forbidden:
        if re.search(rf"\b{word}\b", lowered):
            raise UnsafeQueryError(f"Disallowed keyword detected: {word}")
    if table_name.lower() not in lowered:
        raise UnsafeQueryError("Query does not reference the expected table.")


def generate_sql(table_name: str, question: str) -> dict:
    if groq_client is None:
        raise RuntimeError("GROQ_API_KEY is not configured on the server.")
    schema_context = _build_schema_context(table_name)
    system_prompt = (
        "You are a SQL generator for DuckDB. Given a table schema and a "
        "plain-English question, output ONLY a single SELECT SQL statement "
        "that answers the question. Rules:\n"
        "- Use only the exact table and column names provided.\n"
        "- Never use INSERT, UPDATE, DELETE, DROP, ALTER, or any DDL/DML.\n"
        "- Never include explanations, only the SQL.\n"
        "- Wrap the SQL in a ```sql code block.\n"
        "- If the question cannot be answered with the given columns, "
        "select the closest reasonable interpretation."
    )
    user_prompt = f"""Schema:\n{schema_context}\n\nQuestion: {question}\n\nWrite a single DuckDB SELECT statement to answer this question."""
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        max_tokens=600,
    )
    raw_text = response.choices[0].message.content
    sql = _extract_sql(raw_text)
    _validate_sql(sql, table_name)
    return {"sql": sql, "raw_model_output": raw_text}


def run_query(sql: str) -> dict:
    con = get_connection()
    try:
        df = con.execute(sql).df()
    finally:
        con.close()

    def clean(val):
        if isinstance(val, float) and math.isnan(val):
            return None
        return val

    rows = [
        {col: clean(val) for col, val in row.items()}
        for row in df.to_dict(orient="records")
    ]

    return {
        "columns": list(df.columns),
        "rows": rows,
        "row_count": len(df),
    }


def generate_insight(question: str, sql: str, results: dict) -> str:
    if groq_client is None:
        return ""
    sample_rows = results["rows"][:20]
    prompt = f"""A user asked this question about their data: "{question}"

This SQL was run: {sql}

Result columns: {results['columns']}
Result row count: {results['row_count']}
Sample of the results: {sample_rows}

Write a short (2-4 sentence) plain-English business insight summarizing what
this result shows. Be specific with numbers where relevant. Do not repeat
the SQL or mention "the query". Write as if explaining the finding to a
non-technical business stakeholder."""
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()