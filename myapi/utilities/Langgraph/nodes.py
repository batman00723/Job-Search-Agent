from myapi.utilities.hybrid_search.retrievalservice import HybridRetrievalRerankService
from myapi.utilities.docs_processing.embedding import EmbeddingService
from myapi.utilities.web_search.websearch import WebSearch
from myapi.utilities.Langgraph.state import JobAgentState
from langchain_core.messages import SystemMessage, HumanMessage, trim_messages, ToolMessage, AIMessage
from langgraph.graph import END
import asyncio
from crawl4ai import AsyncWebCrawler

trimmer= trim_messages(
    max_tokens= 2000,
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
            "Your task is to rewrite the user's "
            "latest query into a search engine string. "
            "CRITICAL: Look at the chat history to resolve pronouns (e.g., if the user says 'that company', "
            "find the company name in previous messages). "
            "Output ONLY the rewritten search string."
            "If the user changes the topic (e.g., from AI to Accountant), ignore the old topic"
            "and generate a query based ONLY on the new request."
        )
    
    # Combine history with new system prompt 
    # We add user current query at the end
    message_for_llm= [SystemMessage(content=system_prompt)] + message_history
    message_for_llm.append(HumanMessage(content=f"Orignal Query: {raw_query}"))

    optimised_query= llm.invoke(message_for_llm).content

    print(f"Query is reformulated from {raw_query} --> {optimised_query}")

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

    # Run the async search synchronously using a temporary loop
    try:
        # This forces the coroutine to finish and returns the actual list
        search_results = asyncio.run(WebSearch.search_the_web(query=query))
    except Exception as e:
        print(f"Search failed: {e}")
        return {"job_urls": [], "messages": [ToolMessage(content="Search failed", tool_call_id="tavily_Search")]}

    if isinstance(search_results, str): 
        return {"job_urls": [], "sources": ["Web Search Error"]}

    # Now search_results is a real list
    links = [res.get("url") for res in search_results if res.get("url")]

    print(f"WEB SEARCH SUCCESSFULL: Found {len(links)} links.")

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
            print("Sorry! I can't find any suitable Job for you.")
            return END
        


def scrape_job_node(state: JobAgentState):
    urls = state.job_urls[-5:]
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


    if state.critique and "PASSED" not in state.critique.upper():
        critique_instruction = (
            "\n\nIMPORTANT: Your previous analysis was REJECTED. "
            f"Fix these specific issues in your revised report: {state.critique}"
        )
    else:
        critique_instruction= ""

    for job_text in state.scraped_content:
        if len(job_text) < 200:
            continue
        # trimming text as to be within llm token limits
        trimmed_job = job_text[:5000] 

        system_prompt = (
            "You are a blunt, Technical Recruiter. Analyze the Resume against the Job. "
            "Your response MUST be in this EXACT format:\n\n"
            "COMPANY: [Company Name]\n"
            "ROLE: [Job Title]\n"
            "LINK: [Paste the Link Provided]\n"
            "SCORE: [0-100]\n"
            "GAP: [Reason for rejection]\n"
            "EDGE: [Why you are a top 1% candidate or bad candidate]\n"
            "Do NOT give 'pity points' for general intelligence or 'analytical skills'" 
            "unless they are specifically requested in the JD."
            "Be blunt. If the candidate is a waste of the hiring manager's time, say so."
            f"{critique_instruction}"
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

    system_prompt = (
    "You are a routing gatekeeper. Analyze the user's intent.\n"
    "CLASSIFICATION RULES:\n"
    "1. Return 'chat' if the user asks for ADVICE, OPINIONS, or evaluation of their potential "
    "(e.g., 'Can I excel...', 'What do you think of my skills...', 'Is this a good career?').\n"
    "2. Return 'chat' if the user refers to existing results or history.\n"
    "3. ONLY return 'search' if the user is explicitly asking to find NEW job listings "
    "or internships (e.g., 'Find me...', 'Search for...', 'Look for jobs in...').\n"
    "Output ONLY 'chat' or 'search'."
    )

  
    
    classification = llm.invoke([
        ("system", system_prompt),
        ("user", state.query)
    ]).content.lower().strip()
    
    # default is search if unsure
    action = "chat" if "chat" in classification else "search"   
    
    if action == "search":
        # By returning an empty list for match_reports here, 
        # you are telling the graph to start fresh for this specific branch.
        return {
            "next_action": "search",
            "match_reports": []      # This "Flushes" the old reports 
        }

    return {"next_action": action}

def chat_node(state: JobAgentState, llm):
    """
    Discusses existing results without re-scraping.
    """
    reports = "\n\n".join([r['report'] for r in state.match_reports])
    
    system_prompt = (
        "You are an Career Coach. You have already found several jobs for the user. "
        "Use the provided reports to answer the user's specific feedback or questions. "
        "If the user says the jobs are 'shit', acknowledge it, explain why they were picked, "
        "and ask what they'd prefer to see instead."
    )
    
    user_prompt = f"Context: {reports}\n\nQuestion: {state.query}"
    
    response = llm.invoke([
        ("system", system_prompt),
        ("user", user_prompt)
    ])

    return {"messages": [response]}



def reflection_node(state: JobAgentState, llm):
    """Acts as a critique to ensure the match report generated by LLM is accurate and honest."""

    if state.revision_count >=1:
        return {
            "critique": "PASSED", # force exit
            "revision_count": state.revision_count + 1
        }

    resume_query= "Detailed professional experience, technical skills,and projects"
    query_vector= EmbeddingService.get_embedding(resume_query)

    resume_context_list= HybridRetrievalRerankService.get_hybrid_reranked_content(
        user= state.user_id,
        query= resume_query,
        query_vector=query_vector,
        top_k= 5
    )

    resume_context = "\n---\n".join(resume_context_list)

    prompt= f"""
    You are a Senior Hiring Manager. Review this Job match report agaisnt the User's Resume.
    RESUME: {resume_context}
    MATCH REPORT: {state.match_reports}
    CRITERIA:
        1. Is the score honest? (e.g., don't give a 90% if they lack a core tech).
        2. Are there hallucinations? (Did the analyst lie about skills?).
        3. Is the advice specific or just generic HR fluff?

        If it's perfect, respond ONLY with the word 'PASSED'.
        If it's bad, provide a short, blunt prompt list of what the Analyst needs to fix.
        """
    
    response= llm.invoke(prompt).content

    return{
        "critique": response,
        "revision_count": state.revision_count + 1
    }


def should_continue(state: JobAgentState):
    # chekcing if reflection node passed it or we have hit our 2 attempts lmit
    if "PASSED" in state.critique.upper() or state.revision_count >= 1:
        return "end"
    
    # Otherwise loop back
    return "revise"
