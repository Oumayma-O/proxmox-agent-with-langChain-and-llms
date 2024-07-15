from langchain.prompts.prompt import PromptTemplate

API_REQUEST_PROMPT_TEMPLATE = """
Given the following API Documentation: {api_docs}
Your task is to construct the most efficient API URL to answer 
the user's question, ensuring the 
call is optimized to include only necessary information.
If a parameter is not required and does not have a
default value, do NOT include it in the API URL, unless you think
it's relevant to the user's question.
You MUST extract the API URL, request METHOD and generate the BODY data in JSON format
according to the user question if necessary.
Only include parameters and BODY data keys that are specified in the user input. Do not include fields in the body request that weren't mentioned by the user.
The parameters' names and BODY data keys MUST be obtained from the provided context.
Do NOT make up parameters' names.
The BODY data can be an empty JSON.
Output the API URL, METHOD and BODY. Join them with `|`. DO NOT GIVE ANY EXPLANATION.

Question: {question}

Output:
"""

API_REQUEST_PROMPT = PromptTemplate(
    input_variables=["api_docs", "question"],
    template=API_REQUEST_PROMPT_TEMPLATE,
)

API_RESPONSE_PROMPT_TEMPLATE = """
With the following official API Documentation: {api_docs} 
and the specific user question: {question} in mind,
and given this API URL: {api_url} for querying, here is the 
response from the API: {api_response}. 
Do NOT include technical details like response format.
Do NOT include any thoughts or internal processes.
You MUST provide a clear, relevant and concise answer.

Response:
"""

API_RESPONSE_PROMPT = PromptTemplate(
    input_variables=["api_docs", "question", "api_url", "api_response"],
    template=API_RESPONSE_PROMPT_TEMPLATE,
)