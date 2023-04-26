import os
import re
import time
import boto3
import requests
import streamlit as st
from dotenv import load_dotenv

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

st.header("Reset Password Page !!!")

user = st.text_input("Username")
new_password = st.text_input("Password", type="password")
personal_info = [user]
if len(new_password) < 8:
    st.warning("Password must be at least 8 characters long.")
elif not re.match("^[a-zA-Z0-9!@#$%^&*()_+{}\[\]:;\"'<,>.?/\|`~-]+$", new_password):
    st.warning("Password can only contain letters (both upper and lowercase), numbers, and special characters.")
elif any(info.lower() in new_password.lower() for info in personal_info):
    st.warning("Password cannot contain any part of your personal information.")
elif new_password.lower() in new_password.lower():
    st.warning("Password cannot contain your username.")
else:
    st.success("Password is valid.")

confirm_password = st.text_input("Confirm Password", type="password")
if new_password != confirm_password:
    st.warning("New password and confirm password must match")

reset_button = st.button('Update Password !!!')

if reset_button:
    with st.spinner("Resetting Password..."):
        
        if user == '' or new_password == '' or confirm_password == '':
            st.warning("Please enter all fields")
        
        else:
            payload = {'new_password': new_password}
            headers = {'Authorization': f'Bearer {st.session_state["access_token"]}'}
            
            try:
                response = requests.patch(f"{BASE_URL}/user/update?username={user}", json=payload)
                write_logs(f"Requesting fastapi update endpoint to update the password for {user}")

                if response.status_code == 200:
                    st.success("Password reset successfully")
                    write_api_logs("API endpoint: /user/update\n Called by: " + st.session_state.username + " \n Response: 200 \nPassword updated successfuly")
                    st.experimental_rerun()

                elif response.status_code == 401:
                    st.error("Incorrect current password entered !!")
                    write_api_logs("API endpoint: /user/update\n Called by: " + st.session_state.username + " \n Response: 401 \nIncorrect Password set")

                else:
                    st.error("Failed to reset password")
                    write_api_logs("API endpoint: /user/update\n Called by: " + st.session_state.username + " \n Response: 404 \nFailed to reset password")

            except:
                st.error("Service is unavailable at the moment !!")
                st.error("Please try again later")
                st.stop()
