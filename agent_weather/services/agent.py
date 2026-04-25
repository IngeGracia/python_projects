import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from groq import Groq
from dotenv import load_dotenv
from core.simple_memory import SimpleMemory
from services.tools import Tools


env_path = os.path.join(os.path.dirname(
    os.path.dirname(__file__)), "core", ".env")
load_dotenv(env_path)
MEMORY_MAX_MESSAGES = 10
TOOLS = [
    {
        "type": "function",
                "function": {
                    "name": "obtener_clima_api",
                    "description": (
                        "Llama a esta función para obtener el clima actual de cualquier lugar. "
                        "Se debe enviar como argumento la Latitud y Longitud de la ciudad de la que deseas obtener el clima."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "latitude": {
                                "type": "string",
                                "description": "La Latitud de la ciudad de la cual se desea obtener el clima."
                            },
                            "longitude": {
                                "type": "string",
                                "description": "La Longitud de la ciudad de la cual se desea obtener el clima."
                            }
                        },
                        "required": ["latitude", "longitude"]
                    }
                }
    },
    {
        "type": "function",
                "function": {
                    "name": "obtener_lat_long",
                    "description": (
                        "Llama a esta función para obtener la Latitud y Longitud de cualquier ciudad. "
                        "Se debe enviar como argumento el nombre de la ciudad de la que deseas obtener el clima."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ciudad": {
                                "type": "string",
                                "description": "El nombre de la ciudad de la cual se desea obtener el clima."
                            }
                        },
                        "required": ["ciudad"]
                    }
                }
    },
    {
        "type": "function",
                "function": {
                    "name": "currency_conversion",
                    "description": (
                        "Llama a esta función para obtener la conversión de monedas de cualquier moneda a cualquier otra moneda. "
                        "Se debe enviar como argumento la moneda de origen (from_currency), la moneda de destino (to_currency) y la cantidad a convertir (amount)."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "from_currency": {
                                "type": "string",
                                "description": "La moneda de origen de la cual se desea obtener la conversión."
                            },
                            "to_currency": {
                                "type": "string",
                                "description": "La moneda de destino de la cual se desea obtener la conversión."
                            },
                            "amount": {
                                "type": "number",
                                "description": "La cantidad de la moneda de origen que se desea convertir."
                            }
                        },
                        "required": ["from_currency", "to_currency", "amount"]
                    }
                }
    }
]
SYSTEM_PROMPT = f"""
    Eres un asistente que habla español y recibe de una manera breve y concisa en español latino (México).

    Herramientas:
        - Cuentas con una herramienta llamada obtener_clima_api la cual te proporciona el clima en cualquier ciudad.
            Requiere indicarle una Latitud y Longitud.
        - Cuentas con un aherramienta llamada obtener_lat_long la cual te proporciona la Latitud y Longitud de cualquier ciudad.
            Requiere indicarle una Ciudad.

        - Cuentas con una herramienta llamada currency_conversion la cual te hace una conversión de monedas.
            Requiere indicarle una moneda de origen (from_currency), una moneda de destino (to_currency) y la cantidad a convertir (amount).
            Si el usuario no indica alguna de las monedas, debes asegurarte de solicitarlas.
            Si las monedas son iguales, no debes hacer la conversión e indicarle al usuario el motivo.
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
                # Convertir el json a un diccionario
                args = json.loads(tool_call.function.arguments or "{}")

                if name == "obtener_clima_api":
                    result = self.tools.obtener_clima_api(
                        latitude=args["latitude"],
                        longitude=args["longitude"]
                    )
                elif name == "obtener_lat_long":
                    result = self.tools.obtener_lat_long(
                        ciudad=args["ciudad"]
                    )
                elif name == "currency_conversion":
                    result = self.tools.currency_conversion(
                        from_currency=args["from_currency"],
                        to_currency=args["to_currency"],
                        amount=args["amount"]
                    )
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
