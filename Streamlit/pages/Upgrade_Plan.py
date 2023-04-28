import os
import json
import time
import boto3
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv("API_URL", "http://localhost:8000")

clientLogs = boto3.client('logs',
                        region_name='us-east-1',
                        aws_access_key_id = os.environ.get('AWS_LOGS_ACCESS_KEY'),
                        aws_secret_access_key = os.environ.get('AWS_LOGS_SECRET_KEY')
                        )

def write_logs(message: str):
    clientLogs.put_log_events(
        logGroupName = "Stock-Recommendation-System",
        logStreamName = "Streamlit-Logs",
        logEvents = [
            {
                'timestamp' : int(time.time() * 1e3),
                'message' : message
            }
        ]
    )

def write_api_logs(message: str):
    clientLogs.put_log_events(
        logGroupName = "Stock-Recommendation-System",
        logStreamName = "API-Activity-Logs",
        logEvents = [
            {
                'timestamp' : int(time.time() * 1e3),
                'message' : message
            }
        ]
    )

def set_bg_hack_url():
    '''
    A function to unpack an image from url and set as bg.
    Returns
    -------
    The background.
    '''
        
    st.markdown(
         f"""
         <style>
         .stApp {{
             background: url("https://images.unsplash.com/photo-1549421263-6064833b071b?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1965&q=80");
             background-size: cover
         }}
         </style>
         """,
         unsafe_allow_html=True
     )
set_bg_hack_url()    

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.access_token = ''
    st.session_state.username = ''
    st.session_state.password = ''

if st.session_state.logged_in == True:
    st.title("Market Mavericks: Your Captivating Digest!!!")
    st.header('Upgrade Your Plan !!!')

    with st.sidebar:
        if st.session_state and st.session_state.logged_in and st.session_state.username:
            st.write(f'Current User: {st.session_state.username}')
            
            response = requests.get(f"{BASE_URL}/user/details?username={st.session_state.username}", headers={'Authorization' : f"Bearer {st.session_state['access_token']}"})
            if response.status_code == 200:
                write_api_logs("API endpoint: /user/details\n Called by: " + st.session_state.username + " \n Response: 200 \nGetting user details")
                user_plan = json.loads(response.text)
                st.write("Your plan: ", user_plan)
            elif response.status_code == 401:
                st.write("Session token expired, please login again")
                write_api_logs("API endpoint: /user/details\n Called by: " + st.session_state.username + " \n Response: 401 \nSession token expired")
                st.stop()
            else:
                st.write('')
            
            response = requests.get(f"{BASE_URL}/user/remaining_api_calls", headers={'Authorization' : f"Bearer {st.session_state['access_token']}"})
            if response.status_code == 200:
                write_api_logs("API endpoint: /user/remaining_api_calls\n Called by: " + st.session_state.username + " \n Response: 200 \nRemainig API Calls available")
                api_calls = json.loads(response.text)
                st.write("Remaining calls: ", api_calls)
            elif response.status_code == 401:
                st.write("Session token expired, please login again")
                write_api_logs("API endpoint: /user/remaining_api_calls\n Called by: " + st.session_state.username + " \n Response: 401 \nSession token expired")
                st.stop()
            else:
                st.write('')
            
            logout_button = st.button('Log Out')
            if logout_button:
                st.session_state.logged_in = False
                st.experimental_rerun()
        else:
            st.write('Current User: Not Logged In')
            st.experimental_rerun()

    plans = [{'name': 'Free','details': ''},
            {'name': 'Premium','details': '30 API requests hourly'}]
    selected_plan = st.selectbox('Select a plan', [f"{plan['name']} - {plan['details']}" for plan in plans])
    if selected_plan == "Free - ":
        calls_remaining = 10
    elif selected_plan == "Premium - 30 API requests hourly":
        calls_remaining = 50
    selected_plan = selected_plan.split()

    upgrade_button = st.button('Upgrade!!!')
    if upgrade_button:
        response = requests.post(f"{BASE_URL}/user/upgradeplan?plan={selected_plan[0]}&calls_remaining={calls_remaining}", headers={'Authorization' : f"Bearer {st.session_state['access_token']}"})
        
        if response.status_code == 200:
            write_api_logs("API endpoint: /user/upgradeplan\n Called by: " + st.session_state.username + " \n Response: 200 \nPlan upgraded successfully")
            plan_upgraded = json.loads(response.text)
            st.success("Plan upgraded successfully.")
            
        elif response.status_code == 401:
            st.write("Session token expired, please login again")
            write_api_logs("API endpoint: /user/upgradeplan\n Called by: " + st.session_state.username + " \n Response: 401 \nSession token expired")
            st.stop()
        
        else:
            st.write('Error Upgrading your plan')

else:
    st.header("Please login to access this feature.")
