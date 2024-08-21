from typing import Dict, Any, Optional
import os
from typing import Iterable, Optional, List, Dict, Any
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_core.runnables import RunnablePassthrough


def _format_docs(docs: List[Document]) -> str:
    if not docs:
        return ""
    if len(docs) == 1:
        return docs[0].page_content
    return "\n\n".join([doc.page_content for doc in docs])



def _postprocess_text(
        text: str,
        remove_chars: Optional[Iterable[str]] = ["\n", "**"]
) -> str:
    if remove_chars:
        for char in remove_chars:
            text = text.replace(char, "")
    return text.strip()


def _context_runnable(api_docs: str, retriever: VectorStoreRetriever) -> Dict[str, Any]:
    if api_docs:
        return {"api_docs": RunnablePassthrough()}
    return {"api_docs": retriever | _format_docs}


def _validate_headers(
        headers: Optional[Dict[str, Any]] = None,
        pve_token: Optional[str] = None,
) -> Dict[str, Any]:
    _pve_token = pve_token or os.getenv("PVE_TOKEN")
    auth: Dict[str, str] = {'Authorization': _pve_token}
    if headers:
        if 'Authorization' in headers:
            return headers
        return {**auth, **headers}
    return auth

def _validate_URL(
        base_url: str,
) -> str:
    _base_url = base_url or os.getenv("PROXMOX_BASE_URL")
    if not _base_url:
        raise ValueError("Base URL must be provided either as an argument or via the 'PROXMOX_BASE_URL' environment variable.")
    return _base_url

