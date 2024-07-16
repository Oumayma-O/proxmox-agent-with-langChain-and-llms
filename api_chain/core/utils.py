from typing import Iterable, Optional, List
from langchain_core.documents import Document


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
