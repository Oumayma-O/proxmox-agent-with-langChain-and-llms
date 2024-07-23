from pydantic import BaseModel, Field
from typing import Literal, Dict, Any


class APIRequest(BaseModel):
    api_url: str = Field(description="API URL of the request")
    request_method: Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE'] = Field(
        description="Request method"
    )
    request_body: Dict[str, Any] = Field(description="Request body")
