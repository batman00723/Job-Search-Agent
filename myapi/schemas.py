from ninja import Schema
from pydantic import Field
from datetime import datetime

class UserOut(Schema):
    id: int
    username: str
    email: str | None = None

class DocumentIn(Schema):
    doc_name: str = Field(min_length= 3, max_length= 50)

class DocumentOut(Schema):
    user: UserOut
    id: int
    doc_name: str
    document: str
    file_type: str
    status: str
    uploaded_at: datetime