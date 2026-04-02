from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import retrieve_db_node, web_search_node, generate_node
from typing import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.config import settings
from langgraph.checkpoint.memory import MemorySaver

class GradeAnswer(TypedDict):
    is_sufficient: bool


def create_rag_agent(llm):

    gemini_grader = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite-preview",  
        temperature=0.1,
        api_key=settings.google_api_key.get_secret_value()
    )
    # structured output is who only gives structured response in our case True or False.
    # That's why we are using gemini as cerebras doesnt support .get_strutured_output
    structured_llm = gemini_grader.with_structured_output(GradeAnswer)

    workflow = StateGraph(AgentState)

    workflow.add_node("retrieve_db", retrieve_db_node)
    workflow.add_node("web_search", web_search_node)
    workflow.add_node("generate", lambda state: generate_node(state, llm=llm))

    workflow.set_entry_point("retrieve_db")
    workflow.add_edge("retrieve_db", "generate")

    def router_logic(state: AgentState):

        if state.get("web_search_done"):
            return "end"

        prompt = (
            f"User Query: {state['query']}\n"
            f"AI Response: {state['response']}\n\n"
            "Assess if the AI Response actually answered the question using specific facts. "
            "or if it gives a 'sorry' or 'I don't know' type message. "
            "Return is_sufficient=true only if the answer is factually useful and correct."
        )

        try:
            decision = structured_llm.invoke(prompt)

            if decision.get("is_sufficient"):
                return "end"
            return "web_search"

        except Exception as e:
            # fallback check response text manually
            response_lower = state["response"].lower()
            if "sorry" in response_lower or "don't have enough" in response_lower:
                return "web_search"
            return "end"

    workflow.add_conditional_edges(
        "generate", router_logic,
        {
            "web_search": "web_search",
            "end": END
        }
    )
    workflow.add_edge("web_search", "generate")

    memory= MemorySaver()

    return workflow.compile(checkpointer= memory)