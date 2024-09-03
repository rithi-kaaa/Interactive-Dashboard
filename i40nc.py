import os
from apikey import apikey
import streamlit as st
from i40ncAssistant import i40NCAssistant
import yaml
from sqlalchemy import create_engine
import pymysql
import pandas as pd
from openai import OpenAI
import requests

## Setup
#os.environ["OPENAI_API_KEY"] = "sk-proj-acnvG3rYugMz7GYan7oYT3BlbkFJAJtssJMo9iJQ0rvk245i"
wd = os.getcwd()
with open(wd+"\\i40ncConfig.yml") as cfgfile:
    config = yaml.load(cfgfile, Loader=yaml.FullLoader)
    dbConfig = config["Mysql-i40nc"]

    database = dbConfig["dbname"]
    user = dbConfig["user"]
    pwd = dbConfig["pwd"]
    host = dbConfig["uri"]
    port = dbConfig["port"]

    i40db = create_engine('mysql+pymysql://' + user + ':' + pwd + '@' + host + ':' + str(port) + '/' + database , echo=False)
    #Connection and data capturing tested ok
    #cityDF = pd.read_sql('SELECT * FROM city', i40db)
    #print(cityDF)


st.title("I4.0 Smart Factory Nerve Centre")
## Session Setup/initialisation
if 'nca' not in st.session_state:
    st.session_state["nca"] = i40NCAssistant(i40db, config)
if 'uiStates' not in st.session_state:
    st.session_state['uiStates'] = {}

## UI Setup
nca = st.session_state["nca"]
states = st.session_state['uiStates']
pf_tab, pp_tab, an_tab, sd_tab, st_tab= st.tabs(["Production Floor", "Past Performance", "Ask NerCy", "Smart Detect","Smart Tools"])


with pf_tab:
    st.write("(Scope1)Put your production floor overview page here! All the best!(OEE/ carbon footprint)")

with pp_tab:
    st.write("(Scope2)Put your past performance page here! All the best!(historical page)")

with an_tab:
    st.title("NerCy Chatbot")

    # ChatGPT Setup
    client = OpenAI(api_key="sk-proj-acnvG3rYugMz7GYan7oYT3BlbkFJAJtssJMo9iJQ0rvk245i")

    # Function to display chat messages
    def display_messages():
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Function to send prompts to AnythingLLM
    def post_request(link, data_info, headers=None):
        try:
            reply = requests.post(link, json=data_info, headers=headers)
            reply.raise_for_status()  # Raise an exception for HTTP errors
            return reply.json()  # Assuming the response is in JSON format
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return None

    # Initialize chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {'role': 'assistant', 'content': 'Hi, I am NerCy the chatbot built to answer any questions you may have! I '
                                             'can answer general questions or use an agent to access tools such as the '
                                             'database and the internet to answer more complicated questions. However, '
                                             'in order to access the agent to use the tools mentions, please add @agent'
                                             ' in front of the prompt. A few examples are provided in the default '
                                             'prompts. We apologize for any inconvenience caused.'}
        ]

    if 'selected_prompt' not in st.session_state:
        st.session_state.selected_prompt = ''

    # Display chat history on app rerun in container
    with st.container(height=500):
        display_messages()

    additional_context = ('Check the following prompt to see if it requires the use of an agent and if it does '
                          'return True. Do not return any other words other then True if it does require an agent. '
                          'If it does not require an agent respond to the best of your ability without using an '
                          'agent. Prompt: ')

    assistant_message_agent = 'Null'

    # Capture user input
    prompt = st.text_input("Please type your questions here!", value=st.session_state.selected_prompt)

    # List of default prompts with custom configurations
    default_prompts = [
        {'label': 'Use Case & Purpose', 'prompt': 'What is the use case and purpose of this chatbot?'},
        {'label': 'Database Tables Available', 'prompt': '@agent Tell me the tables present in the database?'},
        {'label': 'Slack Info', 'prompt': '@agent What is Slack and provide me some links for additional information?'}
    ]

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.selected_prompt = ''
        url_3 = 'http://localhost:3001/api/v1/workspace/major-project/chat'
        data_3 = {'message': additional_context + prompt, 'mode': 'chat'}
        headers_3 = {'Authorization': 'Bearer K8QE7DN-5AVMERW-PVFP5N7-9HRMVZ7', 'Accept': 'application/json'}
        response_data_3 = post_request(url_3, data_3, headers_3)
        assistant_message = response_data_3['textResponse']
        if assistant_message == 'True':
            data_agent = {'message': '@agent Using the most suitable function complete the following prompt: '
                          + prompt, 'mode': 'chat'}
            response_data_agent = post_request(url_3, data_agent, headers_3)
            assistant_message_agent = response_data_agent['textResponse']
        if assistant_message_agent != 'Null':
            st.session_state.messages.append({"role": "assistant", "content": assistant_message_agent})
        else:
            st.session_state.messages.append({"role": "assistant", "content": assistant_message})
        st.rerun()  # Rerun the script to display messages

    # Create a horizontal layout for the buttons
    cols = st.columns(len(default_prompts))

    # Buttons to apply the selected default prompt to the chat input
    for i, prompt_info in enumerate(default_prompts):
        with cols[i]:  # Place each button in its respective column
            if st.button(prompt_info["label"]):
                st.session_state.selected_prompt = prompt_info['prompt']
                st.rerun()


with sd_tab:
    st.write("(Scope4)Put your smart detect page here! All the best!(abrnomally detection)")

with st_tab:
    st.write("(Scope5)Put your smart tools page here! All the best!(generate pdf report/ email report/ slack notification)")



















