from langgraph.graph import StateGraph, END
from .state import JobAgentState
from backend.config import settings
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from .nodes import rewrite_query_node, search_node, router, scrape_job_node, analyse_jobs_node, intent_classifier_node, chat_node, reflection_node, should_continue
from functools import partial

DB_URL = settings.db_url.get_secret_value()

_pool = ConnectionPool(
    conninfo=DB_URL,
    max_size=10,
    kwargs={"autocommit": True, "prepare_threshold": 0}
)

memory = PostgresSaver(_pool)
memory.setup()


def create_agent(llm):
    workflow = StateGraph(JobAgentState)

    workflow.add_node("intent_classifier", partial(intent_classifier_node, llm=llm))
    workflow.add_node("chat_node", partial(chat_node, llm=llm))
    workflow.add_node("rewrite", partial(rewrite_query_node, llm=llm))
    workflow.add_node("search_jobs", search_node)
    workflow.add_node("scrape_jobs", scrape_job_node)
    workflow.add_node("analyse_results", partial(analyse_jobs_node, llm=llm))
    workflow.add_node("reflection", partial(reflection_node, llm= llm))

    workflow.set_entry_point("intent_classifier")
    workflow.add_conditional_edges(
        "intent_classifier",
        lambda x: x.next_action,
        {
            "search": "rewrite",
            "chat": "chat_node"
        }
    )
    workflow.add_edge("rewrite", "search_jobs")
    workflow.add_conditional_edges(
        "search_jobs",
        router,
        {
            "scrape_job_node": "scrape_jobs",
            "rewrite_query_node": "rewrite",
            "end": END
        }
    )
    workflow.add_edge("scrape_jobs", "analyse_results")
    workflow.add_edge("analyse_results", "reflection")
    workflow.add_conditional_edges(
        "reflection",
        should_continue,
        {
            "revise": "analyse_results", # LOOP BACK
            "end": END
        }
    )
    workflow.add_edge("chat_node", END)

    return workflow.compile(checkpointer=memory)