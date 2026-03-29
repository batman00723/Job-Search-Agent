from google import genai
from backend.config import settings
from google.genai import types 

class EmbeddingService:

    client= genai.Client(api_key= settings.google_api_key.get_secret_value())
    
    @staticmethod
    def get_embedding(text: str):
        embedding= EmbeddingService.client.models.embed_content(
            model= "gemini-embedding-001",
            contents= text,
            config= types.EmbedContentConfig(
                output_dimensionality= 768
            )
        )

        return embedding.embeddings[0].values
    
    