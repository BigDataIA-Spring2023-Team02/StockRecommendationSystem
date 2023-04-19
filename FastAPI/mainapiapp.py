import os
import time
import boto3
import pandas as pd
import user_data, schemas
from pytest import Session
from fastapi import FastAPI
from sqlite3 import Connection
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from http.client import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi import Depends, status,HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from jwt_api import bcrypt, verify, create_access_token, get_current_user

load_dotenv()

app = FastAPI()
user_data.Base.metadata.create_all(bind = user_data.engine)

# Authenticate S3 client for logging with your user credentials that are stored in your .env config file
clientLogs = boto3.client('logs',
                        region_name='us-east-1',
                        aws_access_key_id = os.environ.get('AWS_LOGS_ACCESS_KEY'),
                        aws_secret_access_key = os.environ.get('AWS_LOGS_SECRET_KEY')
                        )

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

@app.post('/login', status_code = status.HTTP_200_OK, tags = ['User'])
def login(request: OAuth2PasswordRequestForm = Depends(), userdb : Session = Depends(user_data.get_db)):
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
def create_user(request: schemas.User, userdb : Session = Depends(user_data.get_db)):
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
    activity = schemas.User_Activity_Table(
        username = current_user,
        plan = current_user.plan,
        user_type = current_user.user_type,
        request_type = "POST",
        api_endpoint = "user/upgradeplan",
        response_code = "200",
        detail = "",
    )
    
    user = userdb.query(schemas.User_Table).filter(current_user == schemas.User_Table.username).first()
    if not user:
        activity.response_code = "404"
        activity.detail = "User not found."
        userdb.add(activity)
        userdb.commit()
        raise HTTPException(status_code = 404, detail = "User not found")
    
    user.plan = plan
    write_logs(f"Upgraded to {plan} plan for user {user}")
    user.calls_remaining = calls_remaining
    write_logs(f"Remaining {calls_remaining} API calls for user {user}")
    
    activity.plan = plan
    activity.detail = "User plan upgraded."
    userdb.commit()
    userdb.refresh(user)
    userdb.add(activity)
    userdb.commit()
    userdb.close()
    return True

@app.post('/user/activity', status_code = status.HTTP_200_OK, tags = ['User'])
async def user_activity(current_user: schemas.User = Depends(get_current_user), userdb : Session = Depends(user_data.get_db)):
    activity = schemas.User_Activity_Table(
        username = current_user,
        plan = current_user.plan,
        user_type = current_user.user_type,
        request_type = "POST",
        api_endpoint = "user/activity",
        response_code = "200",
        detail = "",
    )
    
    user = userdb.query(schemas.User_Table).filter(current_user == schemas.User_Table.username).first()
    if not user:
        activity.response_code = "404"
        activity.detail = "User not found."
        userdb.add(activity)
        userdb.commit()
        raise HTTPException(status_code = 404, detail = "User not found")
    
    if user == "damg7245":
        query = userdb.query(schemas.User_Activity_Table).all()
    else:
        query = userdb.query(schemas.User_Activity_Table).filter(schemas.User_Activity_Table.username == current_user).all()
    
    activity.detail = "User activity data."
    data = jsonable_encoder(query)
    write_logs(f"Returned data for the current user {user}")
    userdb.add(activity)
    userdb.commit()
    userdb.close()
    return data

@app.get('/stock-data-scrape', status_code = status.HTTP_200_OK, tags = ['Stock-Data'])
async def stock_data_pull(current_user: schemas.User = Depends(get_current_user), userdb : Session = Depends(user_data.get_db)):
    activity = schemas.User_Activity_Table(
        username = current_user,
        plan = current_user.plan,
        user_type = current_user.user_type,
        request_type = "GET",
        api_endpoint = "stock-data-scrape",
        response_code = "200",
        detail = "",
    )
    
    user = userdb.query(schemas.User_Table).filter(current_user == schemas.User_Table.username).first()
    if not user:
        activity.response_code = "404"
        activity.detail = "User not found."
        userdb.add(activity)
        userdb.commit()
        raise HTTPException(status_code = 404, detail = "User not found")
    
    if user.calls_remaining <= 0:
        activity.response_code = "403"
        activity.detail = "Calls remaining exceeded limit"
        userdb.add(activity)
        userdb.commit()
        return ("Your account has reached its call limit. Please upgrade your account to continue using the service.")
    
    user.calls_remaining -= 1
    userdb.commit()

    activity.detail = f""
    userdb.add(activity)
    userdb.commit()
    userdb.close()
    
    ## Enter the code for scraping stock data
    
