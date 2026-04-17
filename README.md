# Job-Search-Agent 
### **A Stateful, Agentic RAG Pipeline for Job Analysis**

Job-Search-Agent is an AI system that orchestrates specialised agents to automate the end-to-end process of job hunting. By combining **LangGraph** orchestration with **Hybrid RAG**, this agent doesn't just find jobs—it validates them against your professional Resume.

---

## System Architecture

<p align="center">
  <img src="job agent.png" width="600" title="System Architecture">
</p>

The system operates in a stateful manner:
1.  **Intent Classifier:** Analyses the query to decide between a fresh search or a follow-up conversation.
2.  **Rewrite Node:** Resolves pronouns from chat history and optimises search strings.
3.  **Search & Scrape:** Executes live web searches via **Tavily** and deep-crawls job posts using **Crawl4AI**.
4.  **Hybrid RAG Analysis:** Pulls resume data from **PostgreSQL**, reranks findings, and provides Match Scores (0-100).

---

## Technical Highlights

### **1. Agentic Memory & Persistence**
Utilises a **PostgreSQL Checkpointer** (via `langgraph-checkpoint-postgres`) to maintain session state. This allows the agent to remember previous job results and chat history across server restarts, effectively turning a script into a persistent application.

### **2. Hybrid Retrieval Engine**
Unlike standard vector-only RAG, this system uses a hybrid approach:
* **Semantic Search:** Using OpenAI/Groq embeddings for project-to-job matching.
* **Keyword Extraction:** Ensuring hard skills (Python, LangGraph, React) are strictly validated.
* **Reranking:** Re-evaluating top results to minimise hallucinations and edge cases.


## Tech Stack

- **Framework:** Django Ninja & LangGraph
- **Interference:** Cerebras (Llama 3 8B)
- **Database:** PostgreSQL 
- **Search & Scrape:** Tavily API & Crawl4AI
- **Memory:** PostgresSaver Checkpointing

---
