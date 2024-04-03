import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from conversation_manager import initialize_bedrock, ConversationAgent
from data_processing import APISpecIndex
from langchain.callbacks import StreamlitCallbackHandler
import utils


def display_msg(msg, author):
	st.session_state.messages.append({"role": author, "content": msg})
	st.chat_message(author).write(msg)



st.set_page_config(page_title="Tool Assist")
st.header('Get answers to your HR, CRM, Marketing questions')
st.write('Equipped with several APIs, our system will try to answer your complex questions ')


class ChatUI:

	conversation_agent = None

    def __init__(self, host_url, index_name, embedding_model):
        self.conversation_agent = ConversationAgent(host_url, index_name, 
        	embedding_model)

    @utils.enable_chat_history
    def main(self):
        user_query = st.chat_input(placeholder="Input query")
        if user_query:
            display_msg(user_query, 'user')
            with st.chat_message("assistant"):
                st_cb = StreamHandler(st.empty())
                response = self.conversation_agent.run_query(user_query, callbacks=[st_cb])
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.write(response)


if __name__ == "__main__":
    obj = ChatUI('qia3iowywamezen9p0mk.us-east-1.aoss.amazonaws.com',
    			  args.index_name, "BAAI/bge-base-en-v1.5")
    obj.main()
