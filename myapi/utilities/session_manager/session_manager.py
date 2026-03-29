import uuid
from functools import wraps

def provide_session_id(func):
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        session_id= request.GET.get('session_id')

        if not session_id:
            session_id= str(uuid.uuid4())

        request.generated_session_id= session_id

        return func(self, request, *args, **kwargs)
    
    return wrapper