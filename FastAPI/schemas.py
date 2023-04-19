import datetime
from enum import Enum 
from user_data import Base
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime

class User_Table(Base):
    __tablename__ = "Users"
    
    id = Column(Integer, primary_key= True, index=True)
    full_name = Column(String)
    username = Column(String)
    email = Column(String)
    password = Column(String)
    plan = Column(String)
    user_type = Column(String)
    calls_remaining = Column(Integer)

class User_Activity_Table(Base):
    __tablename__ = "Users_Activity"
    
    id = Column(Integer, primary_key= True, index=True)
    username = Column(String)
    plan = Column(String)
    user_type = Column(String)
    request_type = Column(String)
    api_endpoint = Column(String)
    response_code = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    calls_remaining = Column(Integer)

class User(BaseModel):
    full_name: str
    username : str
    email: str
    password: str
    plan : str
    user_type: str
    calls_remaining: int

class ShowUser(BaseModel):
    username: str
    class Config():
        orm_mode = True

class UpdatePassword(BaseModel):
    password : str    
    class Config():
        orm_mode = True

class Login(BaseModel):
    username: str
    password : str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class Plan(str, Enum):
    free = 'Free'
    premium = 'Premium'
