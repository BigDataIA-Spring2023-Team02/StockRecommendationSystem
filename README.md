# Stock Recommendation System
> ✅ Active status <br>
> [🚀 Streamlit][http://44.215.201.22:8501] <br>
> [🧑🏻‍💻 FastAPI][http://44.215.201.22:8000/docs] <br>
> [⏱ Airflow][http://44.215.201.22:8080/home] <br>
> [🎬 Codelab Slides][https://codelabs-preview.appspot.com/?file_id=1h3lM1FPgsy0AcRAXEcB00uf5y7V1ZQUb_Cad46vHcuw#0] <br>

----- 

## Team Information
| Name     | NUID        |
| ---      | ---         |
| Meet     | 002776055   |
| Ajin     | 002745287   |
| Siddhi   | 002737346   |
| Akhil    | 002766590   |

## About
This repository contains a collection of Big Data Systems & Intelligence Analytics Assignments & Projects that utilize the power of AWS and SQLite to process and analyze data using Streamlit. The assignments are designed to showcase the capabilities of these technologies in handling and processing large and complex datasets in real-time. The assignments cover various topics such as data ingestion, data processing, data storage, and data analysis, among others. Whether you are a big data enthusiast or a professional looking to build your skills in this field, this repository is a great resource to get started. So, go ahead, fork the repository and start working on these assignments to take your big data skills to the next level!

----- 

## Index
  - [Objective](#objective)
  - [Abstract 📝](#abstract)
  - [Architecture Diagram](#architecture-diagram)
  - [Installation](#installation)
  - [Project Components 💽](#project-components)
  - [Streamlit](#streamlit) 
  - [FastAPI](#fast-api)
  - [Process Flow](#process-flow)


## Objective
To create a custom stock recommendation newsletter dashboard that will provide top recommended stocks to investors and generate a personalized newsletter based on the user's preferences and the top recommended stocks.


## Abstract
This project aims to develop a custom stock recommendation newsletter dashboard that will provide investors with top recommended stocks and create personalized newsletters based on their preferences and investment goals. The dashboard will use advanced algorithms to analyze the stock market data and identify the best stocks based on various factors, such as market trends, company performance, and financial indicators.

Users will be able to set their preferences and receive personalized newsletters with the latest insights and trends in the stock market. The dashboard will also allow users to track their favorite stocks, receive alerts on price changes, and access historical data.

The objective of this project is to provide investors with a user-friendly and intuitive dashboard that will provide them with accurate and reliable information to make informed investment decisions. The custom stock recommendation newsletter dashboard will be a valuable tool for investors looking to stay informed about the latest stock market trends and make smart investment decisions.


## Architecture Diagram
This architecture diagram depicts the flow of the application and the relationships between services. NOTE: Our proposed diagram is same our final implemented framework

<!-- ![Architecure Diagram](---) -->


## Installation
Clone this repository: git clone https://github.com/BigDataIA-Spring2023-Team02/StockRecommendationSystem.git

### Project Tree:
```bash
.
└── StockRecommendationSystem
    ├── Airflow
    │   ├── dags
    │       └── adhoc.py
    │   ├── logs
    │   ├── plugins
    │   ├── working_dir
    │   ├── .env
    │   └── docker-compose.yaml
    ├── FastAPI
    │   ├── .env
    │   ├── Dockerfile
    │   ├── download.py
    │   ├── filtered_data.csv
    │   ├── jwt_api.py
    │   ├── mainapiapp.py
    │   ├── merged_data.csv
    │   ├── model.joblib
    │   ├── model.py
    │   ├── requirements.txt
    │   ├── schemas.py
    │   ├── user_data.db
    │   └── user_data.py
    ├── Streamlit
    │   ├── pages
    │       ├── Forgot_Password.py
    │       ├── Register_Page.py
    │       ├── Stock_Dashboard.py
    │       ├── Stock_Recommendation.py
    │       └── Upgrade_Plan.py
    │   ├── .env
    │   ├── Dockerfile
    │   ├── Login_Page.py
    │   └── requirements.txt
    ├── .env
    ├── .gitattributes
    ├── .gitignore
    ├── docker-compose.yaml
    ├── edit_stock_recommendation_merged_suite.ipynb
    ├── README.md
    ├── requirements.txt
    └── StockPriceEDA.ipynb
```

### Prerequisites
* IDE
* Python 3.x


## Project Components
- FastAPI: REST API endpoints for the application
- Streamlit: Frontend interface for the Stock Recommendation System application
- Airflow: DAG to responsible for scraping data from the sources and storing it in a database for further processing. DAG to generates stock recommendations based on the scraped data, analyzing trends and patterns to provide insights to users. DAG to create a newsletter summary by consolidating information from various sources and generating a concise, engaging summary for users.


## Streamlit
The data exploration tool for the Geospatial startup uses the Python library [Streamlit](https://streamlit.io) for its user interface. 

### Streamlit UI layout:
  - Login Functionality
    - Login page for returning users to enter username and password to get access to the application
  - Register
    - Register page for new users to enter full name, email, username, password, confirm password, user type and plans to access the application
  - Forgot Password
    - Forgot Password page for users to change their password using their username to get access
  - Logout
    - Logout users to end session and return to Login page

### Create a docker image for this Streamlit app:
```
docker build -t stock_streamlit_v2:latest .
docker tag stock_streamlit_v2:latest doshimee11/stock_streamlit_v2:latest
docker push doshimee11/stock_streamlit_v2:latest
```


## Fast API
To truly ensure decoupling, API calls are made in the backend to the Streamlit app in order to achieve the following:

- Create and Get users : Users are created with their full name, username, email, password(stored as a hash), user type and Plan
- Plan: The users are offered 2 plans: Free and Premium with varying levels of API request limits.
- Create and verify Login and Access Tokens
- Change user account password and update hashed password in the database

The users in the database are granted an access token for a limited time, also known as a session. This access token acts as an authentication to facilitate authorization.

create jwt_api.py file, here we make use of a secret key, an algorithm of our choice(HS256) and an expiration time(30 mins)
This file contains 5 functions:
  - Function to hash password of a user
  - Function to verify hashed password of a user
  - Function to generate an access token
  - Function to verify the access token
  - Function to get the current user

### Create a docker image for this FastAPI app:
```
docker build -t stock_api_v1:latest .
docker tag stock_api_v1:latest doshimee11/stock_api_v1:latest
docker push doshimee11/stock_api_v1:latest
```


## Process Flow
* Download app files

* Create a python virtual environment and activate
```bash
python -m venv stock_venv
```

* Activate the virtual environment
```bash
source stealdeal_venv/bin/activate  # on Linux/macOS
env\Scripts\activate     # on Windows
```

* Upgrade pip to install required packages
```bash
python -m pip install pip --upgrade
```

* Install the required packages from requirements.txt file
```bash
pip install -r requirements.txt
```

* Set your environment variable
```bash
AWS_ACCESS_KEY=XXXXX
AWS_SECRET_KEY=XXXXX
USER_BUCKET_NAME=XXXXX
AWS_LOGS_ACCESS_KEY=XXXXX
AWS_LOGS_SECRET_KEY=XXXXX
```

* To run on docker:
> Execute the [___][def] to have the FastAPI and Streamlit images running simultaneously by executing the following command: 
```bash
docker compose up
```

> Execute the [___][def] to have the Airflow images running by executing the following command: 
```bash
cd Airflow/
docker compose up
```

* To run locally:
> Run Streamlit app
```bash
cd Streamlit/
streamlit run Login_Page.py
```

> Run FastAPI
```bash
cd FastAPI/
uvicorn mainapiapp:app --reload --port 8000
```

This runs the application with a frontend streamlit interface on [___][def]
-----
> WE ATTEST THAT WE HAVEN’T USED ANY OTHER STUDENTS’ WORK IN OUR ASSIGNMENT AND ABIDE BY THE POLICIES LISTED IN THE STUDENT HANDBOOK.
> Meet: 25%, Ajin: 25%, Siddhi: 25%, Akhil: 25%
-----
