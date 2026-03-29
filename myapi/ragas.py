import os
import django
from langchain_core.documents import Document as LangchainDocument
from ragas.testset import TestsetGenerator
from ragas.llms import LangchainLLMWrapper
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from myapi.models import DocumentChunk
from backend.config import settings

def generate_automated_testset():
  
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
    generator_llm = LangchainLLMWrapper(llm)
    
    embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
    
    db_chunks = DocumentChunk.objects.all()[:20]
    
    langchain_docs = [
        LangchainDocument(page_content=c.chunk, metadata={"source": str(c.document.id)}) 
        for c in db_chunks
    ]

    generator = TestsetGenerator.from_langchain(
        generator_llm=generator_llm,
        critic_llm=generator_llm, 
        embeddings=embeddings
    )

    testset = generator.generate_with_langchain_docs(langchain_docs, testset_size=5)

    df = testset.to_pandas()
    df.to_json("test_set.json", orient="records", indent=4)
    print("Successfully generated test_set.json!")

if __name__ == "__main__":
    generate_automated_testset()