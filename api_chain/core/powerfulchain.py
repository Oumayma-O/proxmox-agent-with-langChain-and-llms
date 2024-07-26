import json
import logging
from core.templates import API_REQUEST_PROMPT, API_RESPONSE_PROMPT
from langchain.chains import APIChain
from typing import Any, Dict, Optional, Sequence
from pydantic import Field
from langchain.prompts import BasePromptTemplate
from langchain.chains.llm import LLMChain
from langchain_community.utilities.requests import TextRequestsWrapper
from langchain_core.language_models import BaseLanguageModel
from langchain_core.callbacks import (
    AsyncCallbackManagerForChainRun,
    CallbackManagerForChainRun,
)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class PowerfulAPIChain(APIChain):
    api_request_chain: LLMChain
    api_answer_chain: LLMChain
    requests_wrapper: TextRequestsWrapper = Field(exclude=True)
    api_docs: str
    question_key: str = "question"  #: :meta private:
    output_key: str = "output"  #: :meta private:
    limit_to_domains: Optional[Sequence[str]]

    def _call(self,
              inputs: Dict[str, str],
              run_manager: Optional[CallbackManagerForChainRun] = None) -> Dict[str, str]:
        _run_manager = run_manager or CallbackManagerForChainRun.get_noop_manager()
        question = inputs[self.question_key]
        
        # Log the question
        logger.debug(f"Question: {question}")
        
        request_info: str = self.api_request_chain.predict(
            question=question,
            api_docs=self.api_docs,
            callbacks=_run_manager.get_child()
        )
        
        # Log the raw request_info
        logger.debug(f"Raw request info: {request_info}")

        try:
            api_url, request_method, request_body = request_info.split('|', 2)
        except ValueError as e:
            logger.error(f"Error parsing request info: {e}")
            return {
                self.output_key: "",
                "error": f"Output parse error: {str(e)}"
            }

        # Log the parsed components
        logger.debug(f"API URL: {api_url}")
        logger.debug(f"Request method: {request_method}")
        logger.debug(f"Request body: {request_body}")

        api_url = api_url.strip().replace('|', '')
        request_method = request_method.strip().lower().replace('|', '')
        request_body = request_body.strip().replace('|', '')

        # Log the cleaned components
        logger.debug(f"Cleaned API URL: {api_url}")
        logger.debug(f"Cleaned Request method: {request_method}")
        logger.debug(f"Cleaned Request body: {request_body}")

        # Resolve the method by name
        request_func = getattr(self.requests_wrapper, request_method)

        if request_method in ("get", "delete", "head"):
            api_response = request_func(api_url, headers=self.headers)
        else:
            api_response = request_func(api_url, json.loads(request_body), headers=self.headers)

        # Log the API response
        api_response_text = api_response.text if hasattr(api_response, 'text') else api_response
        logger.debug(f"API response: {api_response_text}")

        try:
            api_response_json = api_response.json()
        except json.JSONDecodeError:
            logger.error("Failed to parse response JSON")
            api_response_json = {"error": "Failed to parse response JSON"}

        answer = self.api_answer_chain.predict(
            question=question,
            api_docs=self.api_docs,
            api_url=api_url,
            api_response=api_response_json,
            callbacks=_run_manager.get_child()
        )
        
        # Log the final answer
        logger.debug(f"Final answer: {answer}")

        return {self.output_key: answer}

    async def _acall(self,
                     inputs: Dict[str, str],
                     run_manager: Optional[AsyncCallbackManagerForChainRun] = None) -> Dict[str, str]:
        _run_manager = run_manager or AsyncCallbackManagerForChainRun.get_noop_manager()
        question = inputs[self.question_key]
        request_info: str = await self.api_request_chain.apredict(
            question=question,
            api_docs=self.api_docs,
            callbacks=_run_manager.get_child()
        )
        logger.debug(f'Request info: {request_info}')

        try:
            api_url, request_method, request_body = request_info.split('|', 2)
        except ValueError as e:
            return {
                self.output_key: "",
                "error": f"Output parse error: {str(e)}"
            }

        api_url = api_url.strip().replace('|', '')
        request_method = request_method.strip().lower().replace('|', '')
        request_body = request_body.strip().replace('|', '')

        logger.debug(f"API URL: {api_url}")
        logger.debug(f"Request method: {request_method.upper()}")
        logger.debug(f"Request body: {request_body}")

        # Resolve the method by name
        request_func = getattr(self.requests_wrapper, f"a{request_method}")

        if request_method in ("get", "delete", "head"):
            api_response = await request_func(api_url)
        else:
            api_response = await request_func(api_url, json.loads(request_body))

        answer = await self.api_answer_chain.apredict(
            question=question,
            api_docs=self.api_docs,
            api_url=api_url,
            api_response=api_response,
            callbacks=_run_manager.get_child()
        )
        return {self.output_key: answer}

    @classmethod
    def from_llm_and_api_docs(
        cls,
        llm: BaseLanguageModel,
        api_docs: str,
        headers: Optional[Dict[str, Any]] = None,
        api_url_prompt: BasePromptTemplate = API_REQUEST_PROMPT,
        api_response_prompt: BasePromptTemplate = API_RESPONSE_PROMPT,
        **kwargs: Any,
    ) -> 'PowerfulAPIChain':
        """Load chain from just an LLM and the api docs."""
        get_request_chain = LLMChain(llm=llm, prompt=api_url_prompt)
        requests_wrapper = TextRequestsWrapper(headers=headers)
        get_answer_chain = LLMChain(llm=llm, prompt=api_response_prompt)
        return cls(
            api_request_chain=get_request_chain,
            api_answer_chain=get_answer_chain,
            requests_wrapper=requests_wrapper,
            api_docs=api_docs,
            **kwargs,
        )

