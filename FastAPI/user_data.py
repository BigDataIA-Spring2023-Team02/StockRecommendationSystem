import os
import boto3
import sqlite3
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

user_db_url = 'sqlite:///user_data.db'
engine = create_engine(user_db_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close

async def get_user_data_file():
    user_connection = sqlite3.connect('user_data.db')
    return user_connection
