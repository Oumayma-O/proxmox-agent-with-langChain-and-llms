__author__ = "Wathek Beji"
__maintainer__ = "Wathek Beji"
__email__ = "w.beji@coral-io.fr"
__status__ = "Prototype"

from langchain_core.output_parsers import StrOutputParser 
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from config import ConfigData
import json
import pymongo
from operator import itemgetter
import dirtyjson

# Model instantiation
llm = ChatOllama(model="llama3:instruct", temperature=0)
# Configuration
document_schema = ConfigData.DOCUMENT_SCHEMA
schema_description = ConfigData.SCHEMA_DESCRIPTION 

client = pymongo.MongoClient(ConfigData.MONGO_DB_URI)
db = client[ConfigData.DB_NAME]
collection_name = db[ConfigData.COLLECTION_NAME]

route_chain = (
    PromptTemplate.from_template(
        """Given the user question below, classify it as either being about `Computing` or `Other`.

Do not respond with more than one word.

<question>
{input}
</question>

Classification:"""
    )
    | llm 
    | StrOutputParser()
)

query_creation_template= """
    You are an expert in crafting MongoDB aggregation pipeline queries. 
    Given the document schema and schema description in a specific format, 
    Your task is to read the user question, and create a syntactically correct MongoDb aggregation pipeline.

    Document schema: """ + document_schema + """
    Schema Description: """ + schema_description + """

    The output expression properties  such as $match, $count, $avg MUST be enclosed in double quotes. 
    You have to just return the pipeline expression nothing else. Don't return any additional text with the pipeline.
    Keep the response to only one line.
    
    
    Question: {input}
"""

query_creation_prompt = PromptTemplate(
    template=query_creation_template,
    input_variables=["input", "document_schema", "schema_description"]
)

answer_template = """
    Given the following user question, corresponding MongoDB Aggregation pipeline , and MongoDB pipeline execution result, answer the user question.
    Do not explain your answer.
    Question: {input}
    Mongodb aggregation pipeline: {query}
    Mongodb pipeline execution Result: {result}
"""

answer_prompt = PromptTemplate(
    template=answer_template,
    input_variables=["question", "query", "result"]
)


# Custom function that executes queries against a MongoDB database
def execute_pipeline(raw_pipeline: str):
    print(f"DEBUG: RAW: {raw_pipeline}")
    pipeline = dirtyjson.loads(raw_pipeline)
    print(f"DEBUG FIX: {json.dumps(pipeline)}")
    results = collection_name.aggregate(pipeline)
    answer = [result for result in results]
    print(f"Answer: {answer}")
    return answer 


execute_query = RunnableLambda(execute_pipeline)
   # Main Execution Chain
write_query = (
    query_creation_prompt 
    | llm 
    | StrOutputParser() 
)
chain = (
    RunnablePassthrough.assign(query=write_query).assign(
        result=itemgetter("query") | execute_query
    )
    | answer_prompt
    | llm
    | StrOutputParser()
)

general_chain = PromptTemplate.from_template(
    """Respond to the following question:

Question: {input}
Answer:"""
) | llm | StrOutputParser() 

def route(info):
    if "computing" in info["topic"].lower():
        print(f"USING: info['topic'].lower()")
        return chain 
    else:
        print(f"USING: {info['topic'].lower()}")
        return general_chain

full_chain = {"topic": route_chain, "input": lambda x: x["input"]} | RunnableLambda(
    route
)

while True:
    try:
        question = input("question > ")
        for chunk in full_chain.stream({"input": f"{question}"}):
            print(chunk, end='', flush=True)

    except (EOFError, KeyboardInterrupt):
        break
    print("\n") 
