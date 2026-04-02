from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    query: str
    chat_history: list
    context: list  # either from db or then web if not in db
    response: str
    user_id: int
    sources: Annotated[list, operator.add] # source from where web data is fetched
    web_search_done: bool

## This is shared memory for our agent each node updates this.
# In this AgentState we defined exactly what info our model needs to remember during a single request.
