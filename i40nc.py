import os

from sklearn.preprocessing import StandardScaler

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
    import os
    import pandas as pd
    import mysql.connector
    import plotly.graph_objects as go
    import streamlit as st
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    import time
    import joblib

    # Initialize the Slack client with your Bot User OAuth Token
    client = WebClient(token='xoxb-7628163592884-7628178233924-pnVLhkyUg5eustQB0sEiU3vt')


    # Function to send an alert to Slack
    def send_slack_alert(message):
        try:
            response = client.chat_postMessage(
                channel='#alert-system',
                text=message
            )
            assert response["message"]["text"] == message

        except SlackApiError as e:
            print(f"Error posting message to Slack: {e.response['error']}")


    # Function to load the selected model and scaler
    def load_model(model_name, model_dir):
        model_path = os.path.join(model_dir, model_name)
        with open(model_path, 'rb') as file:
            models = joblib.load(file)
        return models


    # Function to connect to the database
    def connect_to_db():
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="i40nc"
        )


    # Function to fetch all data from the machine_resources_latest table
    def fetch_all_data():
        db = connect_to_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT Time_Stamp, Comp_Air_Totalized, Water_Totalized, kWh_actual_with_sim FROM machine_resources_latest ORDER BY Time_Stamp")
        data = cursor.fetchall()
        db.close()
        return pd.DataFrame(data,
                            columns=['Time_Stamp', 'Comp_Air_Totalized', 'Water_Totalized', 'kWh_actual_with_sim'])


    # Function to fetch new data based on the latest timestamp
    def fetch_new_data(last_timestamp):
        db = connect_to_db()
        cursor = db.cursor()
        query = "SELECT Time_Stamp, Comp_Air_Totalized, Water_Totalized, kWh_actual_with_sim FROM machine_resources_latest WHERE Time_Stamp > %s ORDER BY Time_Stamp"
        cursor.execute(query, (last_timestamp,))
        data = cursor.fetchall()
        db.close()
        return pd.DataFrame(data,
                            columns=['Time_Stamp', 'Comp_Air_Totalized', 'Water_Totalized', 'kWh_actual_with_sim'])


    # Cache the plot creation function
    @st.cache_data(show_spinner=False)
    def create_plot(all_data, row):
        fig = go.Figure()

        # Add normal data points
        normal_data = all_data[(all_data['energy_anomalies'] == 0) &
                               (all_data['air_anomalies'] == 0) &
                               (all_data['water_anomalies'] == 0)]
        fig.add_trace(go.Scatter3d(
            x=normal_data['Comp_Air_Totalized'],
            y=normal_data['Water_Totalized'],
            z=normal_data['kWh_actual_with_sim'],
            mode='markers',
            marker=dict(
                size=4,
                color='blue',
                opacity=0.5
            ),
            name='Normal'
        ))

        # Add anomaly data point
        fig.add_trace(go.Scatter3d(
            x=[row['Comp_Air_Totalized']],
            y=[row['Water_Totalized']],
            z=[row['kWh_actual_with_sim']],
            mode='markers',
            marker=dict(
                size=7,
                color='red',
                opacity=0.8
            ),
            name='Anomaly'
        ))

        fig.update_layout(
            title='3D Scatter Plot of Detected Anomalies',
            scene=dict(
                xaxis_title='Compressed Air Totalized',
                yaxis_title='Water Totalized',
                zaxis_title='Energy Consumption (kWh)'
            ),
            margin=dict(l=0, r=0, b=0, t=40),
            legend=dict(
                x=0.1,
                y=0.9
            )
        )
        return fig


    # Streamlit app
    def main():
        st.title("Anomaly Detection")

        model_dir = 'C:/School/Poly/MP/mp/i40nc/i40nervecentre/models/'

        # Initialize session state for selected anomaly and last timestamp
        if 'selected_anomaly' not in st.session_state:
            st.session_state.selected_anomaly = None
        if 'last_timestamp' not in st.session_state:
            st.session_state.last_timestamp = None
        if 'stop_signal' not in st.session_state:
            st.session_state.stop_signal = False

        # Real-time monitoring with 2D line charts
        st.header("Real-Time Monitoring")
        all_data = fetch_all_data()

        if all_data.empty:
            st.write("No data available in the database.")
            return

        # Set the last processed timestamp
        st.session_state.last_timestamp = all_data['Time_Stamp'].max()

        # Create 2D line plots for energy, air, and water consumption over time
        fig_energy = go.Figure()
        fig_air = go.Figure()
        fig_water = go.Figure()

        fig_energy.add_trace(go.Scatter(
            x=all_data['Time_Stamp'],
            y=all_data['kWh_actual_with_sim'],
            mode='lines',
            line=dict(color='blue'),
            name='Energy Consumption (kW)'
        ))

        fig_air.add_trace(go.Scatter(
            x=all_data['Time_Stamp'],
            y=all_data['Comp_Air_Totalized'],
            mode='lines',
            line=dict(color='green'),
            name='Air Consumption'
        ))

        fig_water.add_trace(go.Scatter(
            x=all_data['Time_Stamp'],
            y=all_data['Water_Totalized'],
            mode='lines',
            line=dict(color='orange'),
            name='Water Consumption'
        ))

        fig_energy.update_layout(
            title="Energy Consumption Over Time",
            xaxis_title="Timestamp",
            yaxis_title="Energy (kW)",
            xaxis=dict(rangeslider=dict(visible=True)),
        )

        fig_air.update_layout(
            title="Air Consumption Over Time",
            xaxis_title="Timestamp",
            yaxis_title="Air Consumption",
            xaxis=dict(rangeslider=dict(visible=True)),
        )

        fig_water.update_layout(
            title="Water Consumption Over Time",
            xaxis_title="Timestamp",
            yaxis_title="Water Consumption",
            xaxis=dict(rangeslider=dict(visible=True)),
        )

        st.plotly_chart(fig_energy)
        st.plotly_chart(fig_air)
        st.plotly_chart(fig_water)

        # Model selection with "None" as the first option
        st.header("Anomaly Detection")
        model_options = ["None"] + os.listdir(model_dir)
        model_name = st.selectbox('Select Model', model_options)

        start_button = st.button('Start Anomaly Detection')
        stop_button = st.button('Stop Anomaly Detection')

        if start_button:
            if model_name != "None":
                models = load_model(model_name, model_dir)
                model_energy = models['model_energy']
                model_air = models['model_air']
                model_water = models['model_water']
                scaler = models['scaler']

                while not st.session_state.stop_signal:
                    # Fetch all data from the database
                    all_data = fetch_all_data()

                    # Calculate the rate of change for energy, air, and water consumption
                    all_data['Energy_Rate_Change'] = all_data['kWh_actual_with_sim'].diff().fillna(0)
                    all_data['Air_Rate_Change'] = all_data['Comp_Air_Totalized'].diff().fillna(0)
                    all_data['Water_Rate_Change'] = all_data['Water_Totalized'].diff().fillna(0)

                    # Apply the saved scaler for normalization
                    all_data[['Energy_Rate_Change', 'Air_Rate_Change', 'Water_Rate_Change']] = scaler.transform(
                        all_data[['Energy_Rate_Change', 'Air_Rate_Change', 'Water_Rate_Change']]
                    )

                    # Detect anomalies using the energy, air, and water models
                    all_data['energy_anomalies'] = model_energy.predict(all_data[['Energy_Rate_Change']])
                    all_data['energy_anomalies'] = all_data['energy_anomalies'].map({1: 0, -1: 1})

                    all_data['air_anomalies'] = model_air.predict(all_data[['Air_Rate_Change']])
                    all_data['air_anomalies'] = all_data['air_anomalies'].map({1: 0, -1: 1})

                    all_data['water_anomalies'] = model_water.predict(all_data[['Water_Rate_Change']])
                    all_data['water_anomalies'] = all_data['water_anomalies'].map({1: 0, -1: 1})

                    # Filter to only rows with anomalies in energy, air, or water
                    detected_anomalies = all_data[(all_data['energy_anomalies'] == 1) |
                                                  (all_data['air_anomalies'] == 1) |
                                                  (all_data['water_anomalies'] == 1)]

                    if detected_anomalies.empty:
                        st.write("No anomalies detected.")
                    else:
                        st.write("Click on an anomaly to view details:")
                        for _, row in detected_anomalies.iterrows():
                            message = f"Anomaly detected at {row['Time_Stamp']}: "
                            if row['energy_anomalies'] == 1:
                                message += "Increased energy consumption"
                            if row['air_anomalies'] == 1:
                                message += " Abnormal air consumption"
                            if row['water_anomalies'] == 1:
                                message += " Abnormal water consumption"

                            # Send anomaly alert to Slack
                            send_slack_alert(message)

                            # Cache and log the plot
                            with st.expander(message):
                                plot = create_plot(all_data, row)
                                st.plotly_chart(plot)

                            # Add a delay to ensure the plot is rendered properly
                            time.sleep(5)

                    # After processing, wait for new data every 5 seconds
                    st.write("Machine is idling...")  # Print once when machine starts idling
                    while not st.session_state.stop_signal:
                        new_data = fetch_new_data(st.session_state.last_timestamp)
                        if not new_data.empty:
                            st.write(f"New data detected, processing {len(new_data)} new records.")
                            st.session_state.last_timestamp = new_data['Time_Stamp'].max()
                            break  # Process new data and detect anomalies

                        time.sleep(5)  # Wait before checking again

                    if stop_button:
                        st.session_state.stop_signal = True
                        st.write("Anomaly detection stopped.")


    if __name__ == '__main__':
        main()

with st_tab:
    st.write("(Scope5)Put your smart tools page here! All the best!(generate pdf report/ email report/ slack notification)")



















