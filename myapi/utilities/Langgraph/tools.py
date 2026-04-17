from ninja import Schema
from pydantic import Field
from langchain_core.tools import tool

from myapi.utilities.hybrid_search.retrievalservice import HybridRetrievalRerankService
from myapi.utilities.docs_processing.embedding import EmbeddingService
from myapi.utilities.web_search.websearch import WebSearch

class SearchSchema(Schema):
    query: str= Field(description= "The reformulated standalone search query")
    user_id: int = Field(description= "The numeric ID of user for document security")


@tool(args_schema=SearchSchema)
def retrieve_document(query: str, user_id: int):
    """Search and retrieve relevant documents from the local database."""

    raw_chunks = HybridRetrievalRerankService.get_hybrid_reranked_content(
        user=user_id,
        query=query,
        query_vector=EmbeddingService.get_embedding(query),
        top_k=5
    )
    
    clean_strings = []
    for doc in raw_chunks:
        text = getattr(doc, 'chunk', "")
        if text:
            clean_strings.append(text)
    if not clean_strings:
        return "No personal data found."
        
    return "\n\n".join(clean_strings)



@tool(args_schema= SearchSchema)
def web_search(query: str, user_id: int):
    """
    Search the live internet for real-time information, news, and 
    general knowledge that is not present in the local private documents. 
    Use this for current events or widely available facts.
    """
    search_results= WebSearch.search_the_web(query= query)

    # isinstance is for error handling as if we get search results as strs then return this
    if isinstance(search_results, str):
        return {"context": [], "sources": ["Web Search Error"], "web_search_done": True}
    
    urls= [res.get("url") for res in search_results if res.get("url")]

    web_chunks= [
        {
            "page_content": res.get("content", ''),
            "metadata": {"source": res.get('url', 'web')}
        } for res in search_results
    ]

    return {
        "context": web_chunks,
        "sources": urls,
        "web_search_done": True
    }

agent_tools = [retrieve_document, web_search]