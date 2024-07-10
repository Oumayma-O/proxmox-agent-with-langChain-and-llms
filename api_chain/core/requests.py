from langchain_community.utilities.requests import TextRequestsWrapper
from requests import Response
from typing import Dict, Any, Union
import aiohttp


class PowerfulRequestsWrapper(TextRequestsWrapper):
    def _get_resp_content(self, response: Response) -> Union[str, Dict[str, Any]]:
        if self.response_content_type == "text":
            return f"Status: {response.status_code} {response.reason}\nResponse: {response.text}"
        elif self.response_content_type == "json":
            return f"Status: {response.status_code} {response.reason}\nResponse: {response.json()}"
        else:
            raise ValueError(f"Invalid return type: {self.response_content_type}")

    async def _aget_resp_content(
        self, response: aiohttp.ClientResponse
    ) -> Union[str, Dict[str, Any]]:
        if self.response_content_type == "text":
            return await f"Status: {response.status} {response.reason}\nResponse: {response.text()}"
        elif self.response_content_type == "json":
            return await f"Status: {response.status} {response.reason}\nResponse: {response.json()}"
        else:
            raise ValueError(f"Invalid return type: {self.response_content_type}")