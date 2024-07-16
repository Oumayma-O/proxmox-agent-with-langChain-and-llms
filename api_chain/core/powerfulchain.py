import json
from typing import Any, Dict, Optional, Sequence, Tuple
from langchain_core.pydantic_v1 import Field

from langchain.chains import APIChain
from langchain.chains.api.base import (
    _check_in_allowed_domain,
)
from langchain.prompts import BasePromptTemplate
from langchain.chains.llm import LLMChain
from langchain_core.language_models import BaseLanguageModel
from langchain_core.callbacks import (
    AsyncCallbackManagerForChainRun,
    CallbackManagerForChainRun,
)

from core.templates import (
    API_REQUEST_PROMPT,
    API_RESPONSE_PROMPT
)
from core.requests import PowerfulRequestsWrapper

SUPPORTED_HTTP_METHODS: Tuple[str] = (
    "get", "post", "put", "patch", "delete"
)


class PowerfulAPIChain(APIChain):
    api_request_chain: LLMChain
    api_answer_chain: LLMChain
    requests_wrapper: PowerfulRequestsWrapper = Field(exclude=True)
    api_docs: str
    question_key: str = "question"  #: :meta private:
    output_key: str = "output"  #: :meta private:
    limit_to_domains: Optional[Sequence[str]]

    def _call(self,
              inputs: Dict[str, str],
              run_manager: Optional[CallbackManagerForChainRun] = None) -> Dict[str, str]:
        _run_manager = run_manager or CallbackManagerForChainRun.get_noop_manager()
        question = inputs[self.question_key]
        request_info = self.api_request_chain.invoke(
            {
                "question": question,
                "api_docs": self.api_docs,
            },
            callbacks=_run_manager.get_child()
        )['text']
        if self.verbose:
            print(f"\nRequest info: {request_info}")

        request_info_list = request_info.split('|')

        if len(request_info_list) < 3:
            raise ValueError("Request info parse error")

        api_url, request_method, request_body = request_info_list[:3]

        api_url = api_url.strip().replace('|', '')
        if self.limit_to_domains and not _check_in_allowed_domain(
            api_url, self.limit_to_domains
        ):
            raise ValueError(
                f"{api_url} is not in the allowed domains: {self.limit_to_domains}"
            )
        request_method = request_method.strip().lower().replace('|', '')
        request_body = request_body.strip().replace('|', '')

        if self.verbose:
            print(f"API URL: {api_url}")
            print(f"Request method: {request_method.upper()}")
            print(f"Request body: {request_body}")

        # Resolve the method by name
        request_func = getattr(self.requests_wrapper, request_method)

        if request_method in ("get", "delete"):
            api_response = request_func(api_url)
        elif request_method in ("post", "put", "patch"):
            api_response = request_func(api_url, json.loads(request_body))
        else:
            raise ValueError(
                f"Expected one of {SUPPORTED_HTTP_METHODS}, got {request_method}"
            )
        run_manager.on_text(
            str(api_response), color="yellow", end="\n", verbose=self.verbose
        )

        answer = self.api_answer_chain.invoke(
            {
                "question": question,
                "api_docs": self.api_docs,
                "api_url": api_url,
                "api_response": api_response,
            },
            callbacks=_run_manager.get_child()
        )['text']
        return {self.output_key: answer}

    async def _acall(self,
                     inputs: Dict[str, str],
                     run_manager: Optional[AsyncCallbackManagerForChainRun] = None) -> Dict[str, str]:
        _run_manager = run_manager or AsyncCallbackManagerForChainRun.get_noop_manager()
        question = inputs[self.question_key]
        request_info = await self.api_request_chain.apredict(
            question=question,
            api_docs=self.api_docs,
            callbacks=_run_manager.get_child()
        )
        if self.verbose:
            print(f'Request info: {request_info}')

        try:
            api_url, request_method, request_body = request_info.split('|', 2)
        except ValueError as e:
            return {
                self.output_key: "",
                "error": f"Output parse error: {str(e)}"
            }

        api_url = api_url.strip().replace('|', '')
        if self.limit_to_domains and not _check_in_allowed_domain(
            api_url, self.limit_to_domains
        ):
            raise ValueError(
                f"{api_url} is not in the allowed domains: {self.limit_to_domains}"
            )
        request_method = request_method.strip().lower().replace('|', '')
        request_body = request_body.strip().replace('|', '')

        if self.verbose:
            print(f"API URL: {api_url}")
            print(f"Request method: {request_method.upper()}")
            print(f"Request body: {request_body}")

        # Resolve the method by name
        request_func = getattr(self.requests_wrapper, f"a{request_method}")

        if request_method in ("get", "delete"):
            api_response = await request_func(api_url)
        elif request_method in ("post", "put", "patch"):
            api_response = await request_func(api_url, json.loads(request_body))
        else:
            raise ValueError(
                f"Expected one of {SUPPORTED_HTTP_METHODS}, got {request_method}"
            )
        await run_manager.on_text(
            str(api_response), color="yellow", end="\n", verbose=self.verbose
        )

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
        requests_wrapper = PowerfulRequestsWrapper(headers=headers)
        get_answer_chain = LLMChain(llm=llm, prompt=api_response_prompt)
        return cls(
            api_request_chain=get_request_chain,
            api_answer_chain=get_answer_chain,
            requests_wrapper=requests_wrapper,
            api_docs=api_docs,
            **kwargs,
        )

    @property
    def _chain_type(self) -> str:
        return "powerful_api_chain"
