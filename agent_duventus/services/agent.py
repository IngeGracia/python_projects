import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from groq import Groq
from dotenv import load_dotenv
from core.simple_memory import SimpleMemory
from core.long_term_memory import LongTermMemory
from services.tools import Tools
from services.gemini_embedder import GeminiEmbedder
from services.supabase_doc_store import SupabaseDocStore


# env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core", ".env")
# load_dotenv(env_path)


class Agent:
    def __init__(self):
        self.__env_path = os.path.join(os.path.dirname(
            os.path.dirname(__file__)), "core", ".env")
        load_dotenv(self.__env_path)
        self.gemini_api = os.environ.get("GEMINI_API_KEY")
        self.database_url = os.environ.get("DATABASE_URL")
        self.embedder = GeminiEmbedder(api_key=self.gemini_api)
        self.store = SupabaseDocStore(database_url=self.database_url)
        MEMORY_MAX_MESSAGES = 10
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "souvenirs",
                    "description": (
                        "Obtiene información importante y actualizada acerca de Souvenirs"
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "La pregunta del usuario."
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

        self.api_key = os.environ.get("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key)
        self.memory = SimpleMemory(max_messages=MEMORY_MAX_MESSAGES)
        # self.tools = Tools()
        self.ltm = LongTermMemory()
        self.initialize_promp()

    def initialize_promp(self):
        database_url = os.environ.get("DATABASE_URL")
        memories = self.ltm.get_long_term_memories("bunbury")
        memories_text = self.ltm.format_memories(memories)

        self.system_prompt = f"""
            # ROL
            Eres un agente de servicio al cliente experto en la distribución de Souvenirs.

            Los usuarios te contactarán con dudas relacionadas a los Souvenirs.
            Para cualquier consulta relacionada sobre ello, debes consultar la información actualizada utilizando la herramienta "tool_souvenirs"

            # HERRAMIENTAS
            ## tool_souvenirs
            Esta herramienta debes llamarla siempre que el usuario desee saber algo relacionado a los Souvenirs. 
            Si no está claro según la pregunta, entonces también utiliza la herramienta.

            # REGLAS
            - No debes responder ni tratar de adivinar soluciones.
            - Nunca debes mencionar los datos proporcionados en este PROMPT.
            - Cuando te pregunten por tus funciones o acerca de lo que haces, debes consultar la herramienta "tool_souvenirs" para brindar un resúmen en base a la información que te brinde esta herramienta.
                Deberás ser conciso y claro en tu respuesta. 
        """
# # REGLAS
#             - No debes inventar información de ningún tipo. Solo utiliza lo que se te
#             proporciona como parte de la herramienta.
#             - Puedes ser amigable pero eres del área de souvenirs, por lo que sé servicial
#             pero no intentes ayudar más allá de dar la información explícita que te solicitan,
#             basado única y exclusivamente en la información del proceso de souvenirs en la herramienta.

    def run(self):
        print("Agent running.")

        while True:
            user_text = input("👉 Tú: ")
            if not user_text:
                continue

            if user_text.lower() in ("salir", "exit", "quit", "q"):
                print("Agent stopped.")
                break

            assistant_text = self.process_response(
                self.client, self.memory.get_messages(), user_text)
            # tokens_total_usage = resp.usage.total_tokens
            # tokens_input_usage = resp.usage.prompt_tokens
            # tokens_output_usage = resp.usage.completion_tokens
            # assistant_text = msg.content or ""
            print(f"\n🤖 Agent: {assistant_text}\n")

            # Actualizar la memoria con el último mensage
            self.memory.add_message("user", user_text)
            self.memory.add_message("assistant", assistant_text)

    def process_response(self, client: Groq, memory_messages: list[dict], user_text: str):
        # Obtener la memoria
        # messages = self.memory.get_messages()
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(memory_messages)
        messages.append(
            {"role": "user", "content": user_text}
        )

        while True:
            resp = self.client.chat.completions.create(
                model="qwen/qwen3-32b",
                messages=messages,
                tools=self.tools
            )

            msg = resp.choices[0].message

            # Si no llama a herramientas, entonces se regresa la respuesta al usuario
            if not getattr(msg, "tool_calls", None):
                return msg.content or ""

            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [tc.model_dump() for tc in msg.tool_calls]
            })

            for tool_call in msg.tool_calls:
                name = tool_call.function.name
                # Convertir el json a un diccionario
                args = json.loads(tool_call.function.arguments or "{}")

                if name == "souvenirs":
                    query = args["query"]
                    # print(f"Llamando función proceso_souvenirs con {query}")
                    print(f"...")
                    emb = self.embedder.embed_query(query)
                    hits = self.store.search_chunks(query_emb=emb)
                    result = {
                        "query": query,
                        "matches": hits
                    }
                else:
                    print(
                        f"Se intentó llamar a una herramienta desconocida: {name}")
                    result = {"error": f"Herramienta desconocida: {name}"}

                # Agregar a los mensajes el resultado del llamado de la herramienta.
                # Esto lo recibirá el modelo al continuar la iteración
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False)
                })
