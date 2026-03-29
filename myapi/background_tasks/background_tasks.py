from celery import shared_task
from myapi.models import Document, DocumentChunk
from myapi.utilities.docs_processing.ragpipeline import RagPipeline
from myapi.utilities.docs_processing.docs_parsing import extract_content

from django.contrib.postgres.search import SearchVector

@shared_task
def document_processing(doc_id):
    try:
        document= Document.objects.get(id= doc_id)

        text= extract_content(document.document.path, document.file_type)

        if text:
            document.raw_content= text
            document.save()

            pipeline= RagPipeline()

            chunk_count= pipeline.process_document(document, text)

            DocumentChunk.objects.filter(document_id= doc_id).update(
                search_vector= SearchVector('chunk')
            )

            document.status= "COMPLETED"
            document.save()



        else:
            document.status= "FAILED"
            return f"Can't process document of doc_id {doc_id}"
        
        
    except Document.DoesNotExist:
        return f"Document of doc_id {doc_id} is not found"


from django.core.mail import send_mail
from backend.config import settings
           
@shared_task
def send_llm_response_email(user_email, question, answer):
    subject= f"AI Response: {question[:30]}...."
    message= f"You asked: {question}\n\nAI Answer: {answer}"

    send_mail(
        subject= subject,
        message= message,
        from_email= settings.email_host,
        recipient_list= ["amanmishrarewa23@gmail.com"],
        fail_silently= False
    )