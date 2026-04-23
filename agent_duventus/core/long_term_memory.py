import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv


class LongTermMemory:
    def __init__(self):
        load_dotenv()
        self.host = os.environ.get("DATABASE_URL")


    # Obtener la conexión de BD Postgres (Supabase)
    def get_conn(self):
        # row_factory: Hace que nos devuelva los resultados como un diccionario, no como tuplas
        return psycopg.connect(self.host, row_factory=dict_row)


    # Obtener las memorias a largo plazo almacenadas
    def get_long_term_memories(self, id_user:str, limit:int=20):
        with self.get_conn() as conn, conn.cursor() as cursor:
            cursor.execute(
                """
                select
                    "created_at" at time zone 'utc' at time zone 'america/hermosillo' as "created_at", "memory" 
                from largo_plazo
                where
                    "id_user" = %s
                order by
                    "created_at" desc
                limit %s
                ;""",
                (id_user, limit)
            )
            return cursor.fetchall()


    # Guardar una nueva memoria a largo plazo
    def insert_long_term_memory(self, id_user:str, memory:str):
        print(f"Guardando memoria: ({id_user}, {memory})")

        with self.get_conn() as conn, conn.cursor() as cursor:
            cursor.execute(
                """
                insert into largo_plazo("id_user", "memory", "created_at")
                values (%s, %s, now() at time zone 'utc')
                ;""",
                (id_user, memory)
            )
            conn.commit()


    # Obtener las memorias en un formato de texto para el System Prompt
    def format_memories(self, memories):
        if not memories:
            return
        
        lines = [f"- {m['created_at'].strftime('%Y-%m-%d %H:%M:%S')}: {m['memory']}\n" for m in memories]
        return "".join(lines)


if __name__ == "__main__":
    load_dotenv()
    ltm = LongTermMemory()
    ltm.set_conn()
    result = ltm.get_long_term_memories("bunbury")
    # result = ltm.insert_long_term_memory("bunbury", "Memoria enviada desde Python")
    result = ltm.format_memories(result)
    print(result)