import os
import time
import json
import boto3
import requests
import yfinance as yf
import streamlit as st
import plotly.express as px
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import plotly.graph_objs as go
from pytrends.request import TrendReq
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

def getTicker(company_name):
    yfinance = "https://query2.finance.yahoo.com/v1/finance/search"
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    params = {"q": company_name, "quotes_count": 1, "country": "United States"}

    res = requests.get(url = yfinance, params = params, headers = {'User-Agent': user_agent})
    data = res.json()

    company_code = data['quotes'][0]['symbol']
    return company_code

def stock_code_plot(ticker_data):
    time_period = st.selectbox('Select Time Period:', ('1d', '5d', '1mo', '3mo', '6mo', '1y', '5y', 'max'))
    ticker_df = ticker_data.history(period = time_period)

    # Add a 50-day moving average to the price chart
    ticker_df['MA50'] = ticker_df['Close'].rolling(window=50).mean()

    fig1 = go.Figure(data = [go.Candlestick(x = ticker_df.index,
                                        open = ticker_df['Open'],
                                        high = ticker_df['High'],
                                        low = ticker_df['Low'],
                                        close = ticker_df['Close']),
                            go.Scatter(x = ticker_df.index, y = ticker_df['MA50'], name = 'MA50')])
    fig1.update_layout(title = f"{Stock_code} Stock Price - {time_period} Time Period",
                        xaxis_title = 'Date',
                        yaxis_title = 'Price')
    st.plotly_chart(fig1)

    # # Get historical data of the S&P 500 index
    # sp500_df = yf.download('^GSPC', start = ticker_df.index[0], end = ticker_df.index[-1], progress = False)

    # fig2 = go.Figure()
    # fig2.add_trace(go.Scatter(x = ticker_df.index, y = ticker_df['Close'], name = ticker))
    # fig2.add_trace(go.Scatter(x = sp500_df.index, y = sp500_df['Close'], name = 'S&P 500'))
    # fig2.update_layout(title = f"{ticker} vs S&P 500 - {time_period} Time Period",
    #                     xaxis_title = 'Date',
    #                     yaxis_title = 'Price')
    # st.plotly_chart(fig2)

    # Link to Yahoo Finance page
    write_logs(f"Returning Yahoo Finance Page for {Stock_code}")
    st.subheader(f'[Yahoo Finance Page for {Stock_code}](https://finance.yahoo.com/quote/{Stock_code})')

def stock_code_tables(Stock_code):
    #Ticker symbol to Ticker Name Concersion
    msft = yf.Ticker(Stock_code)
    company_name = msft.info['longName']
    user_input = company_name

    try:
        # Create a pytrends object and get the data
        pytrends = TrendReq()
        pytrends.build_payload([user_input])
        trends_data = pytrends.interest_over_time()
        fig = px.line(trends_data, x = trends_data.index, y = user_input, title = f'{user_input} Google Trends Data')
        st.plotly_chart(fig)
    except Exception as e:
        st.write("Sorry Too many google trend requests (or) There are no trends to show for this")


    try:
        # Create a pytrends object and get the data for interest by region    
        pytrends.build_payload(kw_list = [company_name])
        df_region = pytrends.interest_by_region()
        df_region = df_region.sort_values(by = [company_name], ascending = False)
        st.write(f'Interest by region for "{company_name}" :')
        st.write(df_region)
    except Exception as e:
        st.write("Sorry Too many google trend requests (or) There are no interest for this stock in any region")
        

    try:
        # Get related queries for the stock
        pytrends.build_payload(kw_list=[company_name], timeframe='today 5-y')
        related_queries = pytrends.related_queries()
        top_queries = related_queries[company_name]['top']

        # Display top 5 related queries in a table
        write_logs(f"Top 5 related queries for {company_name}:")
        st.write(f"Top 5 related queries for {company_name}:")
        st.table(top_queries.head())

        # Get rising queries for the stock
        pytrends.build_payload(kw_list=[company_name], timeframe='today 5-y')
        rising_queries = pytrends.related_queries()[company_name]['rising']

        # Display top 5 rising queries in a table
        write_logs(f"Top 5 rising queries for {company_name}")
        st.write(f"Top 5 rising queries for {company_name}:")
        st.table(rising_queries.head())
    except Exception as e:
        st.write("Sorry Too many google trend requests (or) There are no related top and rising queries for this stock")
        


if st.session_state.logged_in == True:
    st.title("Market Mavericks: Your Captivating Digest!!!")

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

    st.subheader("Most active stocks today")

    header = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9'
        }

    response = requests.get('https://finance.yahoo.com/most-active/', headers = header)
    soup = BeautifulSoup(response.content, 'lxml')
    write_logs(f"Calling Yahoo Finance API")

    # Create a list to hold the options for the radio button
    options = []
    for item in soup.select('.simpTblRow')[:5]:
        stock_info = yf.Ticker(item.select('[aria-label=Symbol]')[0].get_text()).info
        stock_price = round(stock_info["currentPrice"], 2)
        percent_change = round((stock_info["currentPrice"] - stock_info["regularMarketPreviousClose"]) * 100 / stock_info["regularMarketPreviousClose"], 2)

        # Ticker symbol to Ticker Name Conversion
        msft = yf.Ticker(item.select('[aria-label=Symbol]')[0].get_text())
        company_name = msft.info['longName']

        # Add the option to the list
        option = f"{company_name} -- {item.select('[aria-label=Symbol]')[0].get_text()}: Stock Price: {stock_price} Per change: {percent_change}"
        options.append(option)

    # Display the radio button
    selected_option = st.radio("Select a stock:", options)
    selected_stock = selected_option.split(" -- ")[0]
    st.write('')
    st.write("If your stock is not mentioned above please enter the company name below")

    # Create a text input for the user to enter a stock name
    ticker = st.text_input('Enter a stock name (e.g. Apple)')

    if ticker != '':
        try:
            Stock_code = getTicker(ticker)
        except IndexError:
            st.error("The quotes list is empty or does not contain a valid symbol.")
        except NameError:
            st.error("Stock_code is not defined.")
        except Exception as e:
            st.error("An error occurred while getting the ticker: " + str(e))

    else:
        Stock_code = getTicker(selected_stock)
        write_logs(f"Stock Code selected {Stock_code}")

    if Stock_code:
        ticker_data = yf.Ticker(Stock_code)
        stock_info = ticker_data.info
        stock_price = round(stock_info["currentPrice"], 2)
        percent_change = round((stock_info["currentPrice"] - stock_info["regularMarketOpen"]) / stock_info["regularMarketOpen"],5)
        marketCap = stock_info["marketCap"]
        write_logs(f"Giving Details of {Stock_code}: Stock price: {stock_price} Percentage change: {percent_change}% Market Cap: {marketCap}")

        st.write(f"Stock code: {Stock_code}")
        st.write(f"""Stock price: {stock_price}
                    \n Percentage change: {percent_change} %
                    \n Market Cap: {marketCap}""")
        st.write('')

    else:
        write_logs(f"Couldn't find a stock with the name {Stock_code}")
        st.write("Couldn't find a stock with that name. Please try again.")

    selected_option = st.radio("Select a option to view:", ['Plots', 'Trends Data'], horizontal = True)
    if selected_option == 'Plots':
        with st.spinner('Loading...'):
            stock_code_plot(ticker_data)

    else:
        with st.spinner('Loading...'):
            stock_code_tables(Stock_code)

else:
    st.header("Please login to access this feature.")
