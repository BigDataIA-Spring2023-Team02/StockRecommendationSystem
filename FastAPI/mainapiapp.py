import os
import re
import time
import json
import boto3
import requests
import datetime
import pandas as pd
from time import sleep
import user_data, schemas
from pytest import Session
from fastapi import FastAPI
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from newsapi import NewsApiClient
from sqlalchemy.orm import Session
from http.client import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi import Depends, status,HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from jwt_api import bcrypt, verify, create_access_token, get_current_user
from textblob import TextBlob
from fastapi.encoders import jsonable_encoder
import numpy as np
import json
import textwrap
from fastapi import Depends
from typing import List, Tuple
import openai
from transformers import DistilBertTokenizer
from transformers import Trainer, TrainingArguments
from torch.utils.data import Dataset
import torch
import pickle
from transformers import DistilBertModel, DistilBertTokenizer, DistilBertConfig, PreTrainedModel
from transformers import DistilBertConfig
from pathlib import Path
from transformers import DistilBertConfig, DistilBertForSequenceClassification
from fastapi.middleware.cors import CORSMiddleware
from model import DistilBertForSequenceRegression
from fastapi.responses import JSONResponse



# from your_module import schemas, user_data
# from sqlalchemy.orm import Session



from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import pandas as pd
import pickle
import torch
from transformers import DistilBertTokenizer
from typing import List
import schemas
import user_data

from torch.optim import AdamW



import joblib






load_dotenv()
alpha_vantage_key_id = os.environ.get('ALPHA_VANTAGE_API_KEY')
news_api_key_id = os.environ.get('NEWS_API_KEY')
openai.api_key = os.environ.get('openai.api_key')

app = FastAPI(debug =True)
# Add the CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Load the saved model
model = joblib.load("/Users/ajinabraham/Documents/BigData7245/BigData/fine_tuned_model.pkl")
tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")



#&%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%Recommendation Systems%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Load the fine-tuned model
with open("fine_tuned_model.pkl", "rb") as f:
    model = pickle.load(f)

# Load the tokenizer
tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")

def data_to_text(data):
    text_data = data.apply(lambda x: f"Symbol: {x['symbol']} Daily Return: {x['daily_return']} Sentiment: {x['sentiment']}", axis=1)
    return text_data.tolist()

def predict_next_week_returns(data):
    # Convert data to text
    text_data = data_to_text(data)

    # Tokenize and preprocess the data
    encodings = tokenizer(text_data, padding=True, truncation=True, return_tensors='pt')

    # Predict next week returns using the saved model
    with torch.no_grad():
        model.eval()
        outputs = model(**encodings)
        predictions = outputs[0].detach().numpy()

    return predictions


#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


class StockArticles:
    def __init__(self):
        self.all_articles = []

    def set_articles(self, articles: List[Tuple[str, str, datetime.datetime]]):
        self.all_articles = articles

    def get_articles(self) -> List[Tuple[str, str, datetime.datetime]]:
        return self.all_articles




stock_articles_dependency = StockArticles()





def get_stock_articles() -> StockArticles:
    return stock_articles_dependency


# Authenticate S3 client for logging with your user credentials that are stored in your .env config file
clientLogs = boto3.client('logs',
                        region_name='us-east-1',
                        aws_access_key_id = os.environ.get('AWS_LOGS_ACCESS_KEY'),
                        aws_secret_access_key = os.environ.get('AWS_LOGS_SECRET_KEY')
                        )

def create_gpt_prompt(top_stocks, all_articles_list):
    prompt = "Generate a brief newsletter with key insights related to the top 5 stocks:\n\n"
    stock_names = {
        'AAPL': 'Apple Inc.',
        'MSFT': 'Microsoft Corporation',
        'AMZN': 'Amazon.com, Inc.',
        'GOOGL': 'Alphabet Inc. (Google Class A)',
        'FB': 'Facebook, Inc.',
        'TSLA': 'Tesla, Inc.',
        'JPM': 'JPMorgan Chase & Co.',
        'V': 'Visa Inc.',
        'JNJ': 'Johnson & Johnson',
        'MA': 'Mastercard Incorporated'
    }

    for index, row in top_stocks.iterrows():
        symbol = row['symbol']
        predicted_return = row['predicted_return']
        stock_name = stock_names[symbol]

        # Get the latest article for the stock
        stock_articles = [article for article in all_articles_list if article[0] == symbol]
        if stock_articles:
            latest_article = sorted(stock_articles, key=lambda x: x[2], reverse=True)[0]
            article_text, article_timestamp = latest_article[1], latest_article[2]
            prompt += f"{index + 1}. {stock_name} ({symbol})\n"
            prompt += f"Predicted Return: {predicted_return:.2%}\n"
            prompt += f"Latest Article ({article_timestamp:%Y-%m-%d}): {article_text}\n\n"
        else:
            prompt += f"{index + 1}. {stock_name} ({symbol})\n"
            prompt += f"Predicted Return: {predicted_return:.2%}\n"
            prompt += "No recent news available.\n\n"

    return prompt




