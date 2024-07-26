import json
import os
from langchain_core.output_parsers import JsonOutputParser
from typing import Any, Dict, Optional, Sequence, Tuple , List
from pydantic import Field

from langchain.chains import APIChain
from langchain.chains.api.base import (
    _check_in_allowed_domain,
)
import os
from langchain_core.output_parsers import JsonOutputParser
from typing import Any, Dict, Optional, Sequence, Tuple , List
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
from langchain.prompts import BasePromptTemplate
from langchain.chains.base import Chain
from sklearn import base
from proxmox.models import APIRequest
from proxmox.proxmox_templates import API_REQUEST_PROMPT, API_RESPONSE_PROMPT
from langchain_core.callbacks import (
    AsyncCallbackManagerForChainRun,
    CallbackManagerForChainRun,
)
from langchain.prompts import BasePromptTemplate
from langchain.chains.base import Chain
from sklearn import base
from proxmox.models import APIRequest
from proxmox.proxmox_templates import API_REQUEST_PROMPT, API_RESPONSE_PROMPT
from core.requests import PowerfulRequestsWrapper
from proxmox.docs import proxmox_api_docs
from proxmox.utils import _validate_URL, _validate_headers
from langchain.retrievers import ContextualCompressionRetriever
from langchain_core.runnables import RunnableSequence, RunnablePassthrough
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.pydantic_v1 import Field, root_validator
from core.utils import (
    _postprocess_text,
    _format_docs,
    _context_runnable
)


from proxmox.utils import _validate_URL, _validate_headers
from langchain.retrievers import ContextualCompressionRetriever
from langchain_core.runnables import RunnableSequence, RunnablePassthrough
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.pydantic_v1 import Field, root_validator
from core.utils import (
    _postprocess_text,
    _format_docs,
    _context_runnable
)



SUPPORTED_HTTP_METHODS: Tuple[str] = (
    "get", "post", "put", "patch", "delete"
)


