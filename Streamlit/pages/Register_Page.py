import os
import re
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

if st.session_state.logged_in == False:
    st.header("Signup Page !!!")
    st.write("Create a new user account to get started !!!")

    full_name = st.text_input("Full Name", placeholder = 'Full Name', key = "full_Name")
    if not full_name:
        st.markdown("<span style='color:red'>Please enter a Full Name.</span>", unsafe_allow_html=True)

    email = st.text_input("Email", placeholder = 'Email', key = "email")
    if not email:
        st.markdown("<span style='color:red'>Please enter a email.</span>", unsafe_allow_html=True)
    elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        st.markdown("<span style='color:red'>Please enter a valid email address.</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color:green'>Email address is valid.</span>", unsafe_allow_html=True)

    username = st.text_input("Username", placeholder = 'Username', key = "username")
    if not username:
        st.markdown("<span style='color:red'>Please enter a username.</span>", unsafe_allow_html=True)
    elif len(username) < 4 or len(username) > 20:
        st.markdown("<span style='color:red'>Username must be between 4 and 20 characters long.</span>", unsafe_allow_html=True)
    elif not re.match("^[a-zA-Z0-9]+$", username):
        st.markdown("<span style='color:red'>Username can only contain letters (both upper and lowercase) and numbers</span>", unsafe_allow_html=True)
    elif username[0] == "_" or username[0] == "-" or username[-1] == "_" or username[-1] == "-":
        st.markdown("<span style='color:red'>Username cannot start or end with an underscore or hyphen.</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color:green'>Username is valid.</span>", unsafe_allow_html=True)

    password = st.text_input("Password", placeholder = 'Password', type = 'password', key = "password")
    password_regex = "^[a-zA-Z0-9]{8,}$"
    personal_info = [username, email]
    if not password:
        st.markdown("<span style='color:red'>Please enter a password.</span>", unsafe_allow_html=True)
    elif len(password) < 8:
        st.markdown("<span style='color:red'>Password must be at least 8 characters long.</span>", unsafe_allow_html=True)
    elif not re.match(password_regex, password):
        st.markdown("<span style='color:red'>Password can only contain letters (both upper and lowercase) and numbers.</span>", unsafe_allow_html=True)
    elif any(info.lower() in password.lower() for info in personal_info):
        st.markdown("<span style='color:red'>Password cannot contain your username or email.</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color:green'>Password is valid.</span>", unsafe_allow_html=True)

    confirm_password = st.text_input("Confirm Password", type = "password", key = "confirm_password")
    if password != confirm_password:
        st.markdown("<span style='color:red'>Passwords do not match.</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color:green'>Both password matches.</span>", unsafe_allow_html=True)

    plans = [{'name': 'Free','details': ''},
            {'name': 'Premium','details': '30 API requests hourly'}]

    user = st.selectbox("Please choose User Type:",['User', 'Admin'])

    if user == 'User':
        selected_plan = st.selectbox('Select a plan', [f"{plan['name']} - {plan['details']}" for plan in plans])
        if selected_plan == "Free - ":
            calls_remaining = 10
        elif selected_plan == "Premium - 30 API requests hourly":
            calls_remaining = 50
    else:
        selected_plan = 'Premium'
        calls_remaining = 100

    register_submit = st.button('Register')

    if register_submit:
        with st.spinner("Wait.."):        
            try:
                st.session_state.username = username
                st.session_state.password = password
                register_user = {
                    'full_name': full_name,
                    'email': email,
                    'username': username,
                    'password': password,
                    'plan': selected_plan[0],
                    'user_type': user,
                    'calls_remaining': calls_remaining
                }
                response = requests.post(url=f'{BASE_URL}/user/create', json = register_user)
                write_logs(f"Requesting fastapi update endpoint to create a new user {username}")

                if response.status_code == 200:
                    write_api_logs("API endpoint: /user/create\n Called by: " + st.session_state.username + " \n Response: 200 \nUser registered successfully")
                    st.success("Account created successfully !!")
                    st.info("Now login using your ID.")
                    if st.button('Login Page'):
                        switch_page('Login_Page')
                
                elif response.status_code == 400:
                    write_api_logs("API endpoint: /user/create\n Called by: " + st.session_state.username + " \n Response: 400 \nUser already exists")
                    st.warning("User already exists !!")
                    st.info("Please login using your ID.")
                    if st.button('Login Page'):
                        switch_page('Login_Page')
                
                else:
                    st.error("Error: User registration failed!")

            except:
                st.error("Service is unavailable at the moment !!")
                st.error("Please try again later")
                st.stop()
