from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def my_task():
    print('Dag run successfully')

with DAG(
    dag_id='test',
    start_date=datetime(year=2026, day=19, month=2),
    schedule="*/5 * * * *",
    catchup=False
) as dag:
    task = PythonOperator(
        task_id="print_success",
        python_callable=my_task
    )