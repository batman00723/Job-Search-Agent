from typing import Annotated, Sequence
from  ninja import Schema
from pydantic import Field
import operator
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class JobAgentState(Schema):
    query: str

    messages: Annotated[Sequence[BaseMessage], add_messages] = Field(default_factory= list)

    job_urls: list[str]= Field(default_factory=list)
    
    scraped_content: list[str]= Field(default_factory=list)
    
    # The final matching reports comparing the job to your resume
    match_reports: list[dict] = Field(default_factory= list)

    retry_count: int = 0

    user_id: int

    next_action: str = ""

    critique: str = "" # this is for feedback of critique node 
    
    revision_count: int= 0 # only do 1 attempts to make the answer better if bad


### Note: We are using pydantic Schema as it is better than typed dict 
# In typed dict we used state["query"] to call but in pydantic schema we can also use state.query to call which is clean
