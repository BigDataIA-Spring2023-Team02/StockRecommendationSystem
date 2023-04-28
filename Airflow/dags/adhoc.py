import os
import requests
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator


BASE_URL = os.getenv("API_URL", "http://host.docker.internal:8000")
# BASE_URL = "http://host.docker.internal:8000"
# BASE_URL = "http://localhost:8050"
 # Replace with your FastAPI app URL

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 4, 25),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "fastapi_dag",
    default_args=default_args,
    description="Trigger FastAPI endpoints with Airflow",
    schedule_interval=timedelta(days=1),
    catchup=False,
)


def call_fastapi_endpoint(endpoint, token):
    url = f"{BASE_URL}/{endpoint}"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Calling {url} with token: {token}")  # Add this line for debugging

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print(f"Successfully triggered {endpoint}.")
    else:
        print(f"Error triggering {endpoint}: {response.status_code}, {response.text}")


def get_auth_token(username, password):
    url = f"{BASE_URL}/login"
    data = {"username": username, "password": password}
    response = requests.post(url, data=data)

    if response.status_code == 200:
        token = response.json().get("access_token")
        return token
    else:
        print(f"Error getting auth token: {response.status_code}, {response.text}")
        return None



def call_get_auth_token():
    token = get_auth_token("admin", "admin1234")
    if token is None:
        raise Exception("Failed to get auth token.")
    return token



def call_stock_data_scrape(token):
    call_fastapi_endpoint("stock-data-scrape", token)


def call_stock_recommendation(token):
    call_fastapi_endpoint("stock-recommendation", token)


def call_stock_newsletter(token):
    call_fastapi_endpoint("stock-newsletter", token)


get_auth_token_operator = PythonOperator(
    task_id="get_auth_token_task",
    python_callable=call_get_auth_token,
    dag=dag,
)

stock_data_scrape_operator = PythonOperator(
    task_id="stock_data_scrape_task",
    python_callable=call_stock_data_scrape,
    op_args=["{{ task_instance.xcom_pull(task_ids='get_auth_token_task') }}"],
    dag=dag,
)

stock_recommendation_operator = PythonOperator(
    task_id="stock_recommendation_task",
    python_callable=call_stock_recommendation,
    op_args=["{{ task_instance.xcom_pull(task_ids='get_auth_token_task') }}"],
    dag=dag,
)

stock_newsletter_operator = PythonOperator(
    task_id="stock_newsletter_task",
    python_callable=call_stock_newsletter,
    op_args=["{{ task_instance.xcom_pull(task_ids='get_auth_token_task') }}"],
    dag=dag,
)

get_auth_token_operator >> stock_data_scrape_operator >> stock_recommendation_operator >> stock_newsletter_operator
