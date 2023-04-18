import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
import requests
import ta
from pytrends.request import TrendReq
import plotly.express as px
import geopandas as gpd

st.title('Stock Recommendation System')


# Create a text input for the user to enter a stock name
ticker = st.text_input('Enter a stock name (e.g. Apple)')


if ticker != '':

    def getTicker(company_name):
        yfinance = "https://query2.finance.yahoo.com/v1/finance/search"
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        params = {"q": company_name, "quotes_count": 1, "country": "United States"}

        res = requests.get(url=yfinance, params=params, headers={'User-Agent': user_agent})
        data = res.json()

        company_code = data['quotes'][0]['symbol']
        return company_code

    Stock_code = getTicker(ticker)

    # If Stock_code is not None, create a Ticker object and get data
    if Stock_code:
        # Define Stock_code before creating the Ticker object
        ticker_data = yf.Ticker(Stock_code)
        # Do something with the ticker_data object
        time_period = st.selectbox('Select Time Period:', ('1d', '5d', '1mo', '3mo', '6mo', '1y', '5y', 'max'))
        ticker_df = ticker_data.history(period=time_period)

        # Add a 50-day moving average to the price chart
        ticker_df['MA50'] = ta.trend.sma_indicator(ticker_df['Close'], window=50)

        fig = go.Figure(data=[go.Candlestick(x=ticker_df.index,
                                            open=ticker_df['Open'],
                                            high=ticker_df['High'],
                                            low=ticker_df['Low'],
                                            close=ticker_df['Close']),
                            go.Scatter(x=ticker_df.index, y=ticker_df['MA50'], name='MA50')])

        fig.update_layout(title=f"{ticker} Stock Price - {time_period} Time Period",
                        xaxis_title='Date',
                        yaxis_title='Price')
        st.plotly_chart(fig)


        # Get historical data of the S&P 500 index
        sp500_df = yf.download('^GSPC', start=ticker_df.index[0], end=ticker_df.index[-1], progress=False)

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=ticker_df.index, y=ticker_df['Close'], name=ticker))
        fig2.add_trace(go.Scatter(x=sp500_df.index, y=sp500_df['Close'], name='S&P 500'))

        fig.update_layout(title=f"{ticker} vs S&P 500 - {time_period} Time Period",
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
        df = pytrend.interest_by_region()

        # Sort the data in descending order by the interest value
        df = df.sort_values(by=[company_name], ascending=False)

        # Display the data
        st.write(f'Interest by region for "{company_name}" :')
        st.write(df)



        pytrend = TrendReq()
        # Get realtime Google Trends data
        df = pytrend.trending_searches(pn='united_states')
        st.write("Top searches across USA right now!")
        st.write(df)

        
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

  


        # Get stock price and percentage change
        stock_info = yf.Ticker(Stock_code).info
        stock_price = round(stock_info["regularMarketPreviousClose"], 2)
        percent_change = (stock_info["regularMarketPreviousClose"] - stock_info["regularMarketOpen"]) / stock_info["regularMarketPreviousClose"]

        # Get related queries for the stock
        pytrends.build_payload(kw_list=[company_name], timeframe='today 5-y')
        related_queries = pytrends.related_queries()
        top_queries = related_queries[company_name]['top']

        # Display top 5 related queries and stock price/percentage change in a table
        st.write(f"Stock price for {company_name}: {stock_price}")
        st.write(f"Percentage change for {company_name}: {percent_change}%")
        st.write(f"Top 5 related queries for {company_name}:")
        st.table(top_queries.head())

        # Get rising queries for the stock
        pytrends.build_payload(kw_list=[company_name], timeframe='today 5-y')
        rising_queries = pytrends.related_queries()[company_name]['rising']

        # Display top 5 rising queries in a table
        st.write(f"Top 5 rising queries for {company_name}:")
        st.table(rising_queries.head())




        st.write("Top related stocks!")
        # Get related topics for the stock
        pytrends.build_payload(kw_list=[Stock_code], timeframe='today 5-y')
        related_topics = pytrends.related_topics()[Stock_code]['rising']
        
        top_topics = related_topics.head(5)['topic_title'].tolist()
        
        # Display dropdown menu with related stocks
        st.write(f"Select a related stock for {Stock_code}:")
        selected_topic = st.selectbox("", top_topics)




    else:
        st.write("Couldn't find a stock with that name. Please try again.")
else:
    st.write("Please enter a stock name.")




