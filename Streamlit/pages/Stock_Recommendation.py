import os
import json
import time
import boto3
import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit_extras.switch_page_button import switch_page

load_dotenv()
app_status = os.environ.get('APP_STATUS')

if app_status == "DEV":
    BASE_URL = "http://localhost:8000"
elif app_status == "PROD":
    BASE_URL = "http://:8000"

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

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.access_token = ''
    st.session_state.username = ''
    st.session_state.password = ''

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

if st.session_state.logged_in == True:
    st.title("Stock Recommendation Tool !!!")
    
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
            
            ask_upgrade_button = st.button('Want to Upgrade Plan !!!')
            if ask_upgrade_button:
                switch_page('Upgrade_Plan')
            
            logout_button = st.button('Log Out')
            if logout_button:
                st.session_state.logged_in = False
                st.experimental_rerun()
        else:
            st.write('Current User: Not Logged In')
            st.experimental_rerun()

    stock_data_button = st.button('Pull Stock Data !!!')
    if stock_data_button:
        with st.spinner("Wait.."):
            try:
                response = requests.get(f"{BASE_URL}/stock-data-scrape", headers={'Authorization' : f"Bearer {st.session_state['access_token']}"})
                write_logs(f"Pulling Stock data from Yahoo Finance for 10 Stocks")
                
                if response.status_code == 200:
                    write_api_logs("API endpoint: /stock-data-scrape\n Called by: " + st.session_state.username + " \n Response: 200 \nPulled Stock data successfully")
                    st.success("Successfully pulled Stock Data")
                    merged_data = response.text
                elif response.status_code == 401:
                    st.error("Session token expired, please login again")
                    write_api_logs("API endpoint: /stock-data-scrape\n Called by: " + st.session_state.username + " \n Response: 401 \nSession token expired")
                    st.stop()
                else:
                    st.error("Something went wrong, please try again later")

            except:
                st.error("Service is unavailable at the moment !!")
                st.error("Please try again later")
                st.stop()
            
        st.write(merged_data)

    recommend_stock = st.button('Recommend Stocks!!!')
    if recommend_stock:
        with st.spinner("Wait.."):
            try:
                response = requests.get(f"{BASE_URL}/stock-recommendation", headers={'Authorization' : f"Bearer {st.session_state['access_token']}"})
                write_logs(f"Recommending Top 5 Stocks")
                
                if response.status_code == 200:
                    write_api_logs("API endpoint: /stock-recommendation\n Called by: " + st.session_state.username + " \n Response: 200 \nRecommended Top 5 stocks successfully")
                    st.success("Recommended stocks")
                    recommended_stock = json.loads(response.text)
                elif response.status_code == 401:
                    st.error("Session token expired, please login again")
                    write_api_logs("API endpoint: /stock-recommendation\n Called by: " + st.session_state.username + " \n Response: 401 \nSession token expired")
                    st.stop()
                else:
                    st.error("Something went wrong, please try again later")

            except:
                st.error("Service is unavailable at the moment !!")
                st.error("Please try again later")
                st.stop()

        st.write(recommend_stock)

    generate_newsletter = st.button('Generate Custom Newsletter!!!')
    if generate_newsletter:
        with st.spinner("Wait.."):
            try:
                response = requests.get(f"{BASE_URL}/stock-newsletter", headers={'Authorization' : f"Bearer {st.session_state['access_token']}"})
                write_logs(f"Generating Custom Newsletter")
                
                if response.status_code == 200:
                    write_api_logs("API endpoint: /stock-newsletter\n Called by: " + st.session_state.username + " \n Response: 200 \nSent custom generated newsletter to user")
                    st.success("Sent custom newsletter mail")
                    newsletter = response.text
                elif response.status_code == 401:
                    st.error("Session token expired, please login again")
                    write_api_logs("API endpoint: /stock-newsletter\n Called by: " + st.session_state.username + " \n Response: 401 \nSession token expired")
                    st.stop()
                else:
                    st.error("Something went wrong, please try again later")

            except:
                st.error("Service is unavailable at the moment !!")
                st.error("Please try again later")
                st.stop()
        
        st.write(newsletter)

else:
    st.header("Please login to access this feature.")
