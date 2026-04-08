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

from backend.config import settings
from langchain_groq import ChatGroq

class CerebrasLLMService:
    def __init__(self):
        # The single source of truth for the LLM engine
        self.model = ChatGroq(
            api_key=settings.groq_api_key.get_secret_value(),
            model="qwen/qwen3-32b", 
            temperature=0.5,
            max_tokens=1024,
            max_retries=3,
            timeout=20
        )

    def invoke(self, messages):
        response = self.model.invoke(messages)
        return response
    

class FastLLMService:
    def __init__(self):
        self.model= ChatGroq(
            api_key= settings.groq_api_key.get_secret_value(),
            model= "llama-3.1-8b-instant",
            temperature= 0.0,
        )
    def invoke(self, messages):
        response= self.model.invoke(messages)
        return response