import os
import re
import time
import json
import boto3
import openai
import joblib
import textwrap
import requests
import datetime
import numpy as np
import pandas as pd
from time import sleep
from io import StringIO
import user_data, schemas
from fastapi import FastAPI
from pandas import DataFrame
from bs4 import BeautifulSoup
from textblob import TextBlob
from typing import List, Tuple
from dotenv import load_dotenv
from newsapi import NewsApiClient
from sqlalchemy.orm import Session
from http.client import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import FastAPI, Depends, status, HTTPException
from jwt_api import bcrypt, verify, create_access_token, get_current_user
from typing import List, Dict, Union
from fastapi import BackgroundTasks
import user_data
from typing import Optional




load_dotenv()
alpha_vantage_key_id = os.environ.get('ALPHA_VANTAGE_API_KEY')
news_api_key_id = os.environ.get('NEWS_API_KEY')
openai.api_key = os.environ.get('OPENAI_API_KEY')

s3Client = boto3.client('s3',
                        region_name='us-east-1',
                        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'),
                        aws_secret_access_key=os.environ.get('AWS_SECRET_KEY')
                        )

clientLogs = boto3.client('logs',
                          region_name='us-east-1',
                          aws_access_key_id=os.environ.get('AWS_LOGS_ACCESS_KEY'),
                          aws_secret_access_key=os.environ.get('AWS_LOGS_SECRET_KEY')
                          )