def chunkify_prompt(prompt, max_tokens=1000):
    chunks = textwrap.wrap(prompt, max_tokens)
    return chunks

def generate_newsletter(prompt, model_engine="text-davinci-002", max_tokens=1000):
    prompt_chunks = chunkify_prompt(prompt, max_tokens)

    generated_text = ""

    for chunk in prompt_chunks:
        response = openai.Completion.create(
            engine=model_engine,
            prompt=chunk,
            max_tokens=max_tokens,
            n=1,
            stop=None,
            temperature=0.5,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        generated_chunk = response.choices[0].text.strip()
        generated_text += generated_chunk + ' '

    return generated_text.strip()

def write_logs(message: str):
    clientLogs.put_log_events(
        logGroupName = "Stock-Recommendation-System",
        logStreamName = "FastAPI-Logs",
        logEvents = [
            {
                'timestamp' : int(time.time() * 1e3),
                'message' : message
            }
        ]
    )

def custom_encoder(obj):
    if isinstance(obj, np.int64):
        return int(obj)
    elif isinstance(obj, (list, tuple)):
        return [custom_encoder(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: custom_encoder(value) for key, value in obj.items()}
    return obj

def extract_text_from_url(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    paragraphs = soup.find_all('p')
    text = ' '.join([p.get_text() for p in paragraphs])
    return text

@app.post('/login', status_code = status.HTTP_200_OK, tags = ['User'])
async def login(request: OAuth2PasswordRequestForm = Depends(), userdb : Session = Depends(user_data.get_db)):
    user = userdb.query(schemas.User_Table).filter(schemas.User_Table.username == request.username).first()
    if not user:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Invalid Credentials") 
    
    if not verify(user.password, request.password):
                raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Incorrect Password")
    
    access_token = create_access_token(data = {"sub": user.username})
    write_logs(f"User logged in with token {access_token}")
    userdb.close()
    return {"access_token": access_token, "token_type": "bearer"}

@app.post('/user/create', status_code = status.HTTP_200_OK, response_model = schemas.ShowUser, tags = ['User'])
async def create_user(request: schemas.User, userdb : Session = Depends(user_data.get_db)):
    user = userdb.query(schemas.User_Table).filter(schemas.User_Table.username == request.username).first()
    if not user:
        new_user = schemas.User_Table(full_name = request.full_name, email = request.email, 
                                      username = request.username, password = bcrypt(request.password), 
                                      plan = request.plan, user_type = request.user_type, calls_remaining = request.calls_remaining)
        userdb.add(new_user)
        userdb.commit()
        userdb.refresh(new_user)
        userdb.close()
        write_logs(f"Created new user of {new_user}")
        return new_user
        
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User already exists')

@app.patch('/user/update', status_code = status.HTTP_200_OK, response_model = schemas.ShowUser, tags = ['User'])
def update_password(username : str, new_password: schemas.UpdatePassword, userdb : Session = Depends(user_data.get_db)):
    user = userdb.query(schemas.User_Table).filter(username == schemas.User_Table.username).first()
    if not user:
        raise HTTPException(status_code = 404, detail = "User not found")
    
    updated_user = dict(username = username, password = bcrypt(new_password.password))
    for key, value in updated_user.items():
        setattr(user, key, value)
        write_logs(f"Updated password {value} for user {user}")

    userdb.add(user)
    userdb.commit()
    userdb.refresh(user)
    userdb.close()
    return user

@app.get("/user/remaining_api_calls", tags=["User"])
def get_remaining_calls(current_user: schemas.User = Depends(get_current_user), userdb: Session = Depends(user_data.get_db)):
    user = userdb.query(schemas.User_Table).filter(current_user == schemas.User_Table.username).first()
    if not user:
        raise HTTPException(status_code = 404, detail = "User not found")
    
    remaining_calls = user.calls_remaining
    write_logs(f"Remaining {remaining_calls} API calls of {user}")
    return remaining_calls

@app.get('/user/details', status_code = status.HTTP_200_OK, tags = ['User'])
async def user_details(current_user: schemas.User = Depends(get_current_user), userdb : Session = Depends(user_data.get_db)):
    user = userdb.query(schemas.User_Table).filter(current_user == schemas.User_Table.username).first()
    if not user:
        raise HTTPException(status_code = 404, detail = "User not found")
    
    if user.user_type == 'Admin':
        return user.user_type
    
    else:
        plan = user.plan
        return plan

@app.post('/user/upgradeplan', status_code = status.HTTP_200_OK, tags = ['User'])
async def upgrade_plan(plan: str, calls_remaining: int, current_user: schemas.User = Depends(get_current_user), userdb : Session = Depends(user_data.get_db)):
    user = userdb.query(schemas.User_Table).filter(current_user == schemas.User_Table.username).first()
    
    if not user:
        raise HTTPException(status_code = 404, detail = "User not found")
    
    user.plan = plan
    write_logs(f"Upgraded to {plan} plan for user {user}")
    user.calls_remaining = calls_remaining
    write_logs(f"Remaining {calls_remaining} API calls for user {user}")
    
    userdb.commit()
    userdb.refresh(user)
    userdb.close()
    return True

@app.get('/stock-data-scrape', status_code = status.HTTP_200_OK, tags = ['Stock-Data'])
async def stock_data_pull(current_user: schemas.User = Depends(get_current_user), userdb : Session = Depends(user_data.get_db)):
    user = userdb.query(schemas.User_Table).filter(current_user == schemas.User_Table.username).first()
    
    if not user:
        raise HTTPException(status_code = 404, detail = "User not found")
    
    if user.calls_remaining <= 0:
        return ("Your account has reached its call limit. Please upgrade your account to continue using the service.")
    
    user.calls_remaining -= 1
    ## Enter the code for scraping stock data

    # List of top 10 stock symbols (replace with actual symbols)
    top_10_stocks = [
        'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'FB', 'TSLA', 'JPM', 'V', 'JNJ', 'MA'
    ]

    # DataFrame to store stock data
    stock_data = pd.DataFrame()

    for stock in top_10_stocks:
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={stock}&apikey={alpha_vantage_key_id}&outputsize=compact'
        response = requests.get(url)
        data = json.loads(response.text)

        if 'Time Series (Daily)' in data:
            time_series = data['Time Series (Daily)']
            df = pd.DataFrame(time_series).T
            df.reset_index(inplace=True)
            df['symbol'] = stock
            stock_data = stock_data.append(df, ignore_index=True)

        # Alpha Vantage has a limit of 5 requests per minute
        sleep(60 / 5)

    user.calls_remaining -= 1
    # Rename columns
    stock_data.columns = ['date', 'open', 'high', 'low', 'close', 'adjusted_close', 'volume', 'dividend_amount', 'split_coefficient', 'symbol']

    # Filter data for the last 30 days
    stock_data['date'] = pd.to_datetime(stock_data['date'])
    last_30_days = pd.to_datetime('today') - pd.Timedelta(days=30)
    filtered_data = stock_data[stock_data['date'] >= last_30_days]
    filtered_data.to_csv('filtered_data.csv', index=False)

    ################################################### News API ###############################################################################
    newsapi = NewsApiClient(api_key = news_api_key_id)

    stock_names = {
        'AAPL': 'Apple Inc.',
        'MSFT': 'Microsoft Corporation',
        'AMZN': 'Amazon.com, Inc.',
        'GOOGL': 'Alphabet Inc. (Google Class A)',
        'FB': 'Facebook, Inc.',
        'TSLA': 'Tesla, Inc.',
        'JPM': 'JPMorgan Chase & Co.',
        'V': 'Visa Inc.',
        'JNJ': 'Johnson & Johnson',
        'MA': 'Mastercard Incorporated'
    }

    language = 'en'
    sort_by = 'relevancy'
    page_size = 20
    to_date = datetime.date.today()
    from_date = to_date - datetime.timedelta(days=30)
    allowed_domains = 'finance.yahoo.com,fool.com,nasdaq.com,marketbeat.com,benzinga.com'
    all_articles = []

    for stock_symbol, stock_name in stock_names.items():
        query = f'{stock_name}'
        # Fetch articles using api_key
        articles = newsapi.get_everything(q=query,
                                        language=language,
                                        sort_by=sort_by,
                                        page_size=page_size,
                                        domains=allowed_domains,
                                        from_param=from_date.isoformat(),
                                        to=to_date.isoformat())['articles']

        for article in articles:
            article_text = extract_text_from_url(article['url'])
            timestamp = datetime.datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
            all_articles.append((stock_symbol, article_text, timestamp))
    
    user.calls_remaining -= 1
    all_articles.sort(key=lambda x: x[2])

    with open('news_articles.txt', 'w', encoding='utf-8') as f:
        for stock_symbol, article_text, timestamp in all_articles:
            f.write(f'{stock_symbol} ({timestamp}): {article_text}\n')


    # Read stock data from CSV file
    stock_data = pd.read_csv('filtered_data.csv')

    # Calculate additional features like daily returns
    stock_data['daily_return'] = stock_data.groupby('symbol')['adjusted_close'].pct_change()

    # Preprocess the news article data
    news_data = []

    with open('news_articles.txt', 'r', encoding='utf-8') as f:
        content = f.read()
        f.seek(0)  # Reset file pointer to the beginning of the file

        for line in f:
            match = re.match(r'(\w+)\s\((.+)\): (.+)', line.strip())
            if match:
                symbol, timestamp, text = match.groups()
                news_data.append({'symbol': symbol, 'text': text})
            else:
                print(f"Failed to parse line: {line.strip()}")

    news_data = pd.DataFrame(news_data)

    # Calculate sentiment scores for each news article using VADER
    news_data['sentiment'] = news_data['text'].apply(lambda x: TextBlob(x).sentiment.polarity)

    # Aggregate the sentiment scores for each stock symbol
    news_sentiment = news_data.groupby('symbol')[['sentiment']].mean().reset_index()

    # Merge the stock data and news sentiment data into a single DataFrame
    merged_data = stock_data.merge(news_sentiment, on='symbol')

    # Convert the 'date' column to a datetime object and sort by date
    merged_data['date'] = pd.to_datetime(merged_data['date'])
    merged_data = merged_data.sort_values(['symbol', 'date'])

    # Create a target variable: next week's return
    merged_data['next_week_return'] = merged_data.groupby('symbol')['adjusted_close'].shift(-5) / merged_data['adjusted_close'] - 1

    # Drop the last 5 days for each stock, as we don't have future data for those days
    merged_data = merged_data.groupby('symbol').apply(lambda x: x.iloc[:-5]).reset_index(drop=True)

    # Save the merged data to a CSV file
    #merged_data.to_csv('merged_data.csv', index=False)
    json_data = merged_data.to_json(orient='records')

    userdb.commit()
    userdb.refresh(user)
    userdb.close()
    return json.loads(json_data)

############################################################################################################################################


@app.get('/stock-newsletter', status_code = status.HTTP_200_OK, tags = ['Stock-Newsletter'])
async def stock_newsletter(current_user: schemas.User = Depends(get_current_user), userdb : Session = Depends(user_data.get_db),stock_articles: StockArticles = Depends(get_stock_articles)):
    user = userdb.query(schemas.User_Table).filter(current_user == schemas.User_Table.username).first()
    
    if not user:
        raise HTTPException(status_code = 404, detail = "User not found")
    
    if user.calls_remaining <= 0:
        return ("Your account has reached its call limit. Please upgrade your account to continue using the service.")
    
    user.calls_remaining -= 1
    ## Enter the code for scraping stock data
    
#     ## Enter the code for stock newsletter
    # Create the GPT prompt using the top 5 stocks and news articles
    data = {'symbol': ['TSLA', 'AMZN', 'TSLA', 'JPM', 'JNJ'],
        'predicted_return': [0.079031, 0.069934, 0.056484, 0.056184, 0.055282],
        'index': [20, 9, 59, 69, 7]}
    
    top_5_stocks = pd.DataFrame(data)
    top_5_stocks.set_index('index', inplace=True)
    stock_articles_list = stock_articles.get_articles()
    gpt_prompt = create_gpt_prompt(top_5_stocks, stock_articles_list)
    print(gpt_prompt)

    # Generate the newsletter
    newsletter = generate_newsletter(gpt_prompt)
    print("\nGenerated Newsletter:\n")
    print(newsletter)

    return newsletter




############################################################################################################################################




@app.get('/stock-recommendation', status_code=status.HTTP_200_OK, tags=['Stock-Recommendation'])
async def stock_recommendation(current_user: schemas.User = Depends(get_current_user),
                               userdb: Session = Depends(user_data.get_db)):
    user = userdb.query(schemas.User_Table).filter(current_user == schemas.User_Table.username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.calls_remaining <= 0:
        return "Your account has reached its call limit. Please upgrade your account to continue using the service."

    user.calls_remaining -= 1

    # Load and prepare the dataset (replace with the actual dataset path)
    data = pd.read_csv('/Users/ajinabraham/Documents/BigData7245/BigData/FastAPI/merged_data.csv')

    # Predict next week returns
    predictions = predict_next_week_returns(data)

    # Create a DataFrame with stock symbols and their predicted next week returns
    symbols = data['symbol'].values
    predicted_returns = pd.DataFrame({'symbol': symbols, 'predicted_return': predictions.flatten()})

    # Sort the stocks by predicted return in descending order and select the top 5
    top_5_stocks = predicted_returns.sort_values(by='predicted_return', ascending=False).head(5)

    # Return the top 5 stock recommendations as a JSON response
    return JSONResponse(content=top_5_stocks.to_dict(orient='records'))
