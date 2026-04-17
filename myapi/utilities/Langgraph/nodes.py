from myapi.utilities.hybrid_search.retrievalservice import HybridRetrievalRerankService
from myapi.utilities.docs_processing.embedding import EmbeddingService
from myapi.utilities.web_search.websearch import WebSearch
from myapi.utilities.Langgraph.state import JobAgentState
from langchain_core.messages import SystemMessage, HumanMessage, trim_messages, ToolMessage, AIMessage
from langgraph.graph import END
import asyncio
from crawl4ai import AsyncWebCrawler

trimmer= trim_messages(
    max_tokens=500,
    strategy="last",
    token_counter=len,
    include_system=True,
    start_on="human",
)


def rewrite_query_node(state: JobAgentState, llm):
    message_history= trimmer.invoke(state.messages)
    raw_query= state.query

    print(f"Past Messages Count: {len(message_history)}")

    if not message_history:
        return {"query": raw_query }
    

    system_prompt = (
            "You are an expert recruitment researcher. Your task is to rewrite the user's "
            "latest query into a search engine string. "
            "CRITICAL: Look at the chat history to resolve pronouns (e.g., if the user says 'that company', "
            "find the company name in previous messages). "
            "Output ONLY the rewritten search string."
        )
    
    # Combine history with new system prompt 
    # We add user current query at the end
    message_for_llm= [SystemMessage(content=system_prompt)] + message_history
    message_for_llm.append(HumanMessage(content=f"Orignal Query: {raw_query}"))

    # We use ainvoke for await it is async version of invoke
    optimised_query= llm.invoke(message_for_llm).content

    # From return state will be updated
    return {
        "query": optimised_query,
        "messages": [HumanMessage(content= f"Refined search to: {optimised_query}")]
    }




import asyncio

def search_node(state: JobAgentState):
    """Takes optimised query and finds job links on the web"""
    query = state.query
    
    print(f"Searching for: {query}")

    # FIX: Run the async search synchronously using a temporary loop
    try:
        # This forces the coroutine to finish and returns the actual list
        search_results = asyncio.run(WebSearch.search_the_web(query=query))
    except Exception as e:
        print(f"Search failed: {e}")
        return {"job_urls": [], "messages": [ToolMessage(content="Search failed", tool_call_id="tavily_Search")]}

    if isinstance(search_results, str): 
        return {"job_urls": [], "sources": ["Web Search Error"]}

    # Now search_results is a real LIST
    links = [res.get("url") for res in search_results if res.get("url")]

    print(f"WEB SEARCH SUCCESS: Found {len(links)} links.")

    result_message = ToolMessage(
        content=f"Found {len(links)} potential job links.",
        tool_call_id="tavily_Search"
    )

    return {
        "job_urls": links, 
        "messages": [result_message],
        "retry_count": state.retry_count + 1,
    }



def router(state: JobAgentState):
    """
    Looks at 'job_urls' and decide: Scrape. Retry, or Give Up.
    """
    # If links found then move to scrape node this is not necessary but better to be explicit.
    if state.job_urls and len(state.job_urls) > 0:
        print(f"Routing: Found {len(state.job_urls)} links. Next Step- Scraping")
        return "scrape_job_node"
    
    # If links not found going back to rewrite query node
    if not state.job_urls:
        if state.retry_count < 3:
            print(f"No links found. Retying attempt {state.retry_count + 1}/3")
            return "rewrite_query_node"
        else:
            print("Sorry! But ig you'll remain unemployed for now, cus we can't even find a shit for you.")
            return END
        


def scrape_job_node(state: JobAgentState):
    urls = state.job_urls[:5]
    if not urls:
        return {"messages": ["No URLs to scrape."]}

    print(f"Scraping {len(urls)} links...")

    async def run_crawl():
        async with AsyncWebCrawler() as crawler:
            results = await crawler.arun_many(urls=urls)
            return [res.markdown for res in results if res.success]


    scraped_texts = asyncio.run(run_crawl())

    return {
        "scraped_content": scraped_texts,
        "messages": [f"Successfully scraped {len(scraped_texts)} jobs."]
    }
    

def analyse_jobs_node(state: JobAgentState, llm):
    """
    Compares scraped job descriptions against the resume stored in database.
    """
    resume_query= "Detailed professional experience, technical skills,and projects"
    query_vector= EmbeddingService.get_embedding(resume_query)

    resume_context_list= HybridRetrievalRerankService.get_hybrid_reranked_content(
        user= state.user_id,
        query= resume_query,
        query_vector=query_vector,
        top_k= 5
    )

    resume_context = "\n---\n".join(resume_context_list)

    analysis_report = []

    for job_text in state.scraped_content:
        # trimming text as to be within llm token limits
        trimmed_job = job_text[:5000] 

        system_prompt = (
            "You are a blunt, elite Technical Recruiter. Analyze the Resume against the Job. "
            "Your response MUST be in this EXACT format:\n\n"
            "COMPANY: [Company Name]\n"
            "ROLE: [Job Title]\n"
            "LINK: [Paste the Link Provided]\n"
            "SCORE: [0-100]\n"
            "GAP: [Blunt reason for rejection]\n"
            "EDGE: [Why you are a top 1% candidate]\n"
        )

        user_prompt = f"RESUME CONTEXT: \n{resume_context}\n\nJOB DESCRIPTION:\n{trimmed_job}"
        
        try:
            response = llm.invoke([
                ("system", system_prompt),
                ("user", user_prompt)
            ]).content
            analysis_report.append(response)
        except Exception as e:
            print(f"LLM Error on job: {e}")
            continue # skip failed jobs and move to next

    return {
        "match_reports": [{"report": r} for r in analysis_report],
        "messages": [AIMessage(content=f"Completed analysis of {len(analysis_report)} jobs.")]
    }





def intent_classifier_node(state: JobAgentState, llm):
    """
    Determines if the user wants a NEW search or a FOLLOW-UP conversation.
    """
    reports= getattr(state, "match_reports", [])
    # If we have no reports yet, we MUST search
    if not reports:
        return {"next_action": "search"}

    system_prompt = (
        "You are a routing gatekeeper. Analyze the user's message. "
        "CRITICAL RULES:\n"
        "1. If the user is expressing an opinion ('these are bad jobs'), asking a follow-up "
        "('tell me more'), or seeking advice ('which should I pick?'), return 'chat'.\n"
        "2. Only return 'search' if the user provides a NEW job title or a NEW location "
        "to search for (e.g., 'Find me Backend roles' or 'Search in Bangalore').\n"
        "Output ONLY 'chat' or 'search'."
    )
    
    classification = llm.invoke([
        ("system", system_prompt),
        ("user", state.query)
    ]).content.lower().strip()

    # Default to search if unsure
    action = "chat" if "chat" in classification else "search"
    return {"next_action": action}

def chat_node(state: JobAgentState, llm):
    """
    Discusses existing results without re-scraping.
    """
    reports = "\n\n".join([r['report'] for r in state.match_reports])
    
    system_prompt = (
        "You are an elite, blunt Career Coach. You have already found several jobs for the user. "
        "Use the provided reports to answer the user's specific feedback or questions. "
        "If the user says the jobs are 'shit', acknowledge it, explain why they were picked, "
        "and ask what they'd prefer to see instead. Don't just repeat the reports."
    )
    
    user_prompt = f"Context: {reports}\n\nQuestion: {state.query}"
    
    response = llm.invoke([
        ("system", system_prompt),
        ("user", user_prompt)
    ])

    return {"messages": [response]}