class ProxmoxAPIChain(Chain):
    api_request_chain: RunnableSequence
    api_response_chain: RunnableSequence
    requests_wrapper: PowerfulRequestsWrapper = Field(exclude=True)
    pve_token: Optional[str]= None
    api_docs: Optional[str] = None
    base_url:Optional[str] = None
    retriever: ContextualCompressionRetriever
    question_key: str = "question"  #: :meta private:
    output_key: str = "output"  #: :meta private:
    limit_to_domains: Optional[Sequence[str]]
    """Use to limit the domains that can be accessed by the API chain.
    
    * For example, to limit to just the domain `https://www.example.com`, set
        `limit_to_domains=["https://www.example.com"]`.
        
    * The default value is an empty tuple, which means that no domains are
        allowed by default. By design this will raise an error on instantiation.

    * Use a None if you want to allow all domains by default -- this is not
        recommended for security reasons, as it would allow malicious users to
        make requests to arbitrary URLS including internal APIs accessible from
        the server.
    """

    @property
    def input_keys(self) -> List[str]:
        """Expect input key.

        :meta private:
        """
        return [self.question_key]

    @property
    def output_keys(self) -> List[str]:
        """Expect output key.

        :meta private:
        """
        return [self.output_key]

    @property
    def _allowed_http_methods(self) -> List[str]:
        return list(set([method.strip().lower() for method in self.allowed_http_methods]))

    @property
    def context_dict(self) -> Dict[str, Any]:
        if self.api_docs:
            return {"api_docs": self.api_docs}
        return {}
    
    @property
    def resolved_base_url(self) -> str:
        if not self.base_url:
            self.base_url = os.getenv("PROXMOX_BASE_URL")
        return self.base_url

    @root_validator(pre=True)
    def validate_base_url(cls, values: Dict) -> Dict:
        _base_url = values.get('base_url') or os.getenv("PROXMOX_BASE_URL")
        if not _base_url:
            raise ValueError("Base URL for Proxmox API not provided.")
        values['base_url'] = _base_url
        return values

    def context_str(self, question: str) -> str:
        """Returns the text passed to the LLM as context."""
        if self.api_docs:
            return self.api_docs
        return _format_docs(self.retriever.invoke(input=question))

    @root_validator(pre=True)
    def validate_api_docs_and_retriever(cls, values: Dict) -> Dict:
        """Check that either api docs or retriever are set."""
        if "api_docs" not in values and "retriever" not in values:
            raise ValueError(
                "Either 'api_docs' or 'retriever' must be set"
            )
        return values

    @root_validator(pre=True)
    def validate_api_request_prompt(cls, values: Dict) -> Dict:
        """Check that api request prompt expects the right variables."""
        input_vars = values["api_request_chain"].middle[0].input_variables
        expected_vars = {"question", "api_docs" , "base_url"}
        if set(input_vars) != expected_vars:
            raise ValueError(
                f"Input variables should be {expected_vars}, got {input_vars}"
            )
        return values

    @root_validator(pre=True)
    def validate_limit_to_domains(cls, values: Dict) -> Dict:
        """Check that allowed domains are valid."""
        if "limit_to_domains" not in values:
            raise ValueError(
                "You must specify a list of domains to limit access using "
                "`limit_to_domains`"
            )
        if (
            not values["limit_to_domains"]
            and values["limit_to_domains"] is not None
        ):
            raise ValueError(
                "Please provide a list of domains to limit access using "
                "`limit_to_domains`."
            )
        return values

    @root_validator(pre=True)
    def validate_api_response_prompt(cls, values: Dict) -> Dict:
        """Check that api answer prompt expects the right variables."""
        input_vars = values["api_response_chain"].middle[0].input_variables
        expected_vars = {"question", "api_docs", "api_url", "api_response" }
        if set(input_vars) != expected_vars:
            raise ValueError(
                f"Input variables should be {expected_vars}, got {input_vars}"
            )
        return values

    def _call(self,
              inputs: Dict[str, str],
              run_manager: Optional[CallbackManagerForChainRun] = None) -> Dict[str, str]:
        _run_manager = run_manager or CallbackManagerForChainRun.get_noop_manager()
        question = inputs[self.question_key]

        # Log retrieved documents for debugging
        if self.verbose:
            for i, doc in enumerate(self.retriever.invoke(input=question)):
                print(f"Retrieved Document {i}: {doc.page_content}")

    
        request_info = self.api_request_chain.invoke(
            {
                **self.context_dict,
                "question": question,
                "base_url":self.resolved_base_url,
            },
            {"callbacks": _run_manager.get_child()}
        )

        if self.verbose:
            print(f"\nRequest info: {json.dumps(request_info, indent=4)}")


        # Construct the full API URL dynamically
        api_url = f"{_postprocess_text(request_info['api_url'])}"

        if self.limit_to_domains and not _check_in_allowed_domain(
            api_url, self.limit_to_domains
        ):
            raise ValueError(
                f"{api_url} is not in the allowed domains: {self.limit_to_domains}"
            )
        request_method = _postprocess_text(
            request_info["request_method"]).lower()

        request_body: Dict[str, Any] = request_info["request_body"]

        if self.verbose:
            print(f"API URL: {api_url}")
            print(f"Request method: {request_method.upper()}")
            print(f"Request body: {request_body}")

        # Resolve the method by name
        request_func = getattr(self.requests_wrapper, request_method)

        if request_method in ("get", "delete"):
            api_response = request_func(api_url)
        elif request_method in ("post", "put", "patch"):
            api_response = request_func(api_url, request_body)
        else:
            raise ValueError(
                f"Expected one of {SUPPORTED_HTTP_METHODS}, got {request_method}"
            )
        run_manager.on_text(
            str(api_response), color="pink", end="\n", verbose=self.verbose
        )

        answer = self.api_response_chain.invoke(
            {
                **self.context_dict,
                "question": question,
                "api_url": api_url,
                "api_response": api_response,
                "base_url":self.resolved_base_url,

            },
            {"callbacks": _run_manager.get_child()}
        )


        return {self.output_key: answer}

    async def _acall(self,
                     inputs: Dict[str, str],
                     run_manager: Optional[AsyncCallbackManagerForChainRun] = None) -> Dict[str, str]:
        _run_manager = run_manager or AsyncCallbackManagerForChainRun.get_noop_manager()
        question = inputs[self.question_key]

        retrieved_docs = self.retriever.get_relevant_documents(query=question)

        context = "\n\n".join([doc.page_content for doc in retrieved_docs])

        request_info = await self.api_request_chain.ainvoke(
            {
                **self._context_dict,
                "question": question,
                "base_url":self.resolved_base_url,
               
            },
            {"callbacks": _run_manager.get_child()}
        )


        if self.verbose:
            print(f'Request info: {request_info}')

        # Construct the full API URL dynamically
        api_url = f"{_postprocess_text(request_info['api_url'])}"
        
        if self.limit_to_domains and not _check_in_allowed_domain(
            api_url, self.limit_to_domains
        ):
            raise ValueError(
                f"{api_url} is not in the allowed domains: {self.limit_to_domains}"
            )
        request_method = _postprocess_text(
            request_info["request_method"]).lower()
        request_body: Dict[str, Any] = request_info["request_body"]


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

        answer = await self.api_response_chain.ainvoke(
            {
                **self._context_dict,
                "question": question,
                "api_url": api_url,
                "api_response": api_response,
                "base_url":self.resolved_base_url,

            },
            {"callbacks": _run_manager.get_child()}
        )



        return {self.output_key: answer}

    @classmethod
    def from_llm_and_api_docs(
        cls,
        llm: BaseLanguageModel,
        retriever: ContextualCompressionRetriever,
        api_docs: str = proxmox_api_docs,
        pve_token: Optional[str] = None,
        base_url: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
        api_url_prompt: BasePromptTemplate = API_REQUEST_PROMPT,
        api_response_prompt: BasePromptTemplate = API_RESPONSE_PROMPT,
        **kwargs: Any,
    ) -> 'ProxmoxAPIChain':
        """Load chain from just an LLM and the api docs."""
        api_request_chain = (
            {
                **_context_runnable(api_docs=api_docs, retriever=retriever),
                "question": RunnablePassthrough(),
                "base_url": RunnablePassthrough(),

            }
            | api_url_prompt
            | llm
            | JsonOutputParser(pydantic_object=APIRequest)
        )
        base_url = _validate_URL(base_url=base_url)
        headers = _validate_headers(headers=headers, pve_token=pve_token)
        requests_wrapper = PowerfulRequestsWrapper(headers=headers)
        api_response_chain = (
            {
                **_context_runnable(api_docs=api_docs, retriever=retriever),
                "question": RunnablePassthrough(),
                "api_url": RunnablePassthrough(),
                "api_response": RunnablePassthrough(),
                "base_url": RunnablePassthrough(),
            }
            | api_response_prompt
            | llm
            | StrOutputParser()
        )
        return cls(
            api_request_chain=api_request_chain,
            api_response_chain=api_response_chain,
            requests_wrapper=requests_wrapper,
            retriever=retriever,
            api_docs=api_docs,
            base_url=base_url,
            pve_token=pve_token,
            **kwargs,
        )


    @property
    def _chain_type(self) -> str:
        return "proxmox_api_chain"