@app.get('/stock-recommendation', status_code = status.HTTP_200_OK, tags = ['Stock-Recommendation'])
async def stock_recommendation(current_user: schemas.User = Depends(get_current_user), userdb : Session = Depends(user_data.get_db)):
    activity = schemas.User_Activity_Table(
        username = current_user,
        plan = current_user.plan,
        user_type = current_user.user_type,
        request_type = "GET",
        api_endpoint = "stock-recommendation",
        response_code = "200",
        detail = "",
    )
    
    user = userdb.query(schemas.User_Table).filter(current_user == schemas.User_Table.username).first()
    if not user:
        activity.response_code = "404"
        activity.detail = "User not found."
        userdb.add(activity)
        userdb.commit()
        raise HTTPException(status_code = 404, detail = "User not found")
    
    if user.calls_remaining <= 0:
        activity.response_code = "403"
        activity.detail = "Calls remaining exceeded limit"
        userdb.add(activity)
        userdb.commit()
        return ("Your account has reached its call limit. Please upgrade your account to continue using the service.")

    user.calls_remaining -= 1
    userdb.commit()

    activity.detail = f""
    userdb.add(activity)
    userdb.commit()
    userdb.close()
    
    ## Enter the code for recommendation engine
    
@app.get('/stock-newsletter', status_code = status.HTTP_200_OK, tags = ['Stock-Newsletter'])
async def stock_newsletter(current_user: schemas.User = Depends(get_current_user), userdb : Session = Depends(user_data.get_db)):
    activity = schemas.User_Activity_Table(
        username = current_user,
        plan = current_user.plan,
        user_type = current_user.user_type,
        request_type = "GET",
        api_endpoint = "stock-newsletter",
        response_code = "200",
        detail = "",
    )
    
    user = userdb.query(schemas.User_Table).filter(current_user == schemas.User_Table.username).first()
    if not user:
        activity.response_code = "404"
        activity.detail = "User not found."
        userdb.add(activity)
        userdb.commit()
        raise HTTPException(status_code = 404, detail = "User not found")
    
    if user.calls_remaining <= 0:
        activity.response_code = "403"
        activity.detail = "Calls remaining exceeded limit"
        userdb.add(activity)
        userdb.commit()
        return ("Your account has reached its call limit. Please upgrade your account to continue using the service.")

    user.calls_remaining -= 1
    userdb.commit()

    activity.detail = f""
    userdb.add(activity)
    userdb.commit()
    userdb.close()
    
    ## Enter the code for stock newsletter

@app.get('/stock-dashboard', status_code = status.HTTP_200_OK, tags = ['Stock-Dashboard'])
async def stock_dashboard(current_user: schemas.User = Depends(get_current_user), userdb : Session = Depends(user_data.get_db)):
    activity = schemas.User_Activity_Table(
        username = current_user,
        plan = current_user.plan,
        user_type = current_user.user_type,
        request_type = "GET",
        api_endpoint = "stock-dashboard",
        response_code = "200",
        detail = "",
    )
    
    user = userdb.query(schemas.User_Table).filter(current_user == schemas.User_Table.username).first()
    if not user:
        activity.response_code = "404"
        activity.detail = "User not found."
        userdb.add(activity)
        userdb.commit()
        raise HTTPException(status_code = 404, detail = "User not found")
    
    if user.calls_remaining <= 0:
        activity.response_code = "403"
        activity.detail = "Calls remaining exceeded limit"
        userdb.add(activity)
        userdb.commit()
        return ("Your account has reached its call limit. Please upgrade your account to continue using the service.")

    user.calls_remaining -= 1
    userdb.commit()

    activity.detail = f""
    userdb.add(activity)
    userdb.commit()
    userdb.close()
    
    ## Enter the code for stock dashboard
