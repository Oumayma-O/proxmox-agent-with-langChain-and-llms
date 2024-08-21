from fastapi import FastAPI
from .proxmox.docs import _proxmox_api_docs
from .proxmox.base import ProxmoxAPIChain
from langchain.text_splitter import RecursiveJsonSplitter
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.vectorstores.surrealdb import SurrealDBStore
from fastapi.middleware.cors import CORSMiddleware
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph, START
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableLambda
from typing import List, TypedDict
from pydantic import BaseModel
from langserve import add_routes
from langchain_groq import ChatGroq
from fastapi import FastAPI, APIRouter
from fastapi.responses import RedirectResponse
from pydantic_settings import BaseSettings
import asyncio
import base64
import yaml
import os

load_dotenv()

# Get the absolute path to the current script's directory
base_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the absolute path to the tokens.yaml file
tokens_path = os.path.join(base_dir, 'proxmox', 'dict.yaml')

# Load the YAML file using the absolute path
with open(tokens_path, 'r') as file:
    proxmox_nodes = yaml.safe_load(file)

surrealdb_url = os.getenv('SURREALDB_URL')
surrealdb_user = os.getenv('SURREALDB_USER')
surrealdb_password = os.getenv('SURREALDB_PWD')

# Initialize the RecursiveJsonSplitter
splitter = RecursiveJsonSplitter(max_chunk_size=4000)
docs = splitter.create_documents(_proxmox_api_docs)

# Initialize the HuggingFaceEmbeddings with trust_remote_code=True
ef = HuggingFaceEmbeddings(
    model_name="infgrad/stella_en_400M_v5",
    model_kwargs={"trust_remote_code": True},
)

# SurrealDB connection parameters
dburl = "ws://localhost:8000/rpc"
ns = "langchain"
db_name = "proxmox_api_docs"
collection = "proxmox_collection"
db_user = surrealdb_user
db_pass = surrealdb_password

# Initialize the SurrealDBStore with documents
db = SurrealDBStore(
    embedding_function=ef,
    dburl=dburl,
    ns=ns,
    db=db_name,
    collection=collection,
    db_user=db_user,
    db_pass=db_pass
)

# Initialize the cross-encoder model and retrievers
cross_encoder_model = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
compressor = CrossEncoderReranker(model=cross_encoder_model, top_n=3)
retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 3})
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor, base_retriever=retriever
)

# Supervisor and worker setup
workers = [node["name"] for node in proxmox_nodes]

prompt = PromptTemplate(
    template=("""
    You are a supervisor tasked with routing a query to one of the following workers: {workers}. 
    Given the following user request, respond with the worker to act next. Each worker will perform a task 
    and respond with their results and status. The worker output will be returned to the user. 
    The options for workers are {workers}. Return 'end' if the request isn't related to any of the given workers.

    User request: {question}

    Respond in JSON format with a single key "next" which holds the worker name.

    next :
    """),
    input_variables=["question"],
    partial_variables={"workers": workers}
)

# Initialize the LLM for the supervisor
llm_sup = ChatOllama(model="phi3", temperature=0, format="json")
sup_chain = prompt | llm_sup | JsonOutputParser()

class ProxmoxTeamState(TypedDict):
    messages: List[BaseMessage]
    team_members: List[str]
    next: str

def supervisor(state: ProxmoxTeamState) -> ProxmoxTeamState:
    print(f"processing_request: Current state: {state}")
    question = state["messages"][0]
    result = sup_chain.invoke({"question": question})
    state["next"] = result["next"]
    state["team_members"] = [node["name"] for node in proxmox_nodes]
    return state

# Initialize LLM for workers

llm = ChatGroq(
    model="llama-3.1-70b-versatile",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)
agents = {}
for node in proxmox_nodes:
    print(node['base_url'])
    decoded_token = base64.b64decode(os.getenv(node['token'])).decode('utf-8')
    chain = ProxmoxAPIChain.from_llm_and_api_docs(
        llm,
        retriever=compression_retriever,
        headers={"Authorization": decoded_token},
        pve_token=decoded_token,
        verbose=False,
        limit_to_domains=[node["base_url"]],
        base_url=node["base_url"],
    )
    agents[node["name"]] = chain

def Worker_node(state: ProxmoxTeamState, node_name: str) -> ProxmoxTeamState:
    print(f"{state['next']} / {node_name}")
    question = state["messages"][0]
    result = agents[node_name].invoke(input=question)
    state["messages"].append(result)
    return state

def proxmox_router(state: ProxmoxTeamState):
    next_worker = state["next"]
    print(f"proxmox_router: Current state: {state}")
    if next_worker in [node["name"] for node in proxmox_nodes]:
        return next_worker
    return "end"

proxmox_graph = StateGraph(ProxmoxTeamState)
for node in proxmox_nodes:
    proxmox_graph.add_node(node["name"], lambda state, node_name=node["name"]: Worker_node(state, node_name))
    proxmox_graph.add_edge(node["name"], END)

proxmox_graph.add_node("supervisor", supervisor)

node_edges = {node["name"]: node["name"] for node in proxmox_nodes}
node_edges["end"] = END

proxmox_graph.add_conditional_edges(
    "supervisor",
    proxmox_router,
    node_edges,
)

proxmox_graph.add_edge(START, "supervisor")
compiled_graph = proxmox_graph.compile()


# Define Pydantic model for request body
class QuestionRequest(BaseModel):
    question: str

def inp(question: str) -> dict:
    return {"messages": [question] }


def out(state: ProxmoxTeamState)  :
    print("out")
    return state["messages"][-1]["output"]

def out_playground(state: ProxmoxTeamState)  :
    print("out")
    return state[1][state[0]["supervisor"]["next"]]["messages"][-1]["output"]  


final_compiled_graph = RunnableLambda(inp) | compiled_graph | RunnableLambda(out)
final_compiled_graph_playground = RunnableLambda(inp) | compiled_graph | RunnableLambda(out_playground)



class Settings(BaseSettings):
    app_name: str = "proxmox"


settings = Settings()

# Initialize FastAPI app
app = FastAPI()

# Load environment variables
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
allowed_methods = os.getenv("ALLOWED_METHODS", "GET,POST").split(",")

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=allowed_methods,
    allow_headers=["*"],
)

# Add your main routes
add_routes(app, final_compiled_graph_playground, path="/pve")
add_routes(app, final_compiled_graph)
add_routes(app, compiled_graph , path="/without_runnables")


# Define the router and redirection
router = APIRouter()

@router.api_route("/playground/", methods=["GET", "POST"], include_in_schema=False)
async def redirect_to_invoke():
    return RedirectResponse(url="/invoke")

# Include the router in the app
app.include_router(router)

fastapi_host = os.getenv("FASTAPI_HOST", "localhost")
fastapi_port = int(os.getenv("FASTAPI_PORT"))

async def print_messages():
    async for message in compiled_graph.astream({
            "messages": ["list Vms on node 'Proxmox-Node-HCM'"],
            "next": None,
            "team_members": []
        }):
        print(message)
 
if __name__ == "__main__":
    #asyncio.run(print_messages())

    import uvicorn
    uvicorn.run(app, host=fastapi_host, port=fastapi_port)