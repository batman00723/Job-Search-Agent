from myapi.utilities.hybrid_search.retrievalservice import HybridRetrievalRerankService
from myapi.utilities.docs_processing.embedding import EmbeddingService
from myapi.utilities.docs_processing.llm_service import CerebrasLLMService
from myapi.utilities.web_search.websearch import WebSearch
from myapi.utilities.Langgraph.state import AgentState
from types import SimpleNamespace

def retrieve_db_node(state: AgentState):
    query_vector = EmbeddingService.get_embedding(state["query"])

    # This returns a list of OBJECTS 
    raw_chunks = HybridRetrievalRerankService.get_hybrid_reranked_content(
        user=state["user_id"],  
        query=state["query"],
        query_vector=query_vector,
        top_k=5
    )

    # Convert those objects into simple, dictionaries (json serialisable)
    serializable_chunks = []
    source_list = []
    for doc in raw_chunks:
        serializable_chunks.append({
            "page_content": getattr(doc, 'page_content', str(doc)), 
            "metadata": getattr(doc, 'metadata', {})
        })

        name = getattr(doc, 'metadata', {}).get('source', 'Local Doc')
        source_list.append(name)
  
    return {"context": serializable_chunks,
            "sources": list(set(source_list))}



def web_search_node(state: AgentState):
    query = state["query"]
    
    search_results = WebSearch.search_the_web(query=query)
    
    if isinstance(search_results, str): 
        return {"context": [], "sources": ["Web Search Error"], "web_search_done": True}

    urls = [res.get("url") for res in search_results if res.get("url")]
    
    formatted_text = "\n\n".join([
        f"Source: {res.get('url')}\nContent: {res.get('content')}" 
        for res in search_results
    ])
    
    web_chunks = [{
        "page_content": formatted_text, 
        "metadata": {"source": "web_search"}
    }]
    
    print(f"WEB SEARCH SUCCESS: Found {len(urls)} links.")

    return {
        "context": web_chunks, 
        "sources": urls, 
        "web_search_done": True
    }



def generate_node(state: AgentState, llm):
    response = llm.gen_ai_answers(
        user_quey= state["query"],
        context_chunks= state["context"]
    )

    return {"response": response}