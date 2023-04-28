import os
import json
import time
import boto3
import requests
import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.express as px
import plotly.graph_objs as go
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

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.access_token = ''
    st.session_state.username = ''
    st.session_state.password = ''


def stock_code_plot(ticker_symbols):
    time_period = '1y'
    fig1 = go.Figure()
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
    
    # Loop over the list of ticker symbols
    for i, ticker_symbol in enumerate(ticker_symbols):
        ticker_data = yf.Ticker(ticker_symbol)
        ticker_df = ticker_data.history(period = time_period)
        ticker_info = ticker_data.info
        company_name = ticker_info['longName']
        
        fig1.add_trace(go.Candlestick(x = ticker_df.index,
                                      open = ticker_df['Open'],
                                      high = ticker_df['High'],
                                      low = ticker_df['Low'],
                                      close = ticker_df['Close'],
                                      increasing_line_color = colors[i % len(colors)],
                                      decreasing_line_color = colors[i % len(colors)],
                                      name = f"{ticker_symbol} - {company_name}"))
    fig1.update_layout(title = f"Stock Prices - {time_period} Time Period",
                       xaxis_title = 'Date',
                       yaxis_title = 'Price')
    st.plotly_chart(fig1)




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
                    merged_data = json.loads(response.text)
                    
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
            

                
                

            
    recommend_stock = st.button('Recommend Stocks!!!')
    if recommend_stock:
        with st.spinner("Wait.."):
            try:
                response = requests.get(f"{BASE_URL}/stock-recommendation", headers={'Authorization' : f"Bearer {st.session_state['access_token']}"})
                write_logs(f"Recommending Top 5 Stocks")
                
                if response.status_code == 200:
                    write_api_logs("API endpoint: /stock-recommendation\n Called by: " + st.session_state.username + " \n Response: 200 \nRecommended Top 5 stocks successfully")
                    st.success("Recommended stocks")


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

            recommended_stock = json.loads(response.text)

            # Convert the list of dictionaries to a pandas DataFrame
            df = pd.DataFrame.from_records(recommended_stock)


            # Display the DataFrame in Streamlit
            st.write(df)
            # Create a new column 'color' that maps positive and negative values to green and red, respectively
            df['color'] = df['predicted_next_week_return'].apply(lambda x: 'green' if x >= 0 else 'red')

            # Define a dictionary that maps color values to their corresponding color codes
            color_map = {'green': 'rgb(50,205,50)', 'red': 'rgb(255,0,0)'}

            # Create a histogram and color the bars based on the 'color' column using the color_map dictionary
            fig = px.histogram(df, x='symbol', y='predicted_next_week_return', color='color', 
                            color_discrete_map=color_map)

            # Display the histogram in Streamlit
            st.plotly_chart(fig)
            # Assuming df is the pandas DataFrame containing the data
            st.subheader("Recommended stocks Graph!")
            symbols_list = df["symbol"].tolist()
            stock_code_plot(symbols_list)     

            

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