sns_client = boto3.client('sns', region_name='us-east-1',
                          aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'),
                          aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'))

app = FastAPI(debug=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_all_email_addresses(userdb: Session) -> List[str]:
    users = userdb.query(schemas.User_Table).all()
    email_addresses = [user.email for user in users]
    return email_addresses

def subscribe_email_to_topic(topic_arn: str, email: str):
    response = sns_client.subscribe(
        TopicArn=topic_arn,
        Protocol="email",
        Endpoint=email
    )
    return response

def subscribe_all_users_to_sns_topic(userdb: Session):
    topic_arn = "arn:aws:sns:us-east-1:427585180930:bigdatasns"
    email_addresses = get_all_email_addresses(userdb)
    
    for email in email_addresses:
        subscribe_email_to_topic(topic_arn, email)
        print(f"Subscribed {email} to the SNS topic {topic_arn}")

def send_email_notification(subject: str, message: str, email: str):
    response = sns_client.publish(
        TopicArn="arn:aws:sns:us-east-1:427585180930:bigdatasns",
        Message=message,
        Subject=subject
    )
    return response

def trigger_airflow_task(dag_id: str, task_id: str, base_url: str, api_key: Optional[str] = None):
    url = f"{base_url}/api/v1/dags/{dag_id}/tasks/{task_id}/trigger"

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        print("Task triggered successfully")
    else:
        print(f"Error triggering task: {response.status_code}, {response.text}")




# # download the file object from S3 bucket
with open('model.joblib', 'wb') as f:
    s3Client.download_fileobj(os.environ.get('USER_BUCKET_NAME'), 'model.joblib', f)

model = joblib.load('model.joblib')

# model = joblib.load('/Users/ajinabraham/Documents/BigData7245/StockRecommendationSystem/FastAPI/model.joblib')

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
async def stock_data_pull(background_tasks: BackgroundTasks, current_user: schemas.User = Depends(get_current_user), userdb : Session = Depends(user_data.get_db)):
    background_tasks.add_task(trigger_airflow_task, "fastapi_endpoints", "stock_data_pull")
    user = userdb.query(schemas.User_Table).filter(current_user == schemas.User_Table.username).first()
    if not user:
        raise HTTPException(status_code = 404, detail = "User not found")
    
    if user.calls_remaining <= 0:
        return ("Your account has reached its call limit. Please upgrade your account to continue using the service.")
    ## Enter the code for scraping stock data

    # List of top 10 stock symbols (replace with actual symbols)
    print("stock-data-scrape endpoint called")
    top_10_stocks = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'FB', 'TSLA', 'JPM', 'V', 'JNJ', 'MA']

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
            stock_data = pd.concat([stock_data, df], ignore_index=True)
            # stock_data = stock_data.append(df, ignore_index=True)

        sleep(60 / 5)

    stock_data.columns = ['date', 'open', 'high', 'low', 'close', 'adjusted_close', 'volume', 'dividend_amount', 'split_coefficient', 'symbol']
    stock_data['date'] = pd.to_datetime(stock_data['date'])
    last_30_days = pd.to_datetime('today') - pd.Timedelta(days=30)
    filtered_data = stock_data[stock_data['date'] >= last_30_days]
    s3Client.put_object(Body=filtered_data.to_csv(index=False), Bucket=os.environ.get('USER_BUCKET_NAME'), Key=f'MergedData/{current_user}_filtered_data.csv')

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
    
    all_articles.sort(key=lambda x: x[2])

    # Create a string variable to store the content of all articles
    article_text = ''
    for stock_symbol, article_text_single, timestamp in all_articles:
        article_text += f'{stock_symbol} ({timestamp}): {article_text_single}\n'

    with open('news_articles.txt', 'w', encoding='utf-8') as f:
        f.write(article_text)

    with open('news_articles.txt', 'rb') as f:
        s3Client.put_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key=f'MergedData/{current_user}_news_articles.txt', Body=f)
    
    stock_data = s3Client.get_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key=f'MergedData/{current_user}_filtered_data.csv')['Body'].read().decode('utf-8')
    stock_data = pd.read_csv(StringIO(stock_data))

    # Calculate additional features like daily returns
    stock_data['daily_return'] = stock_data.groupby('symbol')['adjusted_close'].pct_change()

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
                write_logs(f"Failed to parse line: {line.strip()}")
    os.remove('news_articles.txt')

    news_data = pd.DataFrame(news_data)
    news_data['sentiment'] = news_data['text'].apply(lambda x: TextBlob(x).sentiment.polarity)
    news_sentiment = news_data.groupby('symbol')[['sentiment']].mean().reset_index()
    merged_data = stock_data.merge(news_sentiment, on='symbol')
    merged_data['date'] = pd.to_datetime(merged_data['date'])
    merged_data = merged_data.sort_values(['symbol', 'date'])
    merged_data['next_week_return'] = merged_data.groupby('symbol')['adjusted_close'].shift(-5) / merged_data['adjusted_close'] - 1
    merged_data = merged_data.groupby('symbol').apply(lambda x: x.iloc[:-5]).reset_index(drop=True)

    # Save the merged data to a CSV file
    s3Client.put_object(Body=merged_data.to_csv(index=False), Bucket=os.environ.get('USER_BUCKET_NAME'), Key=f'MergedData/{current_user}_merged_data.csv')
    json_data = merged_data.to_json(orient='records')
    
    user.calls_remaining -= 1
    userdb.commit()
    userdb.refresh(user)
    userdb.close()
    return json.loads(json_data)


@app.get('/stock-recommendation', status_code=status.HTTP_200_OK, tags=['Stock-Recommendation'])
async def stock_recommendation(background_tasks: BackgroundTasks, current_user: schemas.User = Depends(get_current_user), userdb: Session = Depends(user_data.get_db)):
    background_tasks.add_task(trigger_airflow_task, "fastapi_endpoints", "stock_recommendation")
    user = userdb.query(schemas.User_Table).filter(current_user == schemas.User_Table.username).first()
    if not user:
        raise HTTPException(status_code = 404, detail = "User not found")
    
    if user.calls_remaining <= 0:
        return ("Your account has reached its call limit. Please upgrade your account to continue using the service.")
    
    
    # merged_data = pd.read_csv('merged_data.csv')
    merged_data = s3Client.get_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key=f'MergedData/{current_user}_merged_data.csv')['Body'].read().decode('utf-8')
    # Convert the date column to Unix timestamps
    merged_data = pd.read_csv(StringIO(merged_data))
    merged_data['date'] = pd.to_datetime(merged_data['date']).astype(int) // 10**9
    recent_data = merged_data.loc[merged_data.groupby('symbol')['date'].idxmax()]
    X = recent_data.drop(['symbol', 'next_week_return'], axis=1)
    recent_data['predicted_next_week_return'] = model.predict(X)
    sorted_stocks = recent_data.sort_values('predicted_next_week_return', ascending=False)
    top5_stocks_dict = sorted_stocks.head(5)[['symbol', 'predicted_next_week_return']].to_dict(orient='records')
    
    user.calls_remaining -= 1
    userdb.commit()
    userdb.refresh(user)
    userdb.close()
    return top5_stocks_dict


