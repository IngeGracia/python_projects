from google import genai
from google.genai import types


class GeminiEmbedder:
    # dims - Varía por cada modelo de embedding. Indica cuántas dimensiones tendrá el vector para cada embedding.
    #   Básicamente al pasarle un vector, devolverá un Chunk con 3072 dimensiones (Números separados por coma) para capturar sus ginificado de manera numérica.
    def __init__(self, api_key:str, model:str="models/gemini-embedding-001", dims:int=3072):
        self.model = model
        self.dims = dims
        self.client = genai.Client(api_key=api_key)

    # crear embeddings de una sección del texto
    def embed_document(self, text:str):
        res = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=types.EmbedContentConfig(
                task_type="retrieval_document",
                output_dimensionality=self.dims
            )
        )
        # índice 0, ya que estamos solamente generando embeddings de 1 documento
        return list(res.embeddings[0].values)