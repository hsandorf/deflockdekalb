
import os
import tempfile
import hashlib
import requests
import duckdb
import streamlit as st


# Limit DuckDB's resource consumption on Community Cloud
DUCKDB_MEMORY_LIMIT = "1GB"
DUCKDB_THREADS = 2

TEMP_DIR = os.path.join(
    tempfile.gettempdir(),
    "dekalb_flock_data"
)

os.makedirs(TEMP_DIR, exist_ok=True)


def sql_file_path(path):
    """Safely quote a local file path for DuckDB SQL."""
    return "'" + path.replace("'", "''") + "'"


@st.cache_resource(show_spinner="Downloading data...")
def download_file(url):
    """
    Download a dataset once per app runtime.
    Store it on local temporary disk instead of RAM.
    """

    filename = hashlib.sha256(
        url.encode("utf-8")
    ).hexdigest()

    path = os.path.join(TEMP_DIR, filename)

    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path

    partial_path = path + ".part"

    try:
        with requests.get(
            url,
            stream=True,
            timeout=(30, 300)
        ) as response:

            response.raise_for_status()

            with open(partial_path, "wb") as file:

                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):
                    if chunk:
                        file.write(chunk)

        os.replace(partial_path, path)

    except Exception:
        if os.path.exists(partial_path):
            os.remove(partial_path)
        raise

    return path


def get_connection():
    """
    Create a lightweight DuckDB connection.
    Use disk for temporary spill files.
    """

    return duckdb.connect(
        database=":memory:",
        config={
            "memory_limit": DUCKDB_MEMORY_LIMIT,
            "threads": DUCKDB_THREADS,
            "temp_directory": TEMP_DIR
        }
    )


def query_parquet(path, sql):
    """Run a query against a Parquet file."""

    with get_connection() as connection:
        return connection.execute(sql).fetchdf()


def query_csv(path, sql):
    """Run a query against a CSV file."""

    with get_connection() as connection:
        return connection.execute(sql).fetchdf()
