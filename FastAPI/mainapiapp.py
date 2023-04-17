import pandas as pd
import user_data, schemas
from pytest import Session
from fastapi import FastAPI
from sqlite3 import Connection
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from http.client import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends, status,HTTPException
from jwt_api import bcrypt, verify, verify_token, create_access_token, get_current_user

load_dotenv()

app = FastAPI()
user_data.Base.metadata.create_all(bind = user_data.engine)
get_db = user_data.get_db

@app.post('/login')
def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(user_data.get_db)):
    user = db.query(user_data.User_Table).filter(user_data.User_Table.username == request.username).first()
    if not user:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail="Invalid Credentials") 
    if not verify(user.password, request.password):
                raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail="Incorrect Password")
    access_token = create_access_token(data={"sub": user.full_name})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post('/user/create', response_model= schemas.ShowUser)
def create_user(request: schemas.User, db: Session = Depends(get_db)):
    user = db.query(schemas.User_Table).filter(schemas.User_Table.username == request.username).first()
    if not user:
        new_user = schemas.User_Table(full_name = request.full_name, email = request.email, username = request.username, password = bcrypt(request.password))
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User already exists')

@app.patch('/user/update',response_model= schemas.ShowUser)
def update_password(username : str, new_password: schemas.UpdatePassword, db: Session = Depends(get_db)):
    user = db.query(schemas.User_Table).filter(username == schemas.User_Table.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    updated_user = dict(username = username, password = bcrypt(new_password.password))
    for key, value in updated_user.items():
        setattr(user, key, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.get('/user/user-details', status_code=status.HTTP_200_OK)
async def user_details(username : str, current_user: schemas.User = Depends(get_current_user), userdb : Connection = Depends(user_data.get_user_data_file)):
    query = "SELECT user_type FROM all_users WHERE username==\'" + username +"\'"
    user_data = pd.read_sql_query(query, userdb)
    print(user_data)
    if user_data['user_type'].to_list() == ['Admin']:
        return user_data['user_type'].to_list()
    else:
        query2 = "SELECT plan FROM all_users WHERE username==\'" + username +"\'"
        user_data_2 = pd.read_sql_query(query2, userdb)
        plan = user_data_2['plan'].tolist()
        return plan

@app.post('/user/upgradeplan', status_code=status.HTTP_200_OK)
async def upgrade_plan(username : str, current_user: schemas.User = Depends(get_current_user), userdb : Connection = Depends(user_data.get_user_data_file)):
    query = "SELECT plan FROM all_users WHERE username=\'" + username +"\'"
    user_data = pd.read_sql_query(query, userdb)
    
    if user_data['plan'].iloc[0] == 'Free':
        user_data['plan'].iloc[0] = 'Premium'
    
    cursor = userdb.cursor()
    update_query = "UPDATE all_users SET plan = ? WHERE username = ?"
    new_plan = user_data['plan'].iloc[0]
    username = username
    cursor.execute(update_query, (new_plan, username))
    userdb.commit()
    cursor.close()
    return True
