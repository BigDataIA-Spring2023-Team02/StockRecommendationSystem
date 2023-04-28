import os
import json
import time
import boto3
import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit_extras.switch_page_button import switch_page

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

with st.sidebar:
    if st.session_state and st.session_state.logged_in and st.session_state.username:
        st.write(f'Current User: {st.session_state.username}')
    else:
        st.write('Current User: Not Logged In')

if st.session_state.logged_in == False:
    st.title("Market Mavericks: Your Captivating Digest!!!")
    st.header("Login Page !!!")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_button = st.button('Log In !!!')
    forgot_password = st.button('Forgot Password')

    if login_button:
        if username == '' or password == '':
            st.warning("Please enter username and password")
        else:
            with st.spinner("Wait.."):
                payload = {'username': username, 'password': password}
                
                try:
                    response = requests.post(f"{BASE_URL}/login", data=payload)
                    write_logs(f"Requesting fastapi login endpoint to use the application as {username}")

                    if response.status_code == 200:
                        st.success("Logged in successfully as {}".format(username))
                        json_data = json.loads(response.text)
                        st.session_state.logged_in = True
                        st.session_state.access_token = json_data['access_token']
                        st.session_state.username = username
                        st.success("Login successful")
                        write_api_logs("API endpoint: /login\n Called by: " + st.session_state.username + " \n Response: 200 \nLogged in Successfully")
                    
                    elif response.status_code == 401:
                        st.warning('Please register yourself first.')
                        write_api_logs("API endpoint: /login\n Called by: " + st.session_state.username + " \n Response: 401 \nRegister the user first")
                    
                    else:
                        st.error("""Incorrect username or password entered !! \n Please check again your user credentails !!""")
                        
                except:
                    st.error("Service is unavailable at the moment !!")
                    st.error("Please try again later")
                    st.stop()

    if forgot_password:
        write_logs(f"Switching to forgot password page to change the password")
        switch_page('Forgot_Password')

if st.session_state.logged_in == True:
    with st.spinner("Loading..."):
        write_logs(f"Opening Stock Dashboard")
        switch_page('Stock_Dashboard')
