from langgraph.graph import StateGraph, END
from .state import AgentState
from typing import TypedDict
from backend.config import settings
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver

from langgraph.prebuilt import ToolNode
from myapi.utilities.Langgraph.tools import agent_tools
from .nodes import generate_node, reformulate_query_node,  process_tool_results_node, force_tool_call_node


class GradeAnswer(TypedDict):
    is_sufficient: bool

DB_URL= settings.db_url.get_secret_value()

connection_kwargs= {
    "autocommit": True,
    "prepare_threshold": 0
}

pool= ConnectionPool(
    conninfo=DB_URL,
    max_size=10,
    open= True,
    kwargs= connection_kwargs,
    reconnect_failed= None,
    reconnect_timeout=5,
    max_waiting=5,
    check= ConnectionPool.check_connection,
)

memory= PostgresSaver(pool)
memory.setup()

def create_rag_agent(llm):
    
    # Let LLM know these tools exist
    llm_with_tools= llm.bind_tools(agent_tools)

    workflow= StateGraph(AgentState)

    workflow.add_node("reformulate", lambda state: reformulate_query_node(state, llm= llm))

    workflow.add_node("force_tool_call", force_tool_call_node)  # NEW

    # We are passing llm with tools binded to generate node
    workflow.add_node("generate", lambda state: generate_node(state, llm= llm_with_tools))

    # Tool Node is a pre-built worker to run parallel tools automatically 
    # ToolNode triggres both tools at same time
    workflow.add_node("tools", ToolNode(agent_tools))

    workflow.add_node("process_tools", process_tool_results_node) # NEW ADDED

    workflow.set_entry_point("reformulate")

    workflow.add_edge("reformulate", "force_tool_call")
    workflow.add_edge("force_tool_call", "tools")
    workflow.add_edge("tools", "process_tools")
    workflow.add_edge("process_tools", "generate")

    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        print(">>> tool_calls after generate:", last_message.tool_calls)
        if last_message.tool_calls:
            return "tools"
        return "end"

    workflow.add_conditional_edges(
        "generate",
        should_continue,
        {"tools": "tools", "end": END}
    )

    return workflow.compile(checkpointer=memory)

## Here as you can see I'm using LLM driven tools selection as LLM decides which tools to use and
## in this way we save much token but do do rely on LLM which sometimes hallucinate that's a trade off to hardcoding tol call.
