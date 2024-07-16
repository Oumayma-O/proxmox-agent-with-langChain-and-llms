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
