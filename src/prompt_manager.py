import re
import json

GET_FUNCTION_SEQ = '''

Assume you are an API agent. 

Given a list of API functions and a user query, determine the chain of function 
calls you will have to make to answer the query. 

1. For each API call, also determine the inputs required to call the function API.
2. For each chain of function execution, provide a reason. 
3. Provide EACH function call in ONE line as xml dictionary with <result> tag containing three fields "reason", "function_name", "input_parameters". 

List of most relevant functions you can use to answer the query are:

<functions>
{functions}
</functions>


Step by step process of answering user query "{query}" with above functions is as follows:

'''


GET_ANSWER_FROM_API_CALLS = """

Assume you are an API agent. 

Given a user query and list of responses from different functions, 
determine the output of the user query based on responses of API functions. 

1. Give a reason for your response. 
2. Use all the responses from each function to determine the answer. 
2. Give your response with two fields "reason", "answer". 

The user query is 

<query>
{query}
</query>

Input and Outputs of all functions called to answer user query are:

<function outputs>
{function_outputs}
<function outputs>

Lets try to answer user query, step by step, using above intermediate results is as follows:

"""

def convert_llm_response_to_api_input(response):
    api_calls = []
    result = r'<result>.*?</result>'
    function_name='<function_name>'
    input_parameters = "<input_parameters>"
    #function_name = r'<function_name>(.*?)<\/function_name>'
    #input_parameters = r'<input_parameters>(.*?)</input_parameters>'
    
    match = re.findall(result, response.replace('\n',' '))
    for entry in match:
        if 'input_parameters' in entry and 'function_name' in entry:
            api_calls.append({'function_name': entry[entry.find(function_name)+len(function_name):entry.rfind('</func')], 
            "input_parameters":  entry[entry.find(input_parameters)+len(input_parameters):entry.rfind('</inp')]})
    print("\n\n------ We have to make following function calls ------\n\n\n ", api_calls)
    return api_calls