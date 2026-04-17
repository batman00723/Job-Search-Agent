from backend.config import settings
from langchain_cerebras import ChatCerebras

class FastLLMService:
    def __init__(self):
        self.model= ChatCerebras(
            api_key= settings.cerebras_api_key.get_secret_value(),
            model= "llama3.1-8b",
            temperature= 0.0,
            max_tokens= 1024
        )
    def invoke(self, messages):
        response= self.model.invoke(messages)
        return response