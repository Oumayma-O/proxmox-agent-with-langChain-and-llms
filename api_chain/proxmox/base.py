import os
from typing import Any, Dict, Optional, Sequence, Tuple
from langchain_core.pydantic_v1 import Field, root_validator

from langchain.prompts import BasePromptTemplate
from langchain.chains.llm import LLMChain
from langchain_core.language_models import BaseLanguageModel

from api_chain.core.templates import API_REQUEST_PROMPT, API_RESPONSE_PROMPT
from api_chain.core.requests import PowerfulRequestsWrapper
from api_chain.core.powerfulchain import PowerfulAPIChain
from proxmox.docs import proxmox_api_docs
from proxmox.utils import _validate_headers

SUPPORTED_HTTP_METHODS: Tuple[str] = (
    "get", "post", "put", "patch", "delete"
)


class ProxmoxAPIChain(PowerfulAPIChain):
    api_request_chain: LLMChain
    api_answer_chain: LLMChain
    requests_wrapper: PowerfulRequestsWrapper = Field(exclude=True)
    pve_token: str
    api_docs: str
    question_key: str = "question"  #: :meta private:
    output_key: str = "output"  #: :meta private:
    limit_to_domains: Optional[Sequence[str]]

    @root_validator(pre=True)
    def validate_headers_authorization(cls, values: Dict) -> Dict:
        """Check that headers contains Authorization."""
        headers: Dict[str, Any] = values["requests_wrapper"].headers
        if (
            not "PVE_TOKEN" in os.environ
            and not values["pve_token"]
            and (not headers or 'Authorization' not in headers)
        ):
            raise ValueError(
                "Can't proceed without authorization. Consider one of the following:\n"
                "- Set 'PVE_TOKEN' environment variable.\n"
                "- Set 'pve_token' attribute.\n"
                "- Pass valid Authorization token in headers."
            )
        return values

    @classmethod
    def from_llm_and_api_docs(
        cls,
        llm: BaseLanguageModel,
        api_docs: str = proxmox_api_docs,
        pve_token: Optional[str] = None,
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
            api_docs=api_docs,
            **kwargs,
        )

    @property
    def _chain_type(self) -> str:
        return "proxmox_api_chain"
