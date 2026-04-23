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

    def search_chunks(self, query_emb, k:int=3):
        sql = """
            select * from public.match_documents(%s::vector(3072), %s, %s)
        """

        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (query_emb, k, Jsonb({})))
                rows = cur.fetchall()

        return [
            {
                "id": int(r["id"]),
                "content": r["content"],
                "metadata": r["metadata"] or {},
                "similarity": float(r["similarity"])
            }
            for r in rows
        ]