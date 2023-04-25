import os
import json
import boto3
import requests
import streamlit as st
from dotenv import load_dotenv
from requests.exceptions import HTTPError
from fastapi.security import OAuth2PasswordBearer

load_dotenv()
app_status = os.environ.get('APP_STATUS')

if app_status == "DEV":
    BASE_URL = "http://localhost:8000"
elif app_status == "PROD":
    BASE_URL = "http://:8000"

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
    
    stock_data_button = st.button('Pull Stock Data !!!')
    if stock_data_button:
        with st.spinner("Wait.."):
            try:
                response = requests.get(f"{BASE_URL}/stock-data-scrape", headers={'Authorization' : f"Bearer {st.session_state['access_token']}"})
            except:
                st.error("Service is unavailable at the moment !!")
                st.error("Please try again later")
                st.stop()
            
            if response.status_code == 200:
                st.success("Successfully pulled Stock Data")
                merged_data = response.text
        
        recommend_stock = st.button('Recommend Stocks!!!')
        if recommend_stock:
            with st.spinner("Wait.."):
                try:
                    response = requests.get(f"{BASE_URL}/stock-recommendation", data=merged_data, headers={'Authorization' : f"Bearer {st.session_state['access_token']}"})
                except:
                    st.error("Service is unavailable at the moment !!")
                    st.error("Please try again later")
                    st.stop()
                
                if response.status_code == 200:
                    st.success("Successfully pulled Stock Data")
                    recommended_stock = json.loads(response.text)
                
            generate_newsletter = st.button('Generate Custom Newsletter!!!')
            if generate_newsletter:
                with st.spinner("Wait.."):
                    try:
                        response = requests.get(f"{BASE_URL}/stock-newsletter", data=recommended_stock, headers={'Authorization' : f"Bearer {st.session_state['access_token']}"})
                    except:
                        st.error("Service is unavailable at the moment !!")
                        st.error("Please try again later")
                        st.stop()
                    
                    if response.status_code == 200:
                        st.success("Successfully pulled Stock Data")
                        newsletter = response.text

else:
    st.header("Please login to access this feature.")

with st.sidebar:
    if st.session_state and st.session_state.logged_in and st.session_state.username:
        st.write(f'Current User: {st.session_state.username}')
    else:
        st.write('Current User: Not Logged In')
    
    response = requests.get(f"{BASE_URL}/user/details?username={st.session_state.username}", headers={'Authorization' : f"Bearer {st.session_state['access_token']}"})
    if response.status_code == 200:
        user_plan = json.loads(response.text)
        st.write("Your plan: ", user_plan[0])
    else:
        st.write('')

    logout_button = st.button('Log Out')
    if logout_button:
        st.session_state.logged_in = False
        st.experimental_rerun()
