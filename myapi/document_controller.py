from ninja_extra import ControllerBase, api_controller, http_post, http_get
from ninja_jwt.authentication import JWTAuth
from .schemas import DocumentIn, DocumentOut
from .models import Document
from django.db import transaction
from myapi.utilities.validators.file_type_validator import detect_file_type
from ninja import File, UploadedFile, Form
from myapi.background_tasks.background_tasks import document_processing, send_llm_response_email
from django.shortcuts import get_object_or_404

from myapi.utilities.docs_processing.embedding import EmbeddingService
from myapi.utilities.docs_processing.llm_service import FastLLMService
from myapi.utilities.session_manager.session_manager import provide_session_id
from myapi.utilities.chat_history.chat_history import ChatHistoryManager
from myapi.utilities.hybrid_search.retrievalservice import HybridRetrievalRerankService
from backend.config import settings
from myapi.utilities.Langgraph.graph import create_agent


@api_controller("/documents", tags= ['docs'], auth= JWTAuth())
class DocumentOperationController(ControllerBase):
    def __init__(self):
        self.llm_service= FastLLMService()
        self.job_agent= create_agent(self.llm_service.model)  



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
    

    @http_get("/ask_agent")
    def ask_agent(self, request, query: str): 

        print(">>> ask_agent called") 

        session_id= "aman-session-00"
        
        config= {"configurable": {"thread_id": session_id}}
        
        initial_state= {
            "query": query,
            "job_urls": [],
            "scraped_content": [],
            "retry_count": 0,
            "user_id": request.user.id
        }

        try:
            final_state= self.job_agent.invoke(initial_state, config= config)
            report= final_state.get("match_reports", [])
            last_message= final_state.get("messages")[-1].content if final_state.get("messages") else ""

            send_llm_response_email(settings.email_host_user,
                                    question= query,
                                    answer= report)

            return{
                "status": "Success",
                "answer": last_message,
                "job_report": report
            }
                            
        except Exception as e:
            import logging
            logger= logging.getLogger(__name__)
            logger.error(f"Agent Execution Error: {str(e)}", exc_info= True)

            return {
                "status": "Error",
                "message": "There is a problem while running Job Agent",
                "details": str(e) if settings.debug else "Internal Server Error"
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