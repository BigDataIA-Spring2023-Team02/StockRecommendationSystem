import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
import requests
import ta

st.title('Stock Price App')

# Create a text input for the user to enter a stock name
ticker = st.text_input('Enter a stock name (e.g. Apple)')


# Main section for user-selected stock
ticker_data = yf.Ticker(ticker)
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
st.markdown(f'[Yahoo Finance Page](https://finance.yahoo.com/quote/{ticker})')

