from datetime import timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
import requests

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


dag = DAG(
    'fastapi_endpoints',
    default_args=default_args,
    description='DAG for FastAPI endpoints',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 4, 24),
    catchup=False,
)


class MyCustomOperator(BaseOperator):

    @apply_defaults
    def __init__(self, endpoint, *args, **kwargs):
        super(MyCustomOperator, self).__init__(*args, **kwargs)
        self.endpoint = endpoint

    def execute(self, context):
        url = f"http://localhost:8000/{self.endpoint}"
        response = requests.get(url)
        # Do something with the response, e.g., parse data and store in a database



def stock_data_pull_task(**kwargs):
    print("stock_data_pull_task executed")
    url = "http://localhost:8000/stock-data-scrape"
    response = requests.get(url)
    stock_data = response.json()
    print(stock_data)


def stock_newsletter_task(**kwargs):
    url = "http://localhost:8000/stock-newsletter"
    response = requests.get(url)
    newsletter = response.text
    print(newsletter)


def stock_recommendation_task(**kwargs):
    url = "http://localhost:8000/stock-recommendation"
    response = requests.get(url)
    recommendation = response.json()
    print(recommendation)


stock_data_pull_operator = MyCustomOperator(
    task_id='stock_data_pull',
    endpoint='stock-data-scrape',
    dag=dag,
)

stock_newsletter_operator = MyCustomOperator(
    task_id='stock_newsletter',
    endpoint='stock-newsletter',
    dag=dag,
)

stock_recommendation_operator = MyCustomOperator(
    task_id='stock_recommendation',
    endpoint='stock-recommendation',
    dag=dag,
)

stock_recommendation_operator >>  stock_newsletter_operator
