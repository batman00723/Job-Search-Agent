from google import genai
from google.genai import types
from backend.config import settings

class GeminiLLMService:
    def __init__(self):
        self.client= genai.Client(api_key= settings.google_api_key.get_secret_value())
        self.model_id= settings.main_model_name

    def gen_ai_answers(self, user_quey, context_chunks, chat_history= None):
        context_text= "\n\n".join([chunk.chunk for chunk in context_chunks])  # in chunk.chunk 2nd chunk is from model.

        system_prompt= (
            "Use the given context to answer the question." \
            "If information not in Context say Sorry I don't have enough information." \
            "Speak Humanly as possible."
        )

        content= []
        if chat_history:
            for msg in chat_history:
                role= "user" if msg.message_by == "human" else "model"   # these names user and model must be exact gemini understandds this only.
                content.append(types.Content(role= "user", parts= [types.Part.from_text(text= msg.content)]))
        
        

        user_prompt= f"Context: \n{context_text}\n\nQuestion: {user_quey}"
        content.append(types.Content(role="user", parts= [types.Part.from_text(text= user_prompt)]))

        # first we appended chat_chitory in content and now we appended recent user query to it too.

        config= types.GenerateContentConfig(
            system_instruction= system_prompt,
            temperature= 0.6,
            max_output_tokens= 600,
            thinking_config= types.ThinkingConfig(include_thoughts= True, thinking_level= "medium")
            )

        response= self.client.models.generate_content(
            model=self.model_id,
            contents= content,  # content= (history + recent query)
            config= config
        )

        return response.text
    
# using cerebras because gemini can sometimes stop giving access to free models due to usage spike.

from cerebras.cloud.sdk import Cerebras
from backend.config import settings

class CerebrasLLMService:
    def __init__(self):
        # 1. Ensure 'cerebras_api_key' is added to your config.py/Settings class
        # 2. Ensure 'CEREBRAS_API_KEY' is in your .env file
        self.client = Cerebras(api_key=settings.cerebras_api_key.get_secret_value())
        self.model_id = "qwen-3-235b-a22b-instruct-2507"

    def gen_ai_answers(self, user_quey, context_chunks, chat_history=None):
        # Join chunks exactly as you did before
        context_text = "\n\n".join([
        chunk.get('page_content', '') for chunk in context_chunks
    ])


        system_prompt = (
        "You are a helpful assistant. You MUST answer ONLY using the provided context. "
        "Do NOT use your training data or prior knowledge under any circumstances. "
        "If the context does not contain the answer, say 'Sorry, I don't have enough information.' "
        "Never mention a knowledge cutoff date."
         )

        # Build the messages list
        messages = [{"role": "system", "content": system_prompt}]

        # Add History: Convert "model" to "assistant" for cerebras to understand
        if chat_history:
            for msg in chat_history:
                role = "user" if msg.message_by == "human" else "assistant"
                messages.append({"role": role, "content": msg.content})

        # recent user query + context
        user_prompt = f"Context: \n{context_text}\n\nQuestion: {user_quey}"
        messages.append({"role": "user", "content": user_prompt})

        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
            temperature=0.6,
            max_completion_tokens=600
        )
        return response.choices[0].message.content