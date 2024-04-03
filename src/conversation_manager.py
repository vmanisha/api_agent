import json
import boto3
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ChatMessageHistory
from langchain.chains import ConversationChain
from prompt_manager import GET_FUNCTION_SEQ, GET_ANSWER_FROM_API_CALLS, convert_llm_response_to_api_input
from api_call_manager import make_api_call 
from data_processing import APISpecIndex
from sentence_transformers import SentenceTransformer
from langchain_community.chat_models import BedrockChat
from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate

def initialize_bedrock():
    _SESSION = boto3.Session()
    bedrock = _SESSION.client(service_name='bedrock-runtime', region_name='us-east-1')
    return bedrock


class ConversationAgent():

    # sequence of input / outputs
    history=None
    search_index = None
    embedding_model = None
    llm = None
    function_getter_chain= None


    def __init__(self, host_url, index_name, embedding_model):
        self.search_index = APISpecIndex(host_url, index_name)
        self.embedding_model = SentenceTransformer(embedding_model)
        self.history =  ChatMessageHistory()
        self.llm =  BedrockChat( model_id="anthropic.claude-3-sonnet-20240229-v1:0",
                 model_kwargs={'temperature': 0.0})

        self.function_getter_chain = LLMChain(llm=self.llm, prompt=PromptTemplate(
            input_variables=["functions","query"], template=GET_FUNCTION_SEQ
            ))
        self.ans_from_API_chain = LLMChain(llm=self.llm, prompt=PromptTemplate(
            input_variables=["query", "function_outputs"], 
            template=GET_ANSWER_FROM_API_CALLS
            ))

    def find_and_execute_rel_functions(self, user_query):
        # run the search
        valid_functions_for_query = self.search_index.search_index(user_query, 
            self.embedding_model)
        
        
        # get response from the LLM. 
        functions = self.function_getter_chain.invoke({'functions': str(valid_functions_for_query), 
            "query":user_query})
        
        print('API Functions selected by Language model: ', functions['text'])
        api_requests = convert_llm_response_to_api_input(functions['text'])
        
        
        #responses = [{'function_name':'/employees','response':['employee 1', 'employee 2', 'employee 3']}]
        responses = [{'function_name':'/time-off-balances','response':'34'}]
        '''
        # this wont work without actual API call

        if len(api_requests) > 0:
            for entry in api_requests: 
                response = make_api_call(entry['function_name'], 
                    entry['input_parameters'], "dummy_url")
                responses.append({'function_name':entry['function_name'], 'response': response})
        '''
        
        return responses    


    def run_query(self, user_query, callbacks):

        self.history.add_user_message(user_query)
        function_outputs = self.find_and_execute_rel_functions(user_query)
        if len(function_outputs) > 0:
            model_response = self.ans_from_API_chain.invoke(
                {'function_outputs': function_outputs, 
                "query":user_query}, callbacks=callbacks)
            
            print('\n\n------ Final answer  ------\n\n\n', model_response['text'])
            
            self.history.add_ai_message(model_response['text'])


