import json
from langchain.vectorstores import Chroma
from typing import Any, Dict, Optional, Sequence, Tuple
from pydantic import Field

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

from core.templates import API_REQUEST_PROMPT, API_RESPONSE_PROMPT
from core.requests import PowerfulRequestsWrapper
from proxmox.docs import proxmox_api_docs
from proxmox.utils import _validate_headers

SUPPORTED_HTTP_METHODS: Tuple[str] = (
    "get", "post", "put", "patch", "delete"
)

class ProxmoxAPIChain(APIChain):
    api_request_chain: LLMChain
    api_answer_chain: LLMChain
    requests_wrapper: PowerfulRequestsWrapper = Field(exclude=True)
    pve_token: str
    vectorstore: Chroma
    question_key: str = "question"  #: :meta private:
    output_key: str = "output"  #: :meta private:
    limit_to_domains: Optional[Sequence[str]]

    def _call(self,
              inputs: Dict[str, str],
              run_manager: Optional[CallbackManagerForChainRun] = None) -> Dict[str, str]:
        _run_manager = run_manager or CallbackManagerForChainRun.get_noop_manager()
        question = inputs[self.question_key]

        retriever = self.vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 1})

        retrieved_docs = retriever.get_relevant_documents(question)

        request_info = self.api_request_chain.predict(
            question=question,
            docs=retrieved_docs,
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

        answer = self.api_answer_chain.predict(
            question=question,
            docs=retrieved_docs,
            api_url=api_url,
            api_response=api_response,
            callbacks=_run_manager.get_child()
        )
        return {self.output_key: answer}

    async def _acall(self,
                     inputs: Dict[str, str],
                     run_manager: Optional[AsyncCallbackManagerForChainRun] = None) -> Dict[str, str]:
        _run_manager = run_manager or AsyncCallbackManagerForChainRun.get_noop_manager()
        question = inputs[self.question_key]

        retriever = self.vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 1})

        retrieved_docs = retriever.get_relevant_documents(question)

        request_info = await self.api_request_chain.apredict(
            question=question,
            docs=retrieved_docs,
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
            docs=retrieved_docs,
            api_url=api_url,
            api_response=api_response,
            callbacks=_run_manager.get_child()
        )
        return {self.output_key: answer}

    @classmethod
    def from_llm_and_api_docs(
        cls,
        llm: BaseLanguageModel,
        vectorstore: Chroma,
        pve_token: Optional[str] = "",
        headers: Optional[Dict[str, Any]] = None,
        api_url_prompt: BasePromptTemplate = API_REQUEST_PROMPT,
        api_response_prompt: BasePromptTemplate = API_RESPONSE_PROMPT,
        **kwargs: Any,
    ) -> 'ProxmoxAPIChain':
        """Load chain from just an LLM and the api docs."""
        get_request_chain = LLMChain(llm=llm, prompt=api_url_prompt)
        headers = _validate_headers(headers=headers, pve_token=pve_token)
        requests_wrapper = PowerfulRequestsWrapper(headers=headers)
        get_answer_chain = LLMChain(llm=llm, prompt=api_response_prompt)
        return cls(
            api_request_chain=get_request_chain,
            api_answer_chain=get_answer_chain,
            requests_wrapper=requests_wrapper,
            vectorstore=vectorstore,
            pve_token=pve_token,  # Ensure pve_token is passed here
            **kwargs,
        )

    @property
    def _chain_type(self) -> str:
        return "proxmox_api_chain"
