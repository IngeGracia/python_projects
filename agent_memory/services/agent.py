import os, json
from datetime import datetime
from zoneinfo import ZoneInfo
from groq import Groq
from dotenv import load_dotenv
from core.simple_memory import SimpleMemory
from core.long_term_memory import LongTermMemory
from services.tools import Tools


# env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core", ".env")
# load_dotenv(env_path)


class Agent:
    def __init__(self):
        self.__env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core", ".env")
        load_dotenv(self.__env_path)
        MEMORY_MAX_MESSAGES = 10
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "guardar_memoria_largo_plazo",
                    "description": (
                        "Utiliza esta herramienta cuando el usuario haya dicho algo importante que consideres que se deba almacenar como memoria de largo plazo."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "memory": {
                                "type": "string",
                                "description": "La memoria que se desea almacenar."
                            }
                        },
                        "required": ["memory"]
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
            Eres un asistente de IA amigable que habla español y de manera concisa.
            
            # REGLAS
            - Por cada mensaje que envía el usuario, debes evaluar si tiene información importante o personal (preferencias, hábitos, objetivos, eventos importantes, gustos, pasatiempos, cosas favoritas, fechas. 
                De ser así, utiliza la herramienta llamada **Guardar memoria de largo plazo** para guardar dicha información en memoria de largo plazo.
            - Debes responder al usuario de manera natural y amigable. 
                Aunque guardes información, tu respuesta no debe indicar dicha acción.
            - Utiliza memorias almacenadas para dar respuestas personalizadas y con contexto relevante.
            - Considera la fecha y hora de las memorias obtenidas. 
                Tus respuestas deben ser actualizadas.
            - Redacta tus respuestas según preferencias del usuario e interacciones anteriores.
            - Nunca almacenes información sensible como nombres de usuario, contraseñas, tarjetas de crédito o información de pagos.


            # HERRAMIENTAS
            ## guardar_memoria_largo_plazo
            - Utiliza esta herramienta para almacenar información importante del usuario que debas mantener para futuras interacciones en memoria de largo plazo.


            # MEMORIAS
            ## Memorias importantes recientes
            - A continuación aparece una lista de las memorias almacenadas (puede estar vacía si no has interactuado con el usuario).
                == INICIO DE MEMORIAS
                {memories_text}
                == FIN DE MEMORIAS

            ## Guía para uso de memorias:
            - Prioriza los mensajes recientes.
            - Referencía las memorias entre ellas para mantener consistencia en tus respuestas.
                Por ejemplo, si el usuario comparte preferencias que hacen conflico con el tiempo clarifica o adáptate.
        """


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
                args = json.loads(tool_call.function.arguments or "{}") # Convertir el json a un diccionario

                if name == "guardar_memoria_largo_plazo":
                    self.ltm.insert_long_term_memory(
                        id_user="bunbury",
                        memory=args.get("memory", "")
                    )
                    result = "Memoria almacenada correctamente."
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