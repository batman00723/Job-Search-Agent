from google import genai
from google.genai import types
from backend.config import settings

class QueryRewriter:
    def __init__(self):
        self.client= genai.Client(api_key= settings.google_api_key.get_secret_value())
        self.model_id= settings.main_model_name

        def get_standaone_query(self, user_query, chat_history):
            """
            Rewrite conversational query to be self-contained for hybrid search.

            """

            if not chat_history:
                return user_query
            
            history_context= ""
            for msg in chat_history[-3:]:
                role= "User" if msg.message_by == "human" else "model"
                history_context += f"{role}: {msg.content}\n"

                