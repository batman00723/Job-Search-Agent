from ninja_extra import ControllerBase, api_controller, http_post, http_get, http_patch, http_delete
from ninja_jwt.authentication import JWTAuth
from .schemas import DocumentIn, DocumentOut
from .models import Document
from django.db import transaction
from myapi.utilities.validators.file_type_validator import detect_file_type
from ninja import File, UploadedFile, Form
from myapi.background_tasks.background_tasks import document_processing, send_llm_response_email
from django.shortcuts import get_object_or_404

from myapi.utilities.docs_processing.embedding import EmbeddingService
from myapi.utilities.docs_processing.llm_service import CerebrasLLMService
from myapi.utilities.session_manager.session_manager import provide_session_id
from myapi.utilities.chat_history.chat_history import ChatHistoryManager
from myapi.utilities.hybrid_search.retrievalservice import HybridRetrievalRerankService
from backend.config import settings

from myapi.utilities.Langgraph.graph import create_rag_agent


@api_controller("/documents", tags= ['docs'], auth= JWTAuth())
class DocumentOperationController(ControllerBase):
    def __init__(self):
        self.llm= CerebrasLLMService()

        self.rag_agent= create_rag_agent(self.llm)


    @http_post("/", response= DocumentOut)
    def upload_docs(self, request, data: Form[DocumentIn], docs: File[UploadedFile]):
        
        file_type= detect_file_type(docs)
        
        with transaction.atomic():
            payload= data.model_dump()

            document= Document.objects.create(user= request.user,
                                              status= "PROCESSING",
                                              document= docs,
                                              file_type= file_type,
                                              **payload)
            
            document_processing.delay(document.id)
            
        return document

    @http_get("/status")
    def document_processing_status(self, request, doc_id: int):
        document= Document.objects.get(id= doc_id, user= request.user)
        return {
            "doc_id": document.id,
            "doc_name": document.doc_name,
            "status": document.status
        }
    
    @http_get("/ask")
    @provide_session_id
    def ask_docs_hyb_chat_hist(self, request, query: str):
        
        session_id = request.generated_session_id

        chat_history= ChatHistoryManager.get_session_history_slicing_window(user= request.user,
                                                              session_id=session_id)

        query_vector= EmbeddingService.get_embedding(query)

        context_chunks= HybridRetrievalRerankService.get_hybrid_reranked_content(
            user= request.user,
            query= query,
            query_vector= query_vector
        )

        
        ai_response= self.llm.gen_ai_answers(query, context_chunks, chat_history= chat_history)

        ChatHistoryManager.add_to_history_db(user= request.user, session_id= session_id, 
                                             human_query= query, ai_response= ai_response)
        
        send_llm_response_email(settings.email_host_user,
                                question= query,
                                answer= ai_response)
            
        return{
            "query": query,
            "response": ai_response
        }
    
    @http_get("/ask_agent")
    def ask_agent(self, request, query: str): # rn we are using this input for session id as we dont ahve frontend to catch that session id and hold it so once 
                                                                            # session id i screated we wil copy it from resopnse and paste it if querying 2nd time so that we can maintain memory saver feature.
        
        session_id= "aman-session-123"
        config= {"configurable": {"thread_id": session_id}}
        
        # we remove chathistory from here now memory saver will automatically inject older chtas to graph from session_id
        initial_state= {
            "query": query,
            "context": [],
            "response": "",
            "sources": [],
            "web_search_done": False,
            "user_id": request.user.id
        }

        final_state= self.rag_agent.invoke(initial_state, config=config)

        # for fetching out all sources websites used 
        all_sources = list(set(final_state.get("sources", [])))

        ai_response= final_state["response"]

        return {
            "query": query,
            "response": ai_response,
            "session_id": session_id,
            "sources": all_sources
        }



    
    @http_get("/", response=list[DocumentOut])
    def list_documents(self, request):
        user = request.user

        if user.is_superuser:
            return Document.objects.filter(is_deleted=False)

        return Document.objects.filter(user=request.user, is_deleted=False)       
    
    @http_get("/{doc_id}", response= DocumentOut)
    def get_my_doc(self, request, doc_id: int):
        document= get_object_or_404(Document, user= request.user, id= doc_id, is_deleted= False)
        return document