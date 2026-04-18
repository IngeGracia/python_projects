from psycopg.types.json import Jsonb
from typing import List, Any, Dict
import psycopg
from psycopg.rows import dict_row
from pgvector.psycopg import register_vector


class SupabaseDocStore:
    def __init__(self, database_url:str):
        self.database_url = database_url

    def _conn(self):
        conn = psycopg.connect(self.database_url, row_factory=dict_row)
        register_vector(conn)
        return conn

    # Los parámetros son los campos de la tabla que creamos en Supabase
    def insert_chunk(self, content:str, metadata:Dict[str, Any], embedding:List[float]):
        sql = """
            insert into public.documents(content, metadata, embedding)
            values(%s, %s, %s)
        """
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql, (content, Jsonb(metadata), embedding)
                )
                conn.commit()

    def search_chunks(self, query_embedding, k=5):
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT content, metadata, embedding
                    FROM chunks
                    ORDER BY embedding <-> %s
                    LIMIT %s
                    """,
                    (query_embedding, k)
                )
                return cur.fetchall()