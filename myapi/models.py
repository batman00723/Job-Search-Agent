from django.db import models
from django.contrib.auth.models import User
from myapi.utilities.validators.file_size_validation import validate_file_size

from pgvector.django import VectorField, HnswIndex

from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex


class Document(models.Model):
    user= models.ForeignKey(User, on_delete= models.CASCADE)
    doc_name= models.CharField(max_length=100, validators= [validate_file_size])
    document= models.FileField(upload_to= "documents/")
    file_type= models.CharField(max_length=10)
    uploaded_at= models.DateTimeField(auto_now_add= True)
    status= models.CharField()
    is_deleted= models.BooleanField(default= False)
    raw_content= models.TextField(null= True, blank= True)

    def __str__(self):
        return self.doc_name

class DocumentChunk(models.Model):
    document= models.ForeignKey(Document, on_delete= models.CASCADE, related_name= "chunks")
    chunk= models.TextField()
    chunk_index= models.IntegerField()
    embedding= VectorField(dimensions= 768, null= True, blank= True)
    page_number= models.IntegerField(null= True, blank= True)

    search_vector= SearchVectorField(null= True)

    class Meta:
        indexes= [
            HnswIndex(
                name= 'document_hnsw_idx',
                fields= ['embedding'],
                m= 16,
                ef_construction= 64,
                opclasses= ['vector_cosine_ops']   
            ),

            GinIndex(fields=['search_vector'])
        ]


class SemanticCache(models.Model):
    user= models.ForeignKey(User, on_delete=models.CASCADE)
    query_text= models.TextField()
    query_embedding= VectorField(dimensions= 768)
    llm_response= models.TextField()
    created_at= models.DateTimeField(auto_now_add= True)

    class Meta:
        indexes= [HnswIndex(name= 'chunk_vector_idx',
                            fields= ['query_embedding'],
                            opclasses= ['vector_cosine_ops']
                        )
                    ]

class ChatHistory(models.Model):
    user= models.ForeignKey(User, on_delete= models.CASCADE)
    session_id= models.CharField(max_length= 255, db_index= True)
    message_by= models.CharField(max_length= 10) # human or ai
    content= models.TextField()
    created_at= models.DateTimeField(auto_now_add= True)

    class Meta: indexes = [models.Index(fields=['user', 'session_id', 'created_at']),]