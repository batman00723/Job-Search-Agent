from typing import Annotated, Sequence
from  ninja import Schema
from pydantic import Field
import operator
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class JobAgentState(Schema):
    query: str

    messages: Annotated[Sequence[BaseMessage], add_messages] = Field(default_factory= list)

    job_urls: Annotated[list[str], operator.add]= Field(default_factory= list)
    
    scraped_content: Annotated[list[str], operator.add]= Field(default_factory=list)
    
    # The final matching reports comparing the job to your resume
    match_reports: list[dict] = Field(default_factory= list)

    retry_count: int 

    user_id: int

    next_action: str = "search"

    #web_search_done: bool

### Note: We are using pydantic Schema as it is better than typed dict 
# In typed dict we used state["query"] to call but in pydantic schema we can also use state.query to call which is clean