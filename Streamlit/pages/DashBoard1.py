import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
import requests
import ta
from pytrends.request import TrendReq
import plotly.express as px
from bs4 import BeautifulSoup
import requests

def getTicker(company_name):
    yfinance = "https://query2.finance.yahoo.com/v1/finance/search"
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    params = {"q": company_name, "quotes_count": 1, "country": "United States"}

    res = requests.get(url=yfinance, params=params, headers={'User-Agent': user_agent})
    data = res.json()

    company_code = data['quotes'][0]['symbol']
    return company_code


st.title('Stock Recommendation System')



st.subheader("Most active stocks today")

url='https://finance.yahoo.com/most-active/'

header = {
	'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9'
}
response=requests.get(url,headers=header)

soup = BeautifulSoup(response.content, 'lxml')

import streamlit as st
import yfinance as yf
from bs4 import BeautifulSoup
import requests

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
    option = f"{company_name}__{item.select('[aria-label=Symbol]')[0].get_text()}: Stock Price:  {stock_price} Per change:   {percent_change}"
    options.append(option)

# Display the radio button
selected_option = st.radio("Select a stock:", options)
selected_stock = selected_option.split("__")[0]
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


    # If Stock_code is not None, create a Ticker object and get data
    if Stock_code:
        # Define Stock_code before creating the Ticker object
        ticker_data = yf.Ticker(Stock_code)

        # Get stock price and percentage change
        stock_info = yf.Ticker(Stock_code).info
        stock_price = round(stock_info["currentPrice"], 2)
        percent_change = (stock_info["currentPrice"] - stock_info["regularMarketOpen"]) / stock_info["regularMarketOpen"]
        marketCap = stock_info["marketCap"]
        #trailingPE = stock_info["trailingPE"]


        # Display top 5 related queries and stock price/percentage change in a table
        st.write(f"Stock price for {ticker}: {stock_price}")
        st.write(f"Percentage change for {ticker}: {percent_change}%")
        st.write(f"Market Cap for {ticker}: {marketCap}")
        #st.write(f"Price to earnings ratio for {ticker}: {trailingPE}")





        # Do something with the ticker_data object
        time_period = st.selectbox('Select Time Period:', ('1d', '5d', '1mo', '3mo', '6mo', '1y', '5y', 'max'))
        ticker_df = ticker_data.history(period=time_period)

        # Add a 50-day moving average to the price chart
        ticker_df['MA50'] = ta.trend.sma_indicator(ticker_df['Close'], window=50)

        fig1 = go.Figure(data=[go.Candlestick(x=ticker_df.index,
                                            open=ticker_df['Open'],
                                            high=ticker_df['High'],
                                            low=ticker_df['Low'],
                                            close=ticker_df['Close']),
                                go.Scatter(x=ticker_df.index, y=ticker_df['MA50'], name='MA50')])

        fig1.update_layout(title=f"{ticker} Stock Price - {time_period} Time Period",
                            xaxis_title='Date',
                            yaxis_title='Price')
        
        st.plotly_chart(fig1)

        # Get historical data of the S&P 500 index
        sp500_df = yf.download('^GSPC', start=ticker_df.index[0], end=ticker_df.index[-1], progress=False)

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=ticker_df.index, y=ticker_df['Close'], name=ticker))
        fig2.add_trace(go.Scatter(x=sp500_df.index, y=sp500_df['Close'], name='S&P 500'))

        fig2.update_layout(title=f"{ticker} vs S&P 500 - {time_period} Time Period",
                            xaxis_title='Date',
                            yaxis_title='Price')
        st.plotly_chart(fig2)




        # Link to Yahoo Finance page
        st.markdown(f'[Yahoo Finance Page](https://finance.yahoo.com/quote/{Stock_code})')



        #Ticker symbol to Ticker Name Concersion
        msft = yf.Ticker(Stock_code)

        company_name = msft.info['longName']


        # Set up the Google Trends API client
        pytrends = TrendReq()

        # Define a function to retrieve Google Trends data for a given search term
        def get_trends_data(search_term):
            pytrends.build_payload(kw_list=search_term)
            trends_data = pytrends.interest_over_time()
            return trends_data

        # Get the user input for the search term
        user_input = company_name


        # Create a pytrends object and get the data
        pytrends = TrendReq()
        pytrends.build_payload([user_input])
        trends_data = pytrends.interest_over_time()

        # Create a line chart of the data
        fig = px.line(trends_data, x=trends_data.index, y=user_input, title=f'{user_input} Google Trends Data')
        st.plotly_chart(fig)




        # Create a pytrends object and get the data for interest by region
        pytrend = TrendReq()
        pytrend.build_payload(kw_list=[company_name])
        df_region = pytrend.interest_by_region()

        # Sort the data in descending order by the interest value
        df_region = df_region.sort_values(by=[company_name], ascending=False)

        # Get realtime Google Trends data
        pytrend = TrendReq()
        df_trending = pytrend.trending_searches(pn='united_states')

        # Display the data side by side
        col1, col2 = st.columns(2)
        with col1:
            st.write(f'Interest by region for "{company_name}" :')
            st.write(df_region)

        with col2:
            st.write("Top searches across USA right now!")
            st.write(df_trending)


        
        # Get related queries for the stock
        pytrends.build_payload(kw_list=[company_name], timeframe='today 5-y')
        related_queries = pytrends.related_queries()
        top_queries = related_queries[company_name]['top']
        
        # Display top 5 related queries in a table
        st.write(f"Top 5 related queries for {company_name}:")
        st.table(top_queries.head())


        # Get rising queries for the stock
        pytrends.build_payload(kw_list=[company_name], timeframe='today 5-y')
        rising_queries = pytrends.related_queries()[company_name]['rising']
        
        # Display top 5 rising queries in a table
        st.write(f"Top 5 rising queries for {company_name}:")
        st.table(rising_queries.head())


    else:
        st.write("Couldn't find a stock with that name. Please try again.")
else:

    ticker = selected_stock
    Stock_code = getTicker(ticker)

    # If Stock_code is not None, create a Ticker object and get data
    if Stock_code:
        # Define Stock_code before creating the Ticker object
        ticker_data = yf.Ticker(Stock_code)

        # Get stock price and percentage change
        stock_info = yf.Ticker(Stock_code).info
        stock_price = round(stock_info["currentPrice"], 2)
        percent_change = (stock_info["currentPrice"] - stock_info["regularMarketOpen"]) / stock_info["regularMarketOpen"]
        marketCap = stock_info["marketCap"]
        #trailingPE = stock_info["trailingPE"]


        # Display top 5 related queries and stock price/percentage change in a table
        st.write(f"Stock price for {ticker}: {stock_price}")
        st.write(f"Percentage change for {ticker}: {percent_change}%")
        st.write(f"Market Cap for {ticker}: {marketCap}")
        #st.write(f"Price to earnings ratio for {ticker}: {trailingPE}")





        # Do something with the ticker_data object
        time_period = st.selectbox('Select Time Period:', ('1d', '5d', '1mo', '3mo', '6mo', '1y', '5y', 'max'))
        ticker_df = ticker_data.history(period=time_period)

        # Add a 50-day moving average to the price chart
        ticker_df['MA50'] = ta.trend.sma_indicator(ticker_df['Close'], window=50)

        fig1 = go.Figure(data=[go.Candlestick(x=ticker_df.index,
                                            open=ticker_df['Open'],
                                            high=ticker_df['High'],
                                            low=ticker_df['Low'],
                                            close=ticker_df['Close']),
                                go.Scatter(x=ticker_df.index, y=ticker_df['MA50'], name='MA50')])

        fig1.update_layout(title=f"{ticker} Stock Price - {time_period} Time Period",
                            xaxis_title='Date',
                            yaxis_title='Price')
        
        st.plotly_chart(fig1)

        # Get historical data of the S&P 500 index
        sp500_df = yf.download('^GSPC', start=ticker_df.index[0], end=ticker_df.index[-1], progress=False)

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=ticker_df.index, y=ticker_df['Close'], name=ticker))
        fig2.add_trace(go.Scatter(x=sp500_df.index, y=sp500_df['Close'], name='S&P 500'))

        fig2.update_layout(title=f"{ticker} vs S&P 500 - {time_period} Time Period",
                            xaxis_title='Date',
                            yaxis_title='Price')


        st.plotly_chart(fig2)


        


        # Link to Yahoo Finance page
        st.markdown(f'[Yahoo Finance Page](https://finance.yahoo.com/quote/{Stock_code})')



        #Ticker symbol to Ticker Name Concersion
        msft = yf.Ticker(Stock_code)

        company_name = msft.info['longName']


        # Set up the Google Trends API client
        pytrends = TrendReq()

        # Define a function to retrieve Google Trends data for a given search term
        def get_trends_data(search_term):
            pytrends.build_payload(kw_list=search_term)
            trends_data = pytrends.interest_over_time()
            return trends_data

        # Get the user input for the search term
        user_input = company_name


        # Create a pytrends object and get the data
        pytrends = TrendReq()
        pytrends.build_payload([user_input])
        trends_data = pytrends.interest_over_time()

        # Create a line chart of the data
        fig = px.line(trends_data, x=trends_data.index, y=user_input, title=f'{user_input} Google Trends Data')
        st.plotly_chart(fig)




        # Create a pytrends object and get the data for interest by region
        pytrend = TrendReq()
        pytrend.build_payload(kw_list=[company_name])
        df_region = pytrend.interest_by_region()

        # Sort the data in descending order by the interest value
        df_region = df_region.sort_values(by=[company_name], ascending=False)

        # Get realtime Google Trends data
        pytrend = TrendReq()
        df_trending = pytrend.trending_searches(pn='united_states')

        # Display the data side by side
        col1, col2 = st.columns(2)
        with col1:
            st.write(f'Interest by region for "{company_name}" :')
            st.write(df_region)

        with col2:
            st.write("Top searches across USA right now!")
            st.write(df_trending)


        
        # Get related queries for the stock
        pytrends.build_payload(kw_list=[company_name], timeframe='today 5-y')
        related_queries = pytrends.related_queries()
        top_queries = related_queries[company_name]['top']
        
        # Display top 5 related queries in a table
        st.write(f"Top 5 related queries for {company_name}:")
        st.table(top_queries.head())


        # Get rising queries for the stock
        pytrends.build_payload(kw_list=[company_name], timeframe='today 5-y')
        rising_queries = pytrends.related_queries()[company_name]['rising']
        
        # Display top 5 rising queries in a table
        st.write(f"Top 5 rising queries for {company_name}:")
        st.table(rising_queries.head())

