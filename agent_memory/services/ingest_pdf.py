import os, sys
from pypdf import PdfReader
from core.gemini_embedder import GeminiEmbedder
from dotenv import load_dotenv


def main():
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None
    if not pdf_path or not os.path.exists(pdf_path):
        print("Por favor, proporciona la ruta del PDF.")
        return

    pages = extract_pdf_text(pdf_path)
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), "core", ".env"))
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    embedder = GeminiEmbedder(api_key=GEMINI_API_KEY)

    for page in pages:
        chunks = chunk_text(page["text"])
        print(chunks)
        
        # Generar embeddings por cada sección (Chunk)
        for chunk in chunks:
            vectors = embedder.embed_document(chunk)
            print(vectors)

    
def extract_pdf_text(path:str):
    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append({"page": i, "text": text})
    return pages


def chunk_text(text:str, size:int = 500, overlap:int = 100):
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks

 
if __name__ == "__main__":
    main()