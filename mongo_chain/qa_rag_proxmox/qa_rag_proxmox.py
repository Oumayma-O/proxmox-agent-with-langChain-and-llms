from langchain_chroma import Chroma
from langchain_community.document_loaders.mongodb import MongodbLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# Model instantiation
llm = ChatOllama(model="llama3:instruct")
# Load embeddings model
embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

# Load the contents of the inventory from MongoDB
loader = MongodbLoader(
        connection_string="mongodb://localhost:27017/",
        db_name="proxmox_dummy",
        collection_name="proxmox_dummy_inventory",

)
docs = loader.load()

system_prompt = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer "
    "the question. If you don't know the answer, say that you "
    "don't know. Use three sentences maximum and keep the "
    "answer concise. Do not say according to the provided context."
    "\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{question}"),
    ]
)

vectorstore = Chroma.from_documents(documents=docs, embedding=embedding_function)

retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 1})


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

while True:
    try:
        question = input("question > ")
        print(f"DEBUG: {retriever.invoke(question)}") 
        for chunk in rag_chain.stream(question):
            print(chunk, end='', flush=True)

    except (EOFError, KeyboardInterrupt):
        break
    print("\n") 


