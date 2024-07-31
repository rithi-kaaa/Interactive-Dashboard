import os
from apikey import apikey
import streamlit as st
from i40ncAssistant import i40NCAssistant
import yaml
from sqlalchemy import create_engine
import pymysql
import pandas as pd
from openai import OpenAI
import mysql.connector
from mysql.connector import Error

## Setup
os.environ["OPENAI_API_KEY"] = apikey
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
    db_tab, llm_tab = st.tabs(["Database Queries using OpenAI", "General ChatGT"])
    with db_tab:
        # Function to read the YAML file and get the database config
        def load_db_config(file_path):
            with open(file_path, 'r') as file:
                config = yaml.load(file, Loader=yaml.FullLoader)
            mock_config = config["Mock-database"]
            return mock_config


        # Function to connect to the MySQL database
        def create_connection(config):
            connection = None
            try:
                connection = mysql.connector.connect(
                    host=config['uri'],
                    user=config['user'],
                    passwd=config['pwd'],
                    database=config['dbname'],
                    port=config['port']
                )
                st.success("Connection to MySQL DB successful")
            except Error as e:
                st.error(f"The error '{e}' occurred")
            return connection

        # Function to get table names from the database
        def get_tables(connection):
            query = "SHOW TABLES"
            cursor = connection.cursor()
            tables = []
            try:
                cursor.execute(query)
                tables = cursor.fetchall()
            except Error as e:
                st.error(f"The error '{e}' occurred")
            return tables

        # Load database configuration from YAML file
        config_file_path = os.path.join(wd, "i40ncConfig.yml")
        mock_config = load_db_config(config_file_path)

        # Button to connect to the database
        if st.button("Connect to Database"):
            connection = create_connection(mock_config)
            if connection:
                st.session_state.connection = connection

        # If connected, retrieve and display the number and names of tables
        if "connection" in st.session_state and st.session_state.connection:
            tables = get_tables(st.session_state.connection)
            if tables:
                table_names = [table[0] for table in tables]
                st.write(f"Number of tables: {len(table_names)}")
                st.write("Table names:")
                for table_name in table_names:
                    st.write(f"- {table_name}")

    with llm_tab:
        st.title("NerCy Chatbot")

    # ChatGPT Setup
    #client = OpenAI(api_key="sk-proj-acnvG3rYugMz7GYan7oYT3BlbkFJAJtssJMo9iJQ0rvk245i")

        # Set a default model
        if "openai_model" not in st.session_state:
            st.session_state["openai_model"] = "gpt-3.5-turbo"

        # Function to display chat messages
        def display_messages():
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])


        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages from history on app rerun
        display_messages()

        if prompt := st.chat_input("Please type your questions here!"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                 ],
                stream=False,  # Set stream to False to get the full response at once
                )
            # Extract the assistant's response content
            assistant_message = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": assistant_message})
            st.rerun()  # Rerun the script to clear the displayed messages

        # Clear chat button
        if st.button("Clear Chat"):
            st.session_state.messages = []

with sd_tab:
    st.write("(Scope4)Put your smart detect page here! All the best!(abrnomally detection)")

with st_tab:
    st.write("(Scope5)Put your smart tools page here! All the best!(generate pdf report/ email report/ slack notification)")



















