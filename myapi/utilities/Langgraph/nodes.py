from myapi.utilities.Langgraph.state import AgentState
from langchain_core.messages import SystemMessage, HumanMessage


def reformulate_query_node(state: AgentState, llm):
    # 1. Get existing data from state
    raw_query = state.get("query", "")
    messages = state.get("messages", [])
    user_id = state.get("user_id") # <-- MUST define this first

    # 2. If it's the first message, just pass through
    if not messages:
        return {
            "query": raw_query,
            "messages": [HumanMessage(content=raw_query)],
            "user_id": user_id
        }

    # 3. Proper prompt that actually includes the history
    # If the user says "What about his age?", the LLM needs the history to know who "his" is.
    history_text = "\n".join([f"{type(m).__name__}: {m.content}" for m in messages[-5:]]) # Last 5 messages
    
    prompt = (
        "Given the following chat history and a new user query, "
        "rephrase the query to be a standalone search term.\n\n"
        f"History:\n{history_text}\n\n"
        f"New Query: {raw_query}\n"
        "Standalone Query:"
        "Only return Standalone Query"
    )
    
    rewritten_query = llm.invoke(prompt).content

    import re

    rewritten_query = llm.invoke(prompt).content
    rewritten_query = re.sub(r'<think>.*?</think>', '', rewritten_query, flags=re.DOTALL)
    rewritten_query = re.sub(r'\*+|"', '', rewritten_query)  # strip ** and quotes
    rewritten_query = rewritten_query.replace("Standalone Query:", "").strip()

    # Take only first line in case model adds explanation after
    rewritten_query = rewritten_query.split('\n')[0].strip()
    # 4. Return everything to keep the state alive
    print(f"{raw_query} ->> {rewritten_query}")
    return {
        "query": rewritten_query.strip(),
        "messages": [HumanMessage(content=raw_query)],
        "user_id": user_id 
    }


# generate node first looks for context to give answer if no context found then it invoke tools call (db serach and websearch)
# then again loops after tools called and this time state has context so this time it doesnt calls tools cus it has context
def generate_node(state: AgentState, llm):

    context_list = []
    for doc in state.get("context", [])[:5]:
        source = doc.get('metadata', {}).get('source', 'unknown')
        content = doc.get('page_content', '')[:500]
        context_list.append(f"SOURCE: {source}\nCONTENT: {content}")
    
    context_text = "\n\n---\n\n".join(context_list)

    system_instructions = f"""You are a strictly grounded RAG Agent.
        Use ONLY the provided CONTEXT to answer. 
        If the CONTEXT is empty or does not contain the answer, say 'I don't know based on my data.
        DO NOT use your internal knowledge ever.
    CONTEXT:
    {context_text}"""

    # Combine System + History
    # state["messages"] now contains the HumanMessage we added in the previous node
    messages = [SystemMessage(content=system_instructions)] + state["messages"][-4:]

    response = llm.invoke(messages)

    #Handle Tool Calls vs Final Answer
    return {
        "messages": [response],
        "response": response.content if not response.tool_calls else ""
    }






# nodes.py — add this new node

import json
from langchain_core.messages import ToolMessage

def process_tool_results_node(state: AgentState):
    print(">>> process_tool_results_node called")
    """
    ToolNode puts results into messages as ToolMessage.
    This node extracts context/sources/web_search_done from those messages
    and writes them into state properly.
    """
    messages = state.get("messages", [])
    
    accumulated_context = list(state.get("context", []))  # keep existing context
    accumulated_sources = list(state.get("sources", []))
    web_search_done = state.get("web_search_done", False)

    for msg in reversed(messages):  # only process latest tool results
        if not isinstance(msg, ToolMessage):
            break  # stop at the first non-tool message from the end
        
        try:
            result = json.loads(msg.content)
        except (json.JSONDecodeError, TypeError):
            continue

        if "context" in result:
            accumulated_context.extend(result["context"])
        if "sources" in result:
            accumulated_sources.extend(result["sources"])
        if "web_search_done" in result:
            web_search_done = result["web_search_done"]

        print(">>> raw tool content:", str(msg.content)[:500])

    return {
        "context": accumulated_context,
        "sources": accumulated_sources,
        "web_search_done": web_search_done,
    }


from langchain_core.messages import AIMessage
import uuid

def force_tool_call_node(state: AgentState):
    """
    Context is empty — bypass LLM decision and directly invoke both tools.
    Construct a fake AIMessage with tool_calls so ToolNode can run them.
    """
    query = state.get("query", "")
    user_id = state.get("user_id")

    print(">>> forcing tool calls for query:", query)

    fake_ai_message = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "retrieve_document",
                "args": {"query": query, "user_id": user_id},
                "id": str(uuid.uuid4()),
                "type": "tool_call"
            },
            {
                "name": "web_search",
                "args": {"query": query, "user_id": user_id},
                "id": str(uuid.uuid4()),
                "type": "tool_call"
            }
        ]
    )
    return {"messages": [fake_ai_message]}