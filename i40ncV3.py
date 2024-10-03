import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objs as go
from fpdf import FPDF
from sklearn.neighbors import LocalOutlierFactor
from sqlalchemy import create_engine
import yaml
import matplotlib.ticker as ticker
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import time
import joblib
from sklearn.ensemble import IsolationForest
import streamlit.components.v1 as components
import requests
import plotly.express as px
import numpy as np
import mysql.connector
from apikey import apikey
from i40ncAssistant import i40NCAssistant
import pymysql
import streamlit as st
import schedule
import time
from datetime import datetime
# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from email.mime.base import MIMEBase
# from email import encoders
import streamlit.components.v1 as components
import plotly.io as pio

# Load database configuration from a YAML file
with open("i40ncConfig.yml") as cfgfile:
    config = yaml.load(cfgfile, Loader=yaml.FullLoader)
    dbConfig = config["Mysql-i40nc"]
    database = dbConfig["dbname"]
    user = dbConfig["user"]
    pwd = dbConfig["pwd"]
    host = dbConfig["uri"]
    port = dbConfig["port"]

    aLLMConfig = config["AnythingLLM"]
    gmailConfig = config["Gmail"]

# Create a database connection engine
i40db = create_engine(f'mysql+pymysql://{user}:{pwd}@{host}:{port}/{database}', echo=False)

# Streamlit app setup
st.set_page_config(page_title="I4.0 Smart Factory Nerve Centre", layout="wide")

# Initialize session state variables
if 'selected_prompt' not in st.session_state:
    st.session_state['selected_prompt'] = ''

if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {'role': 'assistant', 'content': 'Hi, I am NerCy the chatbot built to answer any questions you may have! I '
                                         'can answer general questions or use an agent to access tools such as the '
                                         'database and the internet to answer more complicated questions. However, '
                                         'in order to access the agent to use the tools mentioned, please add @agent'
                                         ' in front of the prompt. A few examples are provided in the default '
                                         'prompts. We apologize for any inconvenience caused.'}
    ]

# Custom CSS for centering the tabs and making them wider
st.markdown("""
    <style>
        .centered-title {
            display: flex;
            justify-content: center;
            align-items: center;
            text-align: center;
            margin-bottom: -10px;
        }
        .stTabs [data-baseweb="tab-list"] {
            justify-content: space-evenly;
        }
        .stTabs [role="tab"] {
            flex-grow: 1;
            padding: 16px;
        }
        .date-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .date-container div {
            margin-right: 20px;
        }
    </style>
    <div class="centered-title">
        <h1>I4.0 Smart Factory Nerve Centre</h1>
    </div>
    """, unsafe_allow_html=True)

# Tabs with icons for different sections
tab_titles = [
    "🛠️ Production Floor",
    "📊 Past Performance",
    "🤖 Ask NerCy",
    "🔍 Smart Detect",
    "🔧 Smart Tools"
]
tabs = st.tabs(tab_titles)

# ======= Production Floor Tab =======
with tabs[0]:
    # Define thresholds for real-time alerts
    THRESHOLDS = {
        'Availability': 90,  # Below 90 triggers an alert
        'Performance': 92,   # Below 92 triggers an alert
        'Quality': 95,       # Below 95 triggers an alert
        'OEE': 88            # Below 88 triggers an alert
    }

    # Get the latest date in the data for OEE
    query_latest_date = f"SELECT MAX(DATE(Time_Stamp)) AS latest_date FROM {database}.oee_log3"
    latest_date = pd.read_sql(query_latest_date, i40db)['latest_date'][0]

    # Date selector
    selected_date = st.date_input("Select Date:", latest_date)

    # Fetch OEE data for the selected date
    query_oee = f"""
           SELECT * FROM {database}.oee_log3
           WHERE DATE(Time_Stamp) = '{selected_date}'
           """
    oee_data = pd.read_sql(query_oee, i40db)

    if oee_data.empty:
        st.error("No OEE data available for the selected date.")
        st.stop()

    # Fetch CO2 data for the selected day using the Time_Stamp column
    query_co2 = f"""
           SELECT Time_Stamp, CO2_Comp_Air, CO2_Water, CO2_EEnergy 
           FROM {database}.machine_resources_co2
           WHERE DATE(Time_Stamp) = '{selected_date}'
           """
    co2_data = pd.read_sql(query_co2, i40db)
    if not co2_data.empty:
        co2_data['Time_Stamp'] = pd.to_datetime(co2_data['Time_Stamp'])
    else:
        st.error("No CO2 data available for the selected date.")
        st.stop()

    # Fetch OEE data for visualization over time on the two available dates
    query_oee_time = f"""
            SELECT
                Time_Stamp,
                OEE_Availability,
                OEE_Performance,
                OEE_Quality,
                (OEE_Availability * OEE_Performance * OEE_Quality) / 10000 AS OEE
            FROM
                {database}.oee_log3
            WHERE
                DATE(Time_Stamp) IN ('2024-08-29', '2024-09-02')
            ORDER BY
                Time_Stamp
            """
    df_oee_time = pd.read_sql(query_oee_time, i40db)
    df_oee_time['Time_Stamp'] = pd.to_datetime(df_oee_time['Time_Stamp'])

    if df_oee_time.empty:
        st.error("No OEE data available for the specified dates.")
    else:
        # Melt the dataframe for line chart plotting
        df_melted = df_oee_time.melt(id_vars=['Time_Stamp'],
                                     value_vars=['OEE', 'OEE_Availability', 'OEE_Performance', 'OEE_Quality'],
                                     var_name='Metric', value_name='Value')


    # Set values based on the data
    availability = oee_data['OEE_Availability'].mean()
    performance = oee_data['OEE_Performance'].mean()
    quality = oee_data['OEE_Quality'].mean()
    oee = (availability * performance * quality) / 10000
    machine_id = "01"
    machine_name = "salineproduction"


    # Real-time alerts based on thresholds
    def check_thresholds(data, thresholds):
        if data['Availability'] < thresholds['Availability']:
            st.warning(f"⚠️ Machine availability is critically low. Immediate attention required!)")
        if data['Performance'] < thresholds['Performance']:
            st.warning(f"⚠️ Machine performance is below target. Investigate for potential delays!)")
        if data['Quality'] < thresholds['Quality']:
            st.warning(f"⚠️ Quality issues detected! Reject rate is higher than normal!)")
        if data['OEE'] < thresholds['OEE']:
            st.warning(f"⚠️ Critical alert: OEE is performing below standard. Investigate to avoid downtime!)")


    # Function to create circular gauges using Plotly
    def create_gauge(value, title, goal=95):
        # Defines the color based on the value in relation to the goal
        color = "#34eb4f" if value >= goal else "#eb4034"
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",  # Delta shows difference from the goal
            value=value,
            delta={'reference': goal, 'increasing': {'color': "#34eb4f"}},
            title={'text': title, 'font': {'size': 24}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, goal], 'color': 'lightgray'},
                    {'range': [goal, 100], 'color': 'gray'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': goal
                }
            }
        ))
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
        return fig

    # Layout for Machine Info, Date, and Gauges
    st.markdown("<h2 style='text-align: center;'>OEE and CO2 Monitoring System</h2>", unsafe_allow_html=True)

    st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; margin-top: 20px;">
            <div style="flex: 3; text-align: center;">
                <span style="font-weight: bold;">Machine Information</span>
                <br/>
                <span style="color: green;">machineID: {machine_id} | machineName: {machine_name}</span>
                <br/>
                <span style="font-weight: bold; color: white;">Date: {selected_date.strftime('%d/%m/%y')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Display real-time alerts for OEE metrics
    oee_data_dict = {
        'Availability': availability,
        'Performance': performance,
        'Quality': quality,
        'OEE': oee
    }
    check_thresholds(oee_data_dict, THRESHOLDS)

    # Layout for the Gauges
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.plotly_chart(create_gauge(availability, "Availability"), use_container_width=True)
    with col2:
        st.plotly_chart(create_gauge(performance, "Performance"), use_container_width=True)
    with col3:
        st.plotly_chart(create_gauge(quality, "Quality"), use_container_width=True)
    with col4:
        st.plotly_chart(create_gauge(oee, "OEE"), use_container_width=True)

    fig = px.line(df_melted, x='Time_Stamp', y='Value', color='Metric',
                  title='OEE, Availability, Performance, and Quality Over Time',
                  labels={"Time_Stamp": "Time", "Value": "Percentage", "Metric": "Metric"},
                  line_dash='Metric')  # Different line styles for each metric

    # Customizing the layout
    fig.update_layout({
        'plot_bgcolor': 'rgba(0,0,0,0)',  # Transparent background
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'title_font': {'size': 24},
        'font': {'family': "Courier New, monospace", 'color': "white", 'size': 18},
        'legend_title_font': {'color': 'cyan'},
        'xaxis': {'tickangle': 45, 'title_standoff': 25},
        'yaxis': {'title': {'standoff': 25}}
    })

    # Customizing lines
    fig.update_traces(line=dict(width=4), marker=dict(size=10, symbol='circle'))

    # Adding a custom annotation
    fig.add_annotation(
        x=df_melted['Time_Stamp'].iloc[-1],
        y=df_melted['Value'].iloc[-1],
        text="Latest Data Point",
        showarrow=True,
        arrowhead=1,
        ax=0,
        ay=-40
    )

    # Show the figure
    st.plotly_chart(fig, use_container_width=True)

    # Bar Charts for Availability and Quality
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Availability Breakdown")
        availability_cols = ['A_stop_duration', 'A_Alarm_Duration', 'A_Idle_Duration', 'A_Manual_Duration', 'A_Run_Duration']
        availability_values = [oee_data[col].sum() for col in availability_cols]
        fig_availability = go.Figure(data=[go.Bar(x=availability_cols, y=availability_values, marker_color='blue')])
        fig_availability.update_layout(
            xaxis_title="Categories",
            yaxis_title="Duration (s)",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_availability, use_container_width=True)

    with col2:
        st.subheader("Quality Breakdown")
        quality_cols = ['Q_No_Of_Bad', 'Q_No_Of_Good']
        quality_values = [oee_data[col].sum() for col in quality_cols]
        fig_quality = go.Figure(data=[go.Bar(x=quality_cols, y=quality_values, marker_color='green')])
        fig_quality.update_layout(
            xaxis_title="Categories",
            yaxis_title="Count",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_quality, use_container_width=True)

    # CO2 Emission & Distribution
    with col1:
        st.subheader("CO2 Emissions Over Time")
        fig_co2_day = go.Figure()
        fig_co2_day.add_trace(go.Scatter(x=co2_data['Time_Stamp'], y=co2_data['CO2_Comp_Air'],
                                         mode='lines+markers', name='CO2 Compressed Air'))
        fig_co2_day.add_trace(go.Scatter(x=co2_data['Time_Stamp'], y=co2_data['CO2_Water'],
                                         mode='lines+markers', name='CO2 Water', yaxis='y2'))
        fig_co2_day.add_trace(go.Scatter(x=co2_data['Time_Stamp'], y=co2_data['CO2_EEnergy'],
                                         mode='lines+markers', name='CO2 Energy', yaxis='y2'))

        fig_co2_day.update_layout(
            xaxis_title='Time',
            yaxis=dict(title='CO2 Compressed Air (kg)', side='left', rangemode='tozero'),
            yaxis2=dict(title='CO2 Water and Energy (kg)', side='right', overlaying='y', rangemode='tozero'),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_co2_day, use_container_width=True)

    with col2:
        st.subheader("CO2 Emissions Distribution")

        # Creating a DataFrame for the emissions
        emission_data = pd.DataFrame({
            'Source': ['Compressed Air', 'Water', 'Energy'],
            'Emissions': [co2_data['CO2_Comp_Air'].sum(), co2_data['CO2_Water'].sum(),
                          co2_data['CO2_EEnergy'].sum()]
        })

        emission_data['Visual_Emissions'] = np.sqrt(emission_data['Emissions'])

        # Generating a pie chart
        pie_fig = go.Figure(data=[go.Pie(
            labels=emission_data['Source'],
            values=emission_data['Visual_Emissions'],
            customdata=emission_data['Emissions'],
            texttemplate="%{label}: (%{percent})",
            hole=0.3,
            insidetextorientation='radial'
        )])

        pie_fig.update_traces(textposition='outside')
        pie_fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))

        st.plotly_chart(pie_fig, use_container_width=True)

    # Day-to-day comparison setup
    st.subheader("Day-to-Day Comparison")

    # Check if reset flag is set, use default values if True
    if 'reset_flag' not in st.session_state:
        st.session_state['reset_flag'] = False

    # Set default dates
    default_date1 = datetime.strptime("29/08/2024", "%d/%m/%Y")
    default_date2 = datetime.strptime("02/09/2024", "%d/%m/%Y")

    # If reset flag is set, use default dates
    if st.session_state['reset_flag']:
        date1 = default_date1
        date2 = default_date2
    else:
        date1 = st.date_input("Select the 1st Date:", value=default_date1, key="first_date")
        date2 = st.date_input("Select the 2nd Date:", value=default_date2, key="second_date")

    # Multi-select for choosing emission types
    selected_emissions = st.multiselect(
        "Choose the Emission Types to Compare:",
        options=['CO2_Comp_Air', 'CO2_Water', 'CO2_EEnergy'],
        default=['CO2_Comp_Air', 'CO2_Water', 'CO2_EEnergy'],
        key='emission_select'
    )

    # Compare button for triggering comparison
    if st.button("Compare", key="compare_dates_button"):
        # Fetch data for the selected dates
        query1 = f"""
            SELECT Time_Stamp, {', '.join(selected_emissions)}
            FROM {database}.machine_resources_co2
            WHERE DATE(Time_Stamp) = '{date1.strftime('%Y-%m-%d')}'
        """
        query2 = f"""
            SELECT Time_Stamp, {', '.join(selected_emissions)}
            FROM {database}.machine_resources_co2
            WHERE DATE(Time_Stamp) = '{date2.strftime('%Y-%m-%d')}'
        """
        co2_data_date1 = pd.read_sql(query1, i40db)
        co2_data_date2 = pd.read_sql(query2, i40db)

        if not co2_data_date1.empty and not co2_data_date2.empty:
            # Plotting both datasets
            fig = go.Figure()
            for emission in selected_emissions:
                fig.add_trace(go.Scatter(
                    x=co2_data_date1['Time_Stamp'], y=co2_data_date1[emission],
                    mode='lines', name=f'{emission} {date1.strftime("%d/%m/%Y")}'
                ))
                fig.add_trace(go.Scatter(
                    x=co2_data_date2['Time_Stamp'], y=co2_data_date2[emission],
                    mode='lines', name=f'{emission} {date2.strftime("%d/%m/%Y")}',
                    line=dict(dash='dot')
                ))
            fig.update_layout(
                title="CO2 Emissions Comparison",
                xaxis_title="Time",
                yaxis_title="Emissions (kg)",
                legend_title="Emission Type",
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("No CO2 data available for the selected dates.")

    # Reset button to reset the dates
    if st.button("Reset", key="reset_button"):
        st.session_state['reset_flag'] = True
        st.experimental_rerun()  # Rerun the script to refresh the app and reinitialize the date inputs

#####################################################

    # Add this CSS for styling
    st.markdown("""
        <style>

        /* Main container for tabs */
        .main .block-container .element-container .stTabs {
            display: flex; /* Using flexbox for equal distribution */
        }

        /* Individual tab styling */
        .main .block-container .element-container .stTabs > div {
            flex: 1; /* Each tab takes equal width */
            text-align: center; /* Center align tab titles */
            font-size: 20px; /* Set font size */
            font-weight: bold; /* Bold font for better visibility */
            border: none; /* Optional: remove any default borders */
        }

        /* Style for active tab */
        .main .block-container .element-container .stTabs > div[aria-selected="true"] {
            background-color: red; /* Red background for active tab */
            color: white; /* White text for active tab */
        }

        /* Ensure tabs fill out the full width of the container */
        .css-1l02zno {
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)


    # Add annotations to the plot
    def add_annotations(fig, data, x, y):
        max_val = data[y].max()
        max_idx = data[y].idxmax()
        fig.add_annotation(
            x=data[x][max_idx],
            y=max_val,
            text=f"Max: {max_val:.2f}",
            showarrow=True,
            arrowhead=1,
            font=dict(size=12, color="white"),
            bgcolor="red",
            bordercolor="black"
        )
        min_val = data[y].min()
        min_idx = data[y].idxmin()
        fig.add_annotation(
            x=data[x][min_idx],
            y=min_val,
            text=f"Min: {min_val:.2f}",
            showarrow=True,
            arrowhead=1,
            font=dict(size=12, color="white"),
            bgcolor="blue",
            bordercolor="black"
        )


    # SPC Control Limits Calculation
    def calculate_control_limits(data, feature, custom_ucl=None, custom_lcl=None):
        mean = data[feature].mean()
        std = data[feature].std()
        ucl = custom_ucl if custom_ucl is not None else mean + 3 * std  # Upper Control Limit (UCL)
        lcl = custom_lcl if custom_lcl is not None else mean - 3 * std  # Lower Control Limit (LCL)
        return mean, ucl, lcl


    # Process Capability (Cp, Cpk) Calculation
    def process_capability_analysis(data, feature, ucl, lcl):
        mean = data[feature].mean()
        std = data[feature].std()
        cp = (ucl - lcl) / (6 * std)
        cpk = min((ucl - mean) / (3 * std), (mean - lcl) / (3 * std))
        return cp, cpk


    # Out-of-Control Detection (Rule 1: Points outside UCL/LCL)
    def detect_out_of_control(data, feature, ucl, lcl):
        out_of_control = data[(data[feature] > ucl) | (data[feature] < lcl)]
        return out_of_control


    # Detect 7 Consecutive Points Above/Below the Centerline
    def detect_seven_consecutive(data, feature, cl):
        above = data[feature] > cl
        below = data[feature] < cl
        consecutive_above = above.rolling(7).sum() == 7
        consecutive_below = below.rolling(7).sum() == 7
        return data[consecutive_above | consecutive_below]


    # Rule 2: 2 out of 3 consecutive points on the same side and more than 2 std devs away from the centerline
    def detect_two_of_three(data, feature, cl, std_dev):
        deviation = 2 * std_dev
        points = (data[feature] - cl).abs() > deviation
        same_side = (data[feature] > cl).rolling(window=3).sum() == 2
        return data[same_side & points]


    # Rule 3: 4 out of 5 consecutive points on the same side and more than 1 std devs away from the centerline
    def detect_four_of_five(data, feature, cl, std_dev):
        deviation = 1 * std_dev
        points = (data[feature] - cl).abs() > deviation
        same_side = (data[feature] > cl).rolling(window=5).sum() >= 4
        return data[same_side & points]


    # Rule 4: 8 consecutive points on the same side of the centerline
    def detect_eight_consecutive(data, feature, cl):
        same_side = (data[feature] > cl).rolling(window=8).sum() == 8
        return data[same_side]


    # Trend Detection (Simple linear regression on the data)
    def detect_trend(data, feature):
        data['trend'] = data[feature].rolling(window=5).mean()
        return data


    # Plotly Chart Rendering with SPC Annotations and Out-of-Control Detection
    def render_spc_chart(data, feature, ucl, lcl, cl):
        fig = px.line(data, x='timestamp', y=feature, title=f"SPC Chart for {feature}")
        fig.add_hline(y=cl, line_dash="dash", annotation_text="CL", line_color="green")
        fig.add_hline(y=ucl, line_dash="dash", annotation_text="UCL", line_color="red")
        fig.add_hline(y=lcl, line_dash="dash", annotation_text="LCL", line_color="red")

        std_dev = data[feature].std()

        # Detect Rule 2 violations
        rule_2_violations = detect_two_of_three(data, feature, cl, std_dev)
        fig.add_trace(go.Scatter(
            x=rule_2_violations['timestamp'],
            y=rule_2_violations[feature],
            mode='markers',
            marker=dict(color='orange', size=10, symbol='circle'),
            name='Rule 2 Violations'
        ))

        # Detect Rule 3 violations
        rule_3_violations = detect_four_of_five(data, feature, cl, std_dev)
        fig.add_trace(go.Scatter(
            x=rule_3_violations['timestamp'],
            y=rule_3_violations[feature],
            mode='markers',
            marker=dict(color='purple', size=10, symbol='star'),
            name='Rule 3 Violations'
        ))

        # Detect Rule 4 violations
        rule_4_violations = detect_eight_consecutive(data, feature, cl)
        fig.add_trace(go.Scatter(
            x=rule_4_violations['timestamp'],
            y=rule_4_violations[feature],
            mode='markers',
            marker=dict(color='red', size=10, symbol='diamond'),
            name='Rule 4 Violations'
        ))

        add_annotations(fig, data, 'timestamp', feature)
        return fig


    def render_capability_gauges(cp, cpk):
        fig = go.Figure()

        # Cp Gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=cp,
            title={'text': "Process Capability (Cp)"},
            gauge={'axis': {'range': [0, 2]}, 'bar': {'color': "blue"}},
            domain={'x': [0, 0.5], 'y': [0, 1]}
        ))

        # Cpk Gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=cpk,
            title={'text': "Process Performance (Cpk)"},
            gauge={'axis': {'range': [0, 2]}, 'bar': {'color': "green"}},
            domain={'x': [0.5, 1], 'y': [0, 1]}
        ))

        return fig


    def render_run_chart_with_stability(data, feature, ucl, lcl, cl):
        # Add a stability flag based on control limits
        data['Stability'] = np.where((data[feature] > lcl) & (data[feature] < ucl), 'Stable', 'Unstable')

        # Create the line chart
        fig = px.line(data, x='timestamp', y=feature, title=f"Run Chart with Stability for {feature}",
                      color='Stability', color_discrete_map={'Stable': 'green', 'Unstable': 'red'})

        # Add control limits
        fig.add_hline(y=cl, line_dash="dash", annotation_text="CL", line_color="green")
        fig.add_hline(y=ucl, line_dash="dash", annotation_text="UCL", line_color="red")
        fig.add_hline(y=lcl, line_dash="dash", annotation_text="LCL", line_color="red")

        return fig


    # PDF Report Generation
    def generate_spc_report(feature, cl, ucl, lcl, cp, cpk, rule_violations=None):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Add a title
        pdf.cell(200, 10, txt=f"SPC Analysis Report for {feature}", ln=True, align='C')
        pdf.ln(10)

        # Control Limits
        pdf.cell(200, 10, txt=f"Control Limits:", ln=True)
        pdf.cell(200, 10, txt=f"Center Line (CL): {cl:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Upper Control Limit (UCL): {ucl:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Lower Control Limit (LCL): {lcl:.2f}", ln=True)
        pdf.ln(10)

        # Process Capability
        pdf.cell(200, 10, txt="Process Capability:", ln=True)
        pdf.cell(200, 10, txt=f"Cp: {cp:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Cpk: {cpk:.2f}", ln=True)

        # Add any rule violations
        if rule_violations:
            pdf.ln(10)
            pdf.cell(200, 10, txt="SPC Rule Violations:", ln=True)
            for violation in rule_violations:
                pdf.cell(200, 10, txt=violation, ln=True)

        report_path = f"{feature}_spc_report.pdf"
        pdf.output(report_path)
        return report_path


    # Define a session state variable to track if annotations should be cleared
    if 'clear_annotations' not in st.session_state:
        st.session_state['clear_annotations'] = False


    # Function to render the plotly chart with drawing capabilities
    def render_plotly_chart_with_drawing(fig):
        plotly_html = fig.to_html(full_html=False)
        components.html(f"""
        <div>
            {plotly_html}
            <canvas id="canvas" width="800" height="400" style="position: absolute; top: 0; left: 0; z-index: 10;"></canvas>
            <script>
                window.onload = function() {{
                    var canvas = document.getElementById('canvas');
                    var ctx = canvas.getContext('2d');
                    var drawing = false;

                    var addAnnotationsButton = document.getElementById('add_annotations');
                    var clearAnnotationsButton = document.getElementById('clear_annotations');

                    if (addAnnotationsButton && clearAnnotationsButton) {{

                        addAnnotationsButton.addEventListener('click', function() {{
                            canvas.style.pointerEvents = 'auto';  // Enable drawing
                        }});

                        clearAnnotationsButton.addEventListener('click', function() {{
                            ctx.clearRect(0, 0, canvas.width, canvas.height);  // Clear the canvas
                            window.location.reload();  // Reload the window to refresh the chart
                        }});
                    }}

                    canvas.addEventListener('mousedown', function(e) {{
                        drawing = true;
                        ctx.beginPath();
                        ctx.moveTo(e.offsetX, e.offsetY);
                    }});

                    canvas.addEventListener('mousemove', function(e) {{
                        if (drawing) {{
                            ctx.lineTo(e.offsetX, e.offsetY);
                            ctx.stroke();
                        }}
                    }});

                    canvas.addEventListener('mouseup', function() {{
                        drawing = false;
                    }});

                    canvas.addEventListener('mouseout', function() {{
                        drawing = false;
                    }});
                }};
            </script>
        </div>
        """, height=450)


    # # Clear annotations by refreshing the chart
    # if st.button("Clear Annotations"):
    #     st.session_state['clear_annotations'] = True  # Set flag to refresh chart

    def plot_date_range(data):
        """Plots for Date Range filter."""
        col1, col2 = st.columns(2)

        with col1:
            # Time Series for each feature
            for feature in ['Comp_Air_Totalized', 'Water_Totalized', 'kwh_actual_with_sim']:
                fig = px.line(data, x='timestamp', y=feature, title=f"Time Series of {feature}")
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Cumulative Usage Area Chart
            fig_area = px.area(data, x='timestamp', y=['Comp_Air_Totalized', 'Water_Totalized', 'kwh_actual_with_sim'],
                               title="Cumulative Usage Over Period")
            st.plotly_chart(fig_area, use_container_width=True)

            # Proportional Usage Pie Chart
            pie_data = data[['Comp_Air_Totalized', 'Water_Totalized', 'kwh_actual_with_sim']].sum().reset_index()
            pie_data.columns = ['feature', 'value']
            fig_pie = px.pie(pie_data, values='value', names='feature', title="Proportional Usage Comparison")
            st.plotly_chart(fig_pie, use_container_width=True)

            # Correlation Heatmap
            fig_corr = px.imshow(data[['Comp_Air_Totalized', 'Water_Totalized', 'kwh_actual_with_sim']].corr(),
                                 labels=dict(color="Correlation"), title="Feature Correlation Heatmap")
            st.plotly_chart(fig_corr, use_container_width=True)

            # Scatter Plot (interactive selection)
            feature_x = st.selectbox("Select X feature",
                                     ['Comp_Air_Totalized', 'Water_Totalized', 'kwh_actual_with_sim'],
                                     key='x_feature')
            feature_y = st.selectbox("Select Y feature",
                                     ['Comp_Air_Totalized', 'Water_Totalized', 'kwh_actual_with_sim'],
                                     key='y_feature', index=1)
            fig_scatter = px.scatter(data, x=feature_x, y=feature_y, title=f"{feature_x} vs {feature_y}")
            st.plotly_chart(fig_scatter, use_container_width=True)


    def plot_time_interval(data):
        """Plots for Time Interval filter."""
        col1, col2, col3 = st.columns(3)

        # Histograms and Heatmaps for each feature
        for i, feature in enumerate(['Comp_Air_Totalized', 'Water_Totalized', 'kwh_actual_with_sim']):
            with [col1, col2, col3][i % 3]:
                # Histogram
                fig_hist = px.histogram(data, x=feature, title=f"Distribution of {feature}")
                st.plotly_chart(fig_hist, use_container_width=True)

                # Stacked Bar Chart
                fig_stacked = px.bar(data, x='timestamp', y=feature, title=f"Usage Over Time by {feature}")
                st.plotly_chart(fig_stacked, use_container_width=True)

                # Line Chart with Rolling Average
                fig_line = px.line(data, x='timestamp', y=feature, title=f"Rolling Average of {feature} (7-day window)")
                data['rolling'] = data[feature].rolling(window=7).mean()
                fig_line.add_scatter(x=data['timestamp'], y=data['rolling'], mode='lines', name='Rolling Avg')
                st.plotly_chart(fig_line, use_container_width=True)

                # Heatmap
                heatmap_data = data.set_index('timestamp').resample('D')[feature].mean().reset_index()
                fig_heatmap = px.imshow(heatmap_data.pivot(index='timestamp', columns=feature, values=feature),
                                        labels={'color': 'Intensity'}, title=f"Heatmap of {feature} Usage")
                st.plotly_chart(fig_heatmap, use_container_width=True)


    def plot_oee_date_range(data):
        """Plots for OEE Data based on Date Range filter."""

        st.subheader("OEE Data Visualizations (Date Range)")

        oee_metrics = ['OEE', 'OEE_Availability', 'OEE_Performance', 'OEE_Quality']
        oee_data = data[oee_metrics].mean().reset_index()
        oee_data.columns = ['Metric', 'Value']

        # Create a horizontal stacked bar chart for OEE metrics
        fig_stacked_bar = px.bar(oee_data, x='Value', y='Metric', title="OEE Metrics Overview",
                                 orientation='h', color='Metric', text='Value',
                                 height=400, width=700,
                                 color_discrete_map={
                                     'OEE': 'blue',
                                     'OEE_Availability': 'green',
                                     'OEE_Performance': 'red',
                                     'OEE_Quality': 'purple'
                                 })
        fig_stacked_bar.update_layout(barmode='stack')
        st.plotly_chart(fig_stacked_bar, use_container_width=True)

        # 2. Line Chart for OEE, OEE_Availability, OEE_Performance, OEE_Quality
        fig_line = px.line(data, x='Time_Stamp', y=['OEE', 'OEE_Availability', 'OEE_Performance', 'OEE_Quality'],
                           title="OEE, Availability, Performance, and Quality Over Time")
        st.plotly_chart(fig_line, use_container_width=True)

        # 3. Area Chart for cumulative values of run, manual, idle, etc.
        data = data.dropna(
            subset=['A_Run_Duration', 'A_Manual_Duration', 'A_Idle_Duration', 'A_Total_Duration', 'A_stop_duration',
                    'A_Alarm_Duration'])
        fig_area = px.area(
            data,
            x='Time_Stamp',
            y=['A_Run_Duration', 'A_Manual_Duration', 'A_Idle_Duration', 'A_Total_Duration', 'A_stop_duration',
               'A_Alarm_Duration'],
            title="Cumulative Duration Values Over Time"
        )
        st.plotly_chart(fig_area, use_container_width=True)

        # fig_area = px.area(data, x='Time_Stamp', y=['A_Run_Duration', 'A_Manual_Duration', 'A_Idle_Duration',
        #                                            'A_Total_Duration', 'A_Stop_Duration', 'A_Alarm_Duration'],
        #                    title="Cumulative Duration Values Over Time")
        # st.plotly_chart(fig_area, use_container_width=True)

        # 4. Pie Chart: Compare the proportion of Q_No_Of_Good, Q_No_Of_Bad, and Q_Total_No
        pie_data = data[['Q_No_Of_Good', 'Q_No_Of_Bad', 'Q_Total_No']].sum().reset_index()
        pie_data.columns = ['Quality', 'value']
        fig_pie = px.pie(pie_data, values='value', names='Quality', title="Proportional Quality Comparison")
        st.plotly_chart(fig_pie, use_container_width=True)

        # 5. Stacked Bar Chart for comparing machine states
        fig_stacked_bar = px.bar(data, x='Time_Stamp', y=['A_Run_Duration', 'A_Manual_Duration', 'A_Idle_Duration'],
                                 title="Machine State Comparison (Stacked)", barmode='stack')
        st.plotly_chart(fig_stacked_bar, use_container_width=True)

        # 6. Scatter Plot: Examine relationships between two features (P_No_Of_Cycles vs P_Average_Time)
        feature_x = st.selectbox("Select X feature for scatter plot", ['P_No_Of_Cycles', 'P_Average_Time'],
                                 key='scatter_x')
        feature_y = st.selectbox("Select Y feature for scatter plot", ['P_No_Of_Cycles', 'P_Average_Time'],
                                 key='scatter_y',
                                 index=1)
        fig_scatter = px.scatter(data, x=feature_x, y=feature_y, title=f"Scatter Plot of {feature_x} vs {feature_y}")
        st.plotly_chart(fig_scatter, use_container_width=True)

        # 7. Correlation Heatmap: For OEE metrics
        oee_metrics = ['OEE', 'OEE_Availability', 'OEE_Performance', 'OEE_Quality']
        fig_corr_oee = px.imshow(data[oee_metrics].corr(), text_auto=True, title="Correlation Heatmap for OEE Metrics")
        st.plotly_chart(fig_corr_oee, use_container_width=True)

        # Correlation Heatmap: For features contributing to OEE
        oee_contributors = ['A_Run_Duration', 'A_Manual_Duration', 'A_Idle_Duration', 'A_Total_Duration',
                            'A_stop_duration',
                            'A_Alarm_Duration']
        fig_corr_oee_contrib = px.imshow(data[oee_contributors].corr(), text_auto=True,
                                         title="Correlation Heatmap for OEE Contributors")
        st.plotly_chart(fig_corr_oee_contrib, use_container_width=True)

        # 8. Box Plot for cycle times
        fig_box = px.box(data, y=['P_Min_Cycle_Time', 'P_Average_Time', 'P_Current_Time'],
                         title="Box Plot for Cycle Times")
        st.plotly_chart(fig_box, use_container_width=True)


    # Function to generate Time Interval plots for OEE Data
    def plot_time_interval_oee(filtered_data, interval):
        st.subheader("Visualizations Based on Time Interval")

        # Ensure the 'Time_Stamp' is set as index for resampling
        if 'Time_Stamp' in filtered_data.columns:
            filtered_data = filtered_data.set_index('Time_Stamp')

        try:
            # Resample data by the selected interval
            resampled_data = filtered_data.resample(interval).mean().reset_index()

            if resampled_data.empty:
                st.warning("No data found after resampling. Try changing the filter.")
                return

            # 1. Heatmap: Usage Intensity
            st.subheader("Heatmap: Usage Intensity")
            heatmap_features = ['OEE', 'OEE_Availability', 'OEE_Performance', 'OEE_Quality']
            if all(feature in resampled_data.columns for feature in heatmap_features):
                fig_heatmap = px.imshow(resampled_data[heatmap_features].T, title=f"Heatmap for {interval} interval",
                                        aspect="auto")
                st.plotly_chart(fig_heatmap, use_container_width=True)

            # 2. Rolling Average Line Chart
            st.subheader("Rolling Average Line Chart")
            rolling_features = ['OEE', 'OEE_Performance']
            for feature in rolling_features:
                if feature in resampled_data.columns:
                    resampled_data[f'{feature}_rolling'] = resampled_data[feature].rolling(window=7).mean()
                    fig_rolling_avg = px.line(resampled_data, x='Time_Stamp', y=f'{feature}_rolling',
                                              title=f"Rolling Average of {feature} (7-day window)")
                    st.plotly_chart(fig_rolling_avg, use_container_width=True)

                # 3D Scatter Plot
                st.subheader("3D Scatter Plot")
                scatter_features = ['P_No_Of_Cycles', 'P_Average_Time', 'OEE']
                fig_scatter_3d = px.scatter_3d(resampled_data, x=scatter_features[0], y=scatter_features[1],
                                               z=scatter_features[2],
                                               title="3D Scatter Plot (OEE, P_No_Of_Cycles, P_Average_Time)")
                st.plotly_chart(fig_scatter_3d, use_container_width=True)

                # 3D Line Chart
                st.subheader("3D Line Chart")
                fig_3d_line = go.Figure()
                fig_3d_line.add_trace(go.Scatter3d(x=resampled_data['Time_Stamp'], y=resampled_data['P_Average_Time'],
                                                   z=resampled_data['A_Total_Duration'], mode='lines',
                                                   name="P_Average_Time vs A_Total_Duration"))
                fig_3d_line.update_layout(title="3D Line Chart: P_Average_Time vs A_Total_Duration vs OEE")
                st.plotly_chart(fig_3d_line, use_container_width=True)

                # Stacked Bar Chart: Machine States
                st.subheader("Stacked Bar Chart: Machine States")
                bar_features = ['A_Run_Duration', 'A_Idle_Duration', 'A_Manual_Duration']
                fig_stacked_bar = px.bar(resampled_data, x='Time_Stamp', y=bar_features,
                                         title="Stacked Bar Chart: Machine States (Run, Idle, Manual)", barmode='stack')
                st.plotly_chart(fig_stacked_bar, use_container_width=True)

                # Bar Chart (Interval Comparison)
                st.subheader("Bar Chart: Interval Comparison for P_No_Of_Cycles")
                fig_bar_chart = px.bar(resampled_data, x='Time_Stamp', y='P_No_Of_Cycles',
                                       title=f"P_No_Of_Cycles Comparison over {interval} interval")
                st.plotly_chart(fig_bar_chart, use_container_width=True)

                # Density Heatmap
                st.subheader("Density Heatmap")
                fig_density_heatmap = px.density_heatmap(resampled_data, x='Time_Stamp', y='OEE',
                                                         title=f"Density Heatmap for OEE over {interval} interval")
                st.plotly_chart(fig_density_heatmap, use_container_width=True)

                # 3D Surface Plot
                st.subheader("3D Surface Plot")
                surface_data = resampled_data.pivot_table(index='Time_Stamp', columns='OEE_Performance',
                                                          values='P_Accumulated_Time')
                fig_surface = go.Figure(data=[go.Surface(z=surface_data)])
                fig_surface.update_layout(title="3D Surface Plot: OEE_Performance vs P_Accumulated_Time")
                st.plotly_chart(fig_surface, use_container_width=True)

        except Exception as e:
            st.error(f"Error processing the time interval data: {e}")


    # Reusable function for date range and interval selection
    def apply_filter(data, filter_choice, key_prefix):
        """Applies the selected filter based on the UI elements' state related to key_prefix."""
        filter_choice = st.session_state.get(f"{key_prefix}_filter_method")
        if filter_choice == 'Date Range':
            start_date = st.session_state.get(f"{key_prefix}_start_date")
            end_date = st.session_state.get(f"{key_prefix}_end_date")
            if start_date and end_date:
                return data[(data['timestamp'].dt.date >= start_date) & (data['timestamp'].dt.date <= end_date)]
        elif filter_choice == 'Time Interval':
            interval = st.session_state.get(f"{key_prefix}_interval")
            if interval:
                return data.set_index('timestamp').resample(interval).mean().reset_index()
        return data


    # Before your tabs
    st.markdown('<div class="custom-tabs">', unsafe_allow_html=True)

    # After your tabs
    st.markdown('</div>', unsafe_allow_html=True)

    # ======= Past Performance =======

# ======= Past Performance =======
with tabs[1]:
    st.title("Past Performance")
    # Subtabs for "Past Performance"
    subtab1, subtab2, subtab3 = st.tabs(["SPC Analysis", "Machine Data", "OEE Data"])

    # Subtab 1: SPC Analysis
    with subtab1:
        st.markdown("""
            <style>
            div.row-widget.stRadio > div{ flex-direction: row!important; }
            label {font-weight: bold;}
            </style>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1])
        with col1:
            filter_choice = st.radio("Choose Filter Method", ['Date Range', 'Time Interval'],
                                     key="spc_filter_choice")

        if filter_choice == 'Date Range':
            col3, col4 = st.columns([1, 1])
            with col3:
                start_date = st.date_input("Select start date", key='spc_start_date')
            with col4:
                end_date = st.date_input("Select end date", key='spc_end_date')
        elif filter_choice == 'Time Interval':
            interval = st.selectbox("Select Time Interval for Aggregation",
                                    ['H', 'D', 'W', 'M', 'Y'],
                                    format_func=lambda x:
                                    {'H': 'Hourly', 'D': 'Daily', 'W': 'Weekly', 'M': 'Monthly', 'Y': 'Yearly'}[x],
                                    key='spc_interval')

        try:
            query = f"SELECT Time_Stamp, Comp_Air_Totalized, Water_Totalized, kwh_actual_with_sim FROM {database}.machine_resources_latest"
            data = pd.read_sql(query, i40db)
            data['timestamp'] = pd.to_datetime(data['Time_Stamp'])

            if not data.empty:
                col5, col6, col7 = st.columns([2, 1, 1])
                with col5:
                    feature = st.selectbox('Select Feature for SPC Analysis',
                                           options=data.columns.difference(['timestamp', 'Time_Stamp']))
                with col6:
                    custom_ucl = st.number_input("Enter Custom UCL (optional)", value=0.0)
                with col7:
                    custom_lcl = st.number_input("Enter Custom LCL (optional)", value=0.0)

                filtered_data = apply_filter(data, filter_choice, 'spc')
                cl, ucl, lcl = calculate_control_limits(filtered_data, feature, custom_ucl, custom_lcl)
                cp, cpk = process_capability_analysis(filtered_data, feature, ucl, lcl)

                # Rendering the SPC chart
                fig = render_spc_chart(filtered_data, feature, ucl, lcl, cl)
                render_plotly_chart_with_drawing(fig)  # Enables annotations on the chart
                st.plotly_chart(fig, use_container_width=True)

                # Buttons for clearing annotations and generating reports
                col8, col9 = st.columns([1, 1])
                with col8:
                    if st.button("Clear Annotations"):
                        st.experimental_rerun()  # Refresh the page to simulate clearing the annotations
                with col9:
                    if st.button('Generate SPC Report'):
                        report_path = generate_spc_report(feature, cl, ucl, lcl, cp, cpk)
                        with st.expander("View SPC Report"):
                            with open(report_path, "rb") as file:
                                st.download_button("Download SPC Report", data=file, file_name=report_path,
                                                   mime="application/pdf")
                        st.success("SPC Report generated and ready for download.")

        except Exception as e:
            st.error(f"Error fetching data from the database: {str(e)}")

    # Subtab 2: Machine Data
    with subtab2:
        st.markdown('<div class="sub-header">Machine Data</div>', unsafe_allow_html=True)

        filter_choice = st.radio(
            "Choose Filter Method",
            ['Date Range', 'Time Interval'],
            key='machine_data_filter_choice'
        )

        # Define the filter UI elements based on the selected method
        if filter_choice == 'Date Range':
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Select start date", key='machine_data_start_date')
            with col2:
                end_date = st.date_input("Select end date", key='machine_data_end_date')
        else:
            interval = st.selectbox(
                "Select Time Interval for Aggregation",
                ['H', 'D', 'W', 'M', 'Y'],  # Hourly, Daily, Weekly, Monthly, Yearly
                format_func=lambda x: {'H': 'Hourly', 'D': 'Daily', 'W': 'Weekly', 'M': 'Monthly', 'Y': 'Yearly'}[
                    x],
                key='machine_data_interval'
            )

        try:
            query =f"SELECT Time_Stamp, Comp_Air_Totalized, Water_Totalized, kwh_actual_with_sim FROM {database}.machine_resources_latest"
            data = pd.read_sql(query, i40db)
            data['timestamp'] = pd.to_datetime(data['Time_Stamp'])

            if data.empty:
                st.warning("No data found.")
            else:
                # Adjust the apply_filter call as needed
                filtered_data = apply_filter(data, filter_choice, 'machine_data')
                if filter_choice == 'Date Range':
                    plot_date_range(filtered_data)
                elif filter_choice == 'Time Interval':
                    plot_time_interval(filtered_data)

        except Exception as e:
            st.error("Error fetching Machine data from the database.")
            st.write(str(e))

    # Subtab 3: OEE Data
    # Subtab 3: OEE Data
    with subtab3:
        st.markdown('<div class="sub-header">OEE Data</div>', unsafe_allow_html=True)

        filter_choice = st.radio("Choose Filter Method", ['Date Range', 'Time Interval'], key="oee_filter_choice")

        if filter_choice == 'Date Range':
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Select start date", key='oee_start_date')
            with col2:
                end_date = st.date_input("Select end date", key='oee_end_date')

            try:
                query_oee = f"SELECT * FROM {database}.oee_log3"
                oee_data = pd.read_sql(query_oee, i40db)
                oee_data['Time_Stamp'] = pd.to_datetime(oee_data['Time_Stamp'])

                if oee_data.empty:
                    st.warning("No OEE data found.")
                    st.stop()

                filtered_data = apply_filter(oee_data, filter_choice, 'oee_data')
                if filtered_data.empty:
                    st.warning("No data found for the selected range.")
                    st.stop()

                plot_oee_date_range(filtered_data)

            except Exception as e:
                st.error("Error fetching or processing OEE data from the database.")
                st.exception(e)

        elif filter_choice == 'Time Interval':
            interval = st.selectbox("Select Time Interval for Aggregation",
                                    ['H', 'D', 'W', 'M', 'Y'],  # Hourly, Daily, Weekly, Monthly, Yearly
                                    format_func=lambda x:
                                    {'H': 'Hourly', 'D': 'Daily', 'W': 'Weekly', 'M': 'Monthly', 'Y': 'Yearly'}[x],
                                    key='oee_interval')

            try:
                query_oee = f"SELECT * FROM {database}.oee_log3"
                oee_data = pd.read_sql(query_oee, i40db)
                oee_data['Time_Stamp'] = pd.to_datetime(oee_data['Time_Stamp'])

                if oee_data.empty:
                    st.warning("No OEE data found.")
                    st.stop()

                filtered_data = apply_filter(oee_data, filter_choice, 'oee_data')
                if filtered_data.empty:
                    st.warning("No data found after filtering.")
                    st.stop()

                plot_time_interval_oee(filtered_data, interval)

            except Exception as e:
                st.error("Error fetching or processing OEE data from the database.")
                st.exception(e)

# ======= Ask NerCy Tab =======
with tabs[2]:
    st.title("NerCy Chatbot")

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

    # Display chat history on app rerun in container
    with st.container(height=500):
        display_messages()

    additional_context = ('Check the following prompt to see if it requires the use of an agent and if it does '
                          'return True. Do not return any other words other then True if it does require an agent. '
                          'If it does not require an agent respond to the best of your ability without using an '
                          'agent. Prompt: ')

    assistant_message_agent = 'Null'

    # Use columns to position input and send button side by side
    col1, col2 = st.columns([8, 1])  # Adjust the ratio as needed (4:1 for input field:button)

    with col1:
        prompt = st.text_input("Please type your questions here!", value=st.session_state.selected_prompt)

    with col2:
        # Create an empty space above the button to center it
        st.write("")  # Adds a small space
        # "Send" button
        send_button = st.button('Send')

    # If send button is clicked and prompt bar is not empty
    if send_button:
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            url_3 = aLLMConfig["url"]+'/chat'
            print(url_3)
            data_3 = {'message': additional_context + prompt, 'mode': 'chat'}
            headers_3 = {'Authorization':  aLLMConfig["Authorization"], 'Accept': 'application/json'}
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
            st.session_state.selected_prompt = ''
            st.rerun()  # Rerun the script to display messages

    # List of default prompts with custom configurations
    default_prompts = [
        {'label': 'Use Case & Purpose', 'prompt': 'What is the use case and purpose of this chatbot?'},
        {'label': 'Database Tables Available', 'prompt': '@agent Tell me the tables present in the database?'},
        {'label': 'Information on Slack', 'prompt': '@agent What is Slack and provide some additional links '
                                                    'for information?'}
    ]

    # Create a horizontal layout for the buttons
    cols = st.columns(len(default_prompts))

    # Buttons to apply the selected default prompt to the chat input
    for i, prompt_info in enumerate(default_prompts):
        with cols[i]:  # Place each button in its respective column
            if st.button(prompt_info["label"]):
                st.session_state.selected_prompt = prompt_info['prompt']
                st.rerun()

    if st.button('Clear Chat History'):
        st.session_state.messages = []
        st.rerun()

# ======= Smart Detect Tab =======
with tabs[3]:
    # st.title("Anomaly Detection")

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


    # Function to load the selected model
    def load_model(model_name, model_dir):
        model_path = os.path.join(model_dir, model_name)
        with open(model_path, 'rb') as file:
            models = joblib.load(file)
        return models


    # Function to connect to the database
    def connect_to_db():
        return mysql.connector.connect(
            host=host,
            user=user,
            password=pwd,
            database=database
        )


    # Function to fetch all data from the machine_resources_latest table
    def fetch_all_data():
        db = connect_to_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT Time_Stamp, Comp_Air_Totalized, Water_Totalized, kWh_actual_with_sim FROM machine_resources_latest ORDER BY Time_Stamp"
        )
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


    # Function to filter data within the selected date-time range
    def filter_data_by_time(data, start_dt, end_dt):
        data['Time_Stamp'] = pd.to_datetime(data['Time_Stamp'])
        filtered_data = data[(data['Time_Stamp'] >= start_dt) & (data['Time_Stamp'] <= end_dt)]
        return filtered_data


    # Function to create a 3D line plot based on the type of anomaly
    @st.cache_data(show_spinner=False)
    def create_plot(all_data, row, type_of_anomaly):
        fig = go.Figure()

        start_time = all_data['Time_Stamp'].min()
        end_time = all_data['Time_Stamp'].max()
        middle_index = len(all_data) // 2
        middle_time = all_data['Time_Stamp'].iloc[middle_index]

        tick_indices = [all_data.index.min(), middle_index, all_data.index.max()]
        tick_labels = [start_time.strftime('%d-%m-%Y %I:%M:%S %p'),
                       middle_time.strftime('%d-%m-%Y %I:%M:%S %p'),
                       end_time.strftime('%d-%m-%Y %I:%M:%S %p')]

        if type_of_anomaly == 'water':
            z_data = all_data['Water_Totalized']
            z_anomaly = row['Water_Totalized']
            z_label = 'Water Consumption'
        elif type_of_anomaly == 'energy':
            z_data = all_data['kWh_actual_with_sim']
            z_anomaly = row['kWh_actual_with_sim']
            z_label = 'Energy Consumption (kWh)'
        elif type_of_anomaly == 'air':
            z_data = all_data['Comp_Air_Totalized']
            z_anomaly = row['Comp_Air_Totalized']
            z_label = 'Air Consumption'

        fig.add_trace(go.Scatter3d(
            x=[0] * len(all_data),
            y=all_data.index,
            z=z_data,
            mode='lines',
            line=dict(color='blue', width=2),
            name='Normal'
        ))

        fig.add_trace(go.Scatter3d(
            x=[0],
            y=[row.name],
            z=[z_anomaly],
            mode='markers',
            marker=dict(size=10, color='red', opacity=0.8),
            name=f'{type_of_anomaly.capitalize()} Anomaly'
        ))

        fig.update_layout(
            title=f'3D Line Plot of {type_of_anomaly.capitalize()} Anomaly',
            scene=dict(
                xaxis=dict(title='', showticklabels=False),
                yaxis=dict(
                    title='Date',
                    tickvals=tick_indices,
                    ticktext=tick_labels
                ),
                zaxis_title=z_label,
            ),
            height=700,
            legend=dict(x=0.1, y=0.9)
        )

        return fig


    # Function to create a 3D anomaly graph with energy, air, and water
    def create_3d_anomaly_graph(data):
        start_time = data['Time_Stamp'].min()
        end_time = data['Time_Stamp'].max()
        middle_index = len(data) // 2
        middle_time = data['Time_Stamp'].iloc[middle_index]

        tick_indices = [data.index.min(), middle_index, data.index.max()]
        tick_labels = [start_time.strftime('%d-%m-%Y %I:%M:%S %p'),
                       middle_time.strftime('%d-%m-%Y %I:%M:%S %p'),
                       end_time.strftime('%d-%m-%Y %I:%M:%S %p')]

        fig = go.Figure()

        fig.add_trace(go.Scatter3d(
            x=[0] * len(data),
            y=data.index,
            z=data['kWh_actual_with_sim'],
            mode='lines',
            line=dict(color='blue', width=2),
            name='Energy Consumption (Normal)'
        ))

        if 'Energy_Anomaly' in data.columns:
            fig.add_trace(go.Scatter3d(
                x=[0] * len(data[data['Energy_Anomaly'] == 1]),
                y=data[data['Energy_Anomaly'] == 1].index,
                z=data[data['Energy_Anomaly'] == 1]['kWh_actual_with_sim'],
                mode='markers',
                marker=dict(size=5, color='red'),
                name='Energy Anomalies'
            ))

        fig.add_trace(go.Scatter3d(
            x=[0] * len(data),
            y=data.index,
            z=data['Comp_Air_Totalized'],
            mode='lines',
            line=dict(color='green', width=2),
            name='Air Consumption (Normal)'
        ))

        if 'Air_Anomaly' in data.columns:
            fig.add_trace(go.Scatter3d(
                x=[0] * len(data[data['Air_Anomaly'] == 1]),
                y=data[data['Air_Anomaly'] == 1].index,
                z=data[data['Air_Anomaly'] == 1]['Comp_Air_Totalized'],
                mode='markers',
                marker=dict(size=5, color='red'),
                name='Air Anomalies'
            ))

        fig.add_trace(go.Scatter3d(
            x=[0] * len(data),
            y=data.index,
            z=data['Water_Totalized'],
            mode='lines',
            line=dict(color='purple', width=2),
            name='Water Consumption (Normal)'
        ))

        if 'Water_Anomaly' in data.columns:
            fig.add_trace(go.Scatter3d(
                x=[0] * len(data[data['Water_Anomaly'] == 1]),
                y=data[data['Water_Anomaly'] == 1].index,
                z=data[data['Water_Anomaly'] == 1]['Water_Totalized'],
                mode='markers',
                marker=dict(size=5, color='red'),
                name='Water Anomalies'
            ))

        fig.update_layout(
            title='3D Line Plot of Energy, Air, and Water Consumption with Anomalies',
            scene=dict(
                xaxis=dict(title='', showticklabels=False),
                yaxis=dict(
                    title='Date',
                    tickvals=tick_indices,
                    ticktext=tick_labels
                ),
                zaxis=dict(title='Consumption'),
            ),
            height=700,
            legend=dict(x=0.1, y=0.9)
        )

        return fig


    # Streamlit app
    def main():
        st.title("Anomaly Detection")

        model_dir = os.getcwd()+"\models"

        if 'selected_anomaly' not in st.session_state:
            st.session_state.selected_anomaly = None
        if 'last_timestamp' not in st.session_state:
            st.session_state.last_timestamp = None
        if 'stop_signal' not in st.session_state:
            st.session_state.stop_signal = False
        if 'contamination_energy' not in st.session_state:
            st.session_state.contamination_energy = 0.04450
        if 'contamination_air' not in st.session_state:
            st.session_state.contamination_air = 0.019
        if 'contamination_water' not in st.session_state:
            st.session_state.contamination_water = 0.0001

        st.header("Real-Time Monitoring")
        all_data = fetch_all_data()

        if all_data.empty:
            st.write("No data available in the database.")
            return

        st.session_state.last_timestamp = all_data['Time_Stamp'].max()

        fig_energy = go.Figure()
        fig_air = go.Figure()
        fig_water = go.Figure()

        fig_energy.add_trace(go.Scatter(
            x=all_data['Time_Stamp'],
            y=all_data['kWh_actual_with_sim'],
            mode='lines',
            line=dict(color='blue'),
            name='Energy Consumption (kWh)'
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
            yaxis_title="Energy (kWh)",
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

        st.header("Anomaly Detection")
        model_options = ["None"] + os.listdir(model_dir)
        model_name = st.selectbox('Select Model', model_options)

        if model_name != "None":
            models = load_model(model_name, model_dir)

            # Check if the model is an Isolation Forest or Local Outlier Factor (LOF)
            model_energy = models['energy_model']
            model_air = models['air_model']
            model_water = models['water_model']

            model_type = type(model_energy)

            if model_type == IsolationForest:
                st.write("Using Isolation Forest Model for Anomaly Detection")
            elif model_type == LocalOutlierFactor:
                st.write("Using Local Outlier Factor (LOF) Model for Anomaly Detection")
            else:
                st.write("Unknown model type.")
                return

            st.header("Adjust Contamination Rates")
            st.session_state.contamination_air = st.slider(
                'Air Model Contamination',
                min_value=0.00001,
                max_value=0.50000,
                value=st.session_state.contamination_air,
                step=0.00001,
                format="%.5f"
            )

            st.session_state.contamination_energy = st.slider(
                'Energy Model Contamination',
                min_value=0.00001,
                max_value=0.50000,
                value=st.session_state.contamination_energy,
                step=0.00001,
                format="%.5f"
            )

            st.session_state.contamination_water = st.slider(
                'Water Model Contamination',
                min_value=0.00001,
                max_value=0.50000,
                value=st.session_state.contamination_water,
                step=0.00001,
                format="%.5f"
            )

            if st.button('Reset to Default Contamination'):
                st.session_state.contamination_energy = 0.04450
                st.session_state.contamination_air = 0.019
                st.session_state.contamination_water = 0.0001
                st.experimental_rerun()

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Start")
                start_date = st.date_input("Date", all_data['Time_Stamp'].min().date(), key='start_date')
                start_time = st.time_input("Time", all_data['Time_Stamp'].min().time(), key='start_time')

            with col2:
                st.subheader("End")
                end_date = st.date_input("Date", all_data['Time_Stamp'].max().date(), key='end_date')
                end_time = st.time_input("Time", all_data['Time_Stamp'].max().time(), key='end_time')

            start_dt = datetime.combine(start_date, start_time)
            end_dt = datetime.combine(end_date, end_time)
            filtered_data = filter_data_by_time(all_data, start_dt, end_dt)

            if filtered_data.empty:
                st.write("No data found in the selected date-time range.")
                return

            start_button = st.button('Start Anomaly Detection')
            stop_button = st.button('Stop Anomaly Detection')

            if start_button:
                filtered_data['Energy_Rate'] = filtered_data['kWh_actual_with_sim'].diff().fillna(0)
                filtered_data['Air_Rate'] = filtered_data['Comp_Air_Totalized'].diff().fillna(0)
                window_size = 30
                filtered_data['Smoothed_Water'] = filtered_data['Water_Totalized'].rolling(window=window_size,
                                                                                           min_periods=1).mean()
                filtered_data['Water_Slope'] = filtered_data['Smoothed_Water'].diff(periods=2880).fillna(0)

                # Fit and predict based on model type
                if isinstance(model_energy, IsolationForest):
                    model_energy.set_params(contamination=st.session_state.contamination_energy)
                    model_air.set_params(contamination=st.session_state.contamination_air)
                    model_water.set_params(contamination=st.session_state.contamination_water)

                    model_energy.fit(filtered_data[['Energy_Rate']])
                    model_air.fit(filtered_data[['Air_Rate']])
                    model_water.fit(filtered_data[['Water_Slope']])

                    filtered_data['Energy_Anomaly'] = model_energy.predict(filtered_data[['Energy_Rate']])
                    filtered_data['Energy_Anomaly'] = filtered_data['Energy_Anomaly'].map({1: 0, -1: 1})

                    filtered_data['Air_Anomaly'] = model_air.predict(filtered_data[['Air_Rate']])
                    filtered_data['Air_Anomaly'] = filtered_data['Air_Anomaly'].map({1: 0, -1: 1})

                    filtered_data['Water_Anomaly'] = model_water.predict(filtered_data[['Water_Slope']])
                    filtered_data['Water_Anomaly'] = filtered_data['Water_Anomaly'].map({1: 0, -1: 1})

                elif isinstance(model_energy, LocalOutlierFactor):
                    # Re-instantiate LOF models with updated contamination values
                    model_energy = LocalOutlierFactor(n_neighbors=20,
                                                      contamination=st.session_state.contamination_energy)
                    model_air = LocalOutlierFactor(n_neighbors=20, contamination=st.session_state.contamination_air)
                    model_water = LocalOutlierFactor(n_neighbors=20, contamination=st.session_state.contamination_water)

                    filtered_data['Energy_Anomaly'] = model_energy.fit_predict(filtered_data[['Energy_Rate']])
                    filtered_data['Energy_Anomaly'] = filtered_data['Energy_Anomaly'].map({1: 0, -1: 1})

                    filtered_data['Air_Anomaly'] = model_air.fit_predict(filtered_data[['Air_Rate']])
                    filtered_data['Air_Anomaly'] = filtered_data['Air_Anomaly'].map({1: 0, -1: 1})

                    filtered_data['Water_Anomaly'] = model_water.fit_predict(filtered_data[['Water_Slope']])
                    filtered_data['Water_Anomaly'] = filtered_data['Water_Anomaly'].map({1: 0, -1: 1})

                fig_3d = create_3d_anomaly_graph(filtered_data)
                st.plotly_chart(fig_3d)

                while not st.session_state.stop_signal:
                    all_data = fetch_all_data()

                    all_data['Energy_Rate'] = all_data['kWh_actual_with_sim'].diff().fillna(0)
                    all_data['Air_Rate'] = all_data['Comp_Air_Totalized'].diff().fillna(0)
                    all_data['Smoothed_Water'] = all_data['Water_Totalized'].rolling(window=30, min_periods=1).mean()
                    all_data['Water_Slope'] = all_data['Smoothed_Water'].diff(periods=2880).fillna(0)

                    if isinstance(model_energy, IsolationForest):
                        all_data['energy_anomalies'] = model_energy.predict(all_data[['Energy_Rate']])
                        all_data['energy_anomalies'] = all_data['energy_anomalies'].map({1: 0, -1: 1})

                        all_data['air_anomalies'] = model_air.predict(all_data[['Air_Rate']])
                        all_data['air_anomalies'] = all_data['air_anomalies'].map({1: 0, -1: 1})

                        all_data['water_anomalies'] = model_water.predict(all_data[['Water_Slope']])
                        all_data['water_anomalies'] = all_data['water_anomalies'].map({1: 0, -1: 1})

                    elif isinstance(model_energy, LocalOutlierFactor):
                        all_data['energy_anomalies'] = model_energy.fit_predict(all_data[['Energy_Rate']])
                        all_data['energy_anomalies'] = all_data['energy_anomalies'].map({1: 0, -1: 1})

                        all_data['air_anomalies'] = model_air.fit_predict(all_data[['Air_Rate']])
                        all_data['air_anomalies'] = all_data['air_anomalies'].map({1: 0, -1: 1})

                        all_data['water_anomalies'] = model_water.fit_predict(all_data[['Water_Slope']])
                        all_data['water_anomalies'] = all_data['water_anomalies'].map({1: 0, -1: 1})

                    detected_anomalies = all_data[(all_data['energy_anomalies'] == 1) |
                                                  (all_data['air_anomalies'] == 1) |
                                                  (all_data['water_anomalies'] == 1)]

                    if detected_anomalies.empty:
                        st.write("No anomalies detected.")
                    else:
                        for _, row in detected_anomalies.iterrows():
                            if row['energy_anomalies'] == 1:
                                message = f"Anomaly detected at {row['Time_Stamp']}: Increased energy consumption"
                                send_slack_alert(message)
                                with st.expander(message):
                                    plot = create_plot(all_data, row, 'energy')
                                    st.plotly_chart(plot)

                            if row['air_anomalies'] == 1:
                                message = f"Anomaly detected at {row['Time_Stamp']}: Abnormal air consumption"
                                send_slack_alert(message)
                                with st.expander(message):
                                    plot = create_plot(all_data, row, 'air')
                                    st.plotly_chart(plot)

                            if row['water_anomalies'] == 1:
                                message = f"Anomaly detected at {row['Time_Stamp']}: Abnormal water consumption"
                                send_slack_alert(message)
                                with st.expander(message):
                                    plot = create_plot(all_data, row, 'water')
                                    st.plotly_chart(plot)

                            time.sleep(5)

                    st.write("Machine is idling...")
                    while not st.session_state.stop_signal:
                        new_data = fetch_new_data(st.session_state.last_timestamp)
                        if not new_data.empty:
                            st.write(f"New data detected, processing {len(new_data)} new records.")
                            st.session_state.last_timestamp = new_data['Time_Stamp'].max()
                            break

                        time.sleep(5)

                    if stop_button:
                        st.session_state.stop_signal = True
                        st.write("Anomaly detection stopped.")


    if __name__ == '__main__':
        main()

# ======= Smart Tools Tab =======
with tabs[4]:
    import streamlit as st
    import schedule
    import time
    from datetime import datetime
    from utilities.pdfwriter import generate_pdf_report
    from utilities.emailersmtp import send_email_with_attachment


    def schedule_report(user_email, report_time, report_frequency):
        # Convert report_time to the required string format
        report_time_str = report_time.strftime("%H:%M:%S")

        def send_report():
            data = get_data_for_report()  # Fetch data for report generation
            pdf_filename = os.getcwd() + "\\report\i40report.pdf"
            generate_pdf_report(pdf_filename, data)  # Generate the PDF report
            send_email_with_attachment(gmailConfig["sender"], gmailConfig["password"],user_email, "AMC Scheduled Report", "Please find your report attached.",
                                       pdf_filename)  # Send the email with the PDF

        # Scheduling based on frequency
        if report_frequency == 'minute':
            schedule.every(1).minutes.do(send_report)
        elif report_frequency == 'daily':
            schedule.every().day.at(report_time_str).do(send_report)
        elif report_frequency == 'weekly':
            schedule.every().week.do(send_report)  # Weekly does not support specific times, adjust if needed
        elif report_frequency == 'monthly':
            schedule.every(30).days.do(send_report)  # Approximation for monthly (30 days)
        elif report_frequency == 'yearly':
            schedule.every(365).days.do(send_report)  # Approximation for yearly (365 days)

        # Running the scheduler in a loop
        while True:
            schedule.run_pending()
            time.sleep(60)


    def main():
        st.title("Machine Resources Report")

        # Input email address
        user_email = st.text_input("Enter your email address:")

        # Select time for the report
        report_time = st.time_input("Select report time", datetime.now().time())

        # Select report frequency (daily, weekly, etc.)
        frequency_options = ['minute', 'daily', 'weekly', 'monthly', 'yearly']
        report_frequency = st.selectbox("Select report frequency", frequency_options)

        # Submit button to confirm the scheduling
        if st.button("Submit"):
            if user_email:
                st.success(f"Reports will be sent to {user_email} every {report_frequency} at {report_time}.")
                schedule_report(user_email, report_time, report_frequency)
            else:
                st.error("Please enter a valid email address.")

        # Option to stop reports via email
        stop_report = st.text_input("Enter your email to stop receiving reports:")
        if st.button("Stop Reports"):
            st.success(f"Reports for {stop_report} have been stopped.")
            stop_scheduled_report(stop_report)


    def stop_scheduled_report(user_email):
        # Placeholder for logic to remove the scheduled report for this email
        st.info(f"Unsubscribed {user_email} from receiving further reports.")
        pass


    def get_data_for_report():
        # Function to fetch data from MySQL table
        import mysql.connector

        conn = mysql.connector.connect(
            host= host,
            user= user,
            password= pwd,
            database= database
        )

        query = "SELECT * FROM machine_resources_latest WHERE Time_Stamp >= NOW() - INTERVAL 1 DAY"
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        data = cursor.fetchall()
        conn.close()
        return data


    if __name__ == "__main__":
        main()