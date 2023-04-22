import os
import json
import boto3
import requests
import streamlit as st
from dotenv import load_dotenv
from requests.exceptions import HTTPError
from fastapi.security import OAuth2PasswordBearer

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

load_dotenv()
app_status = os.environ.get('APP_STATUS')

if app_status == "DEV":
    BASE_URL = "http://localhost:8001"
elif app_status == "PROD":
    BASE_URL = "http://:8001"

def login_page():
    st.title("Stock Recommendation Tool !!!")
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
                except:
                    st.error("Service is unavailable at the moment !!")
                    st.error("Please try again later")
                    st.stop()
            if response.status_code == 200:
                st.success("Logged in successfully as {}".format(username))
                json_data = json.loads(response.text)
                st.session_state.logged_in = True
                st.session_state.access_token = json_data['access_token']
                st.session_state.username = username
                st.success("Login successful")
                st.experimental_rerun()
            elif response.status_code == 401:
                st.session_state.page = 'Register_Page'
            else:
                st.error("Incorrect username or password entered !!")
                st.error("Please check again your user credentails !!")

    if forgot_password:
        st.session_state.page = 'Forgot_Password'

    with st.sidebar:
        if st.session_state and st.session_state.logged_in and st.session_state.username:
            st.write(f'Current User: {st.session_state.username}')
        else:
            st.write('Current User: Not Logged In')

def main():
    if 'page' not in st.session_state:
        st.session_state.page = 'Login'
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.access_token = ''
        st.session_state.full_name = ''
        st.session_state.email = ''
        st.session_state.username = ''
        st.session_state.password = ''

    pages = {
        "Login": login_page,
        # Add other page functions here, e.g. "Register": register_page, "Forgot_Password": forgot_password_page
    }

    pages[st.session_state.page]()


if __name__ == "__main__":
    main()
