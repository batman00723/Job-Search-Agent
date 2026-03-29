# Here we will make seperate logic file for chathistory to clean bloatware of doc_conroller.py and it become plug and play.

from myapi.models import ChatHistory
from django.db import transaction


class ChatHistoryManager:
    @staticmethod
    def get_session_history_slicing_window(user, session_id: str, window_size: int= 6):
        history_qs= ChatHistory.objects.filter(
            user= user,
            session_id= session_id
        ).order_by('-created_at')[:window_size]

        return list(reversed(history_qs))
    
    @staticmethod
    def add_to_history_db(user, session_id, human_query, ai_response):
        with transaction.atomic():
            ChatHistory.objects.create(
                user= user,
                session_id= session_id,
                message_by= "human",
                content= human_query
            )
            ChatHistory.objects.create(
                user= user,
                session_id= session_id,
                message_by= "ai",
                content= ai_response
            )