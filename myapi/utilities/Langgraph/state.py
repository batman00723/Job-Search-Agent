from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages # similar to operator.add

class AgentState(TypedDict):
    query: str
    messages : Annotated[list, add_messages]  # THis chathistory refrest to our postgres saver (RENAME IT RO MESSAGES AS IN LANGGRAPH IT NEED IT TO NAMED AS MESSAGES)
    # add_messges ensures old messages aren't deleted 
    context: list  # either from db or then web if not in db
    response: str
    user_id: int
    sources: list # source from where web data is fetched
    web_search_done: bool

## This is shared memory for our agent each node updates this.
# In this AgentState we defined exactly what info our model needs to remember during a single request.
