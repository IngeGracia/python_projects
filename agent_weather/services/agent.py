import os, json
from datetime import datetime
from zoneinfo import ZoneInfo
from groq import Groq
from dotenv import load_dotenv
from core.simple_memory import SimpleMemory
from services.tools import Tools


env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core", ".env")
load_dotenv(env_path)
MEMORY_MAX_MESSAGES = 10
TOOLS = [
            {
                "type": "function",
                "function": {
                    "name": "check_availability",
                    "description": (
                        "Revisa si el calendario del usuario está disponible entre time_ini y time_end usando Google Calendar."
                        "Los datos time_ini y time_end DEBEN estar en el formato RFC3339 (con offset para la zona horaria). Por ejemplo: "
                        "2026-04-14T15:00:00-07:00"
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "time_ini": {
                                "type": "string",
                                "description": "Fecha y hora de inicio en formato RFC3339 (con offset para la zona horaria)."
                            },
                            "time_end": {
                                "type": "string",
                                "description": "Fecha y hora de fin en formato RFC3339 (con offset para la zona horaria)."
                            }
                        },
                        "required": ["time_ini", "time_end"]
                    }
                }
            },
            {
                "type": "function",
                "function":{
                    "name": "create_event",
                    "description": (
                        "Crea un evento en el calendario del usuario usando Google Calendar."
                        "Los datos start y end DEBEN estar en el formato RFC3339 (con offset para la zona horaria). Por ejemplo: "
                        "2026-04-14T15:00:00-07:00"
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "summary": {
                                "type": "string",
                                "description": "Resumen del evento."
                            },
                            "start": {
                                "type": "string",
                                "description": "Fecha y hora de inicio en formato RFC3339 (con offset para la zona horaria)."
                            },
                            "end": {
                                "type": "string",
                                "description": "Fecha y hora de fin en formato RFC3339 (con offset para la zona horaria)."
                            },
                            "description": {
                                "type": "string",
                                "description": "Descripción del evento (Este es opcional)"
                            }
                        },
                        "required": ["summary", "start", "end"]
                    }
                }
            }
        ]
SYSTEM_PROMPT = f"""
    Eres un asistente que habla español y recibe de una manera breve y concisa en español latino (México).

    Reglas:
        - Antes de crear una reunión, siempre debes pedir confirmación explícita del usuario.
        - Si el usuario no confirma, no puedes llamar a la herramienta create_event.
        - Cada vez que crees un evento en el calendario (Únicamente cuando ya hayas creado el evento), debes indicarle al usuario los datos con los que creaste el evento.

    Fecha y hora actual: {datetime.now(ZoneInfo("America/Hermosillo")).strftime('%Y-%m%d %H:%M:%S')} (UTC -07:00, hora local)
"""


class Agent:
    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key)
        self.memory = SimpleMemory(max_messages=MEMORY_MAX_MESSAGES)
        self.tools = Tools()        

    def run(self):
        print("Agent running.")

        while True:
            user_text = input("Tú: ")
            if not user_text:
                continue

            if user_text.lower() in ("salir", "exit", "quit", "q"):
                print("Agent stopped.")
                break

            assistant_text = self.process_response(self.client, self.memory.get_messages(), user_text)
            # tokens_total_usage = resp.usage.total_tokens
            # tokens_input_usage = resp.usage.prompt_tokens
            # tokens_output_usage = resp.usage.completion_tokens
            # assistant_text = msg.content or ""
            print(f"\nAgent: {assistant_text}\n")

            # Actualizar la memoria con el último mensage
            self.memory.add_message("user", user_text)
            self.memory.add_message("assistant", assistant_text)

    def process_response(self, client:Groq, memory_messages:list[dict], user_text:str):
        # Obtener la memoria
        #messages = self.memory.get_messages()
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(memory_messages)
        messages.append(
            {"role": "user", "content": user_text}
        )

        while True:
            resp = self.client.chat.completions.create(
                model="qwen/qwen3-32b",
                messages=messages,
                tools=TOOLS
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
                args = json.loads(tool_call.function.arguments or "{}") # Convertir el json a un diccionario

                if name == "check_availability":
                    result = self.tools.check_availability(
                        time_ini=args["time_ini"],
                        time_end=args["time_end"]
                    )
                elif name == "create_event":
                    result = self.tools.create_event(
                        summary=args["summary"],
                        start=args["start"],
                        end=args["end"],
                        description=args.get("description", "")
                    )
                else:
                    print(f"Se intentó llamar a una herramienta desconocida: {name}")
                    result = {"error": f"Herramienta desconocida: {name}"}
                
                # Agregar a los mensajes el resultado del llamado de la herramienta.
                # Esto lo recibirá el modelo al continuar la iteración
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False)
                })