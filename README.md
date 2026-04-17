# Job-Search-Agent 

Tired of manually checking jobs? I built Job-Search-Agent. It’s an AI system that finds job links, scrapes and analyses them. It uses a Hybrid RAG pipeline to validate each job against your resume, so you only apply to job that matters.

---

## System Architecture

<p align="center">
  <img src="job agent.png" width="600" title="System Architecture">
</p>

The system operates in a stateful manner:
1.  **Intent Classifier:** Analyses the query to decide between a search or a follow-up conversation ("search" or "chat").
2.  **Rewrite Node:** Resolves pronouns from chat history and optimises search query.
3.  **Search & Scrape:** Executes live web searches via **Tavily** and deep-crawls job posts using **Crawl4AI**.
4.  **Hybrid RAG Analysis:** Pulls resume data from **PostgreSQL**, reranks findings, and provides Match Scores (0-100).

---

## Technical Highlights

### **1. Agentic Memory & Persistence**
Utilises a **PostgreSQL Checkpointer** (via `langgraph-checkpoint-postgres`) to maintain session state. This allows the agent to remember previous job results and chat history across server restarts, effectively turning a script into a persistent application.

### **2. Hybrid Retrieval **

* **Semantic Search:** Using Gemini embeddings for project-to-job matching.
* **Keyword Extraction:** Ensuring hard skills (Python, LangGraph, React) are strictly validated.
* **Reranking:** Re-evaluating top results to minimise hallucinations and edge cases.


## Tech Stack

- **Framework:** Django Ninja & LangGraph
- **Interference Model:** Cerebras (Llama 3 8B)
- **Database:** PostgreSQL
- **Reranker:** Voyage Reranker
- **Background Worker:** Celery(Workers) with Redis (Queue) 
- **Search & Scrape:** Tavily API for URls & Crawl4AI for Scraping
- **Memory:** PostgresSaver Checkpointer

---
