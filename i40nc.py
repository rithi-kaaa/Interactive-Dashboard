import os
from apikey import apikey
import streamlit as st
from i40ncAssistant import i40NCAssistant
import yaml
from sqlalchemy import create_engine
import pymysql
import pandas as pd


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
    st.text_area("create programing here")

with pp_tab:
    st.write("(Scope2)Put your past performance page here! All the best!(historical page)")

with an_tab:
    st.write("(Scope3)Put your Ask Nercy page here! All the best!(LLC chatbot)")

with sd_tab:
    st.write("(Scope4)Put your smart detect page here! All the best!(abrnomally detection)")

with st_tab:
    st.write("(Scope5)Put your smart tools page here! All the best!(generate pdf report/ email report/ slack notification)")



