# @app.get('/stock-newsletter', status_code=status.HTTP_200_OK, tags=['Stock-Newsletter'])
# async def stock_newsletter(background_tasks: BackgroundTasks, top5_stocks_dict: List[Dict[str, Union[str, float]]] = Depends(stock_recommendation), current_user: schemas.User = Depends(get_current_user), userdb: Session = Depends(user_data.get_db), stock_articles: StockArticles = Depends(get_stock_articles)):
#     background_tasks.add_task(trigger_airflow_task, "fastapi_endpoints", "stock_newsletter")
#     user = userdb.query(schemas.User_Table).filter(current_user == schemas.User_Table.username).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     if user.calls_remaining <= 0:
#         return ("Your account has reached its call limit. Please upgrade your account to continue using the service.")

#     top_5_stocks = pd.DataFrame(top5_stocks_dict).rename(columns={'predicted_next_week_return': 'predicted_return'})

#     # Reset the index of the DataFrame
#     top_5_stocks.reset_index(drop=True, inplace=True)

#     # Create the GPT prompt using the top 5 stocks and news articles
#     stock_articles_list = stock_articles.get_articles()
#     gpt_prompt = create_gpt_prompt(top_5_stocks, stock_articles_list)

#     # Generate the newsletter
#     newsletter = generate_newsletter(gpt_prompt)
#     with open('newsletter.txt', 'w', encoding='utf-8') as f:
#         f.write(newsletter)

#     # Store the file to AWS S3 bucket
#     with open('newsletter.txt', 'rb') as f:
#         s3Client.put_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key=f'MergedData/{current_user}_newsletter.txt', Body=f)
#     os.remove('newsletter.txt')

#     user.calls_remaining -= 1
#     userdb.commit()
#     userdb.refresh(user)
#     userdb.close()
#     return newsletter

@app.get('/stock-newsletter', status_code=status.HTTP_200_OK, tags=['Stock-Newsletter'])
async def stock_newsletter(
    background_tasks: BackgroundTasks, 
    top5_stocks_dict: List[Dict[str, Union[str, float]]] = Depends(stock_recommendation), 
    current_user: schemas.User = Depends(get_current_user), 
    userdb: Session = Depends(user_data.get_db), 
    stock_articles: StockArticles = Depends(get_stock_articles)
):
    background_tasks.add_task(trigger_airflow_task, "fastapi_endpoints", "stock_newsletter")
    user = userdb.query(schemas.User_Table).filter(current_user == schemas.User_Table.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.calls_remaining <= 0:
        return ("Your account has reached its call limit. Please upgrade your account to continue using the service.")

    top_5_stocks = pd.DataFrame(top5_stocks_dict).rename(columns={'predicted_next_week_return': 'predicted_return'})

    # Fetch the email address of the user from the SQLite database
    subscriber_email = user.email

    # Prepare the subject and message for the email
    subject = "Stock Newsletter"
    message = "Here are the top 5 stocks for this week:\n\n"
    message += top_5_stocks.to_string(index=False)

    # Send the email using AWS SNS
    send_email_notification(subject, message, subscriber_email)

    return {"detail": "Stock newsletter sent to the subscriber's email."}

# # Call the function when your application starts
# # ...
# # Call the function when your application starts
# db = user_data.get_db()
# subscribe_all_users_to_sns_topic(db)
