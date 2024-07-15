
class CustomRetriever:
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore

    def get_relevant_documents(self, query):
        # First retrieve the most similar documents using embeddings
        retrieved_docs = self.vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3}).get_relevant_documents(query)
        
        # Further filter documents based on specific keywords
        keywords = ["Create VM", "new VM", "initial creation", "setup of a VM"]
        filtered_docs = []
        for doc in retrieved_docs:
            if any(keyword.lower() in doc.page_content.lower() for keyword in keywords):
                filtered_docs.append(doc)
        
        # Return the filtered documents or the original retrieval if no keywords matched
        return filtered_docs if filtered_docs else retrieved_docs
