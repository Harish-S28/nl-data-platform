import duckdb
from app.config import DB_PATH


def get_connection():
    """
    Returns a DuckDB connection to the shared warehouse file.
    DuckDB handles concurrent reads fine for this use case;
    each request opens and closes its own connection.
    """
    return duckdb.connect(DB_PATH)


def list_tables():
    con = get_connection()
    try:
        rows = con.execute("SHOW TABLES").fetchall()
        return [r[0] for r in rows]
    finally:
        con.close()


def get_table_schema(table_name: str):
    con = get_connection()
    try:
        rows = con.execute(f"DESCRIBE {quote_ident(table_name)}").fetchall()
        # DESCRIBE returns: column_name, column_type, null, key, default, extra
        return [{"column": r[0], "type": r[1]} for r in rows]
    finally:
        con.close()


def get_sample_rows(table_name: str, limit: int = 5):
    con = get_connection()
    try:
        df = con.execute(f"SELECT * FROM {quote_ident(table_name)} LIMIT {limit}").df()
        return df.to_dict(orient="records")
    finally:
        con.close()


def quote_ident(name: str) -> str:
    """Safely quote a DuckDB identifier (table/column name)."""
    return '"' + name.replace('"', '""') + '"'
