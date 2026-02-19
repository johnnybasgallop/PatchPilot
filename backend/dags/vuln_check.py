from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from typing import List
import requests

repos = ['DMOIDBot', 'JTFX-Discord_Bot', 'TpTradingSubBot']
def get_deps(repo_names: List):
    response = requests.post(url="http://api:8000/get-dep-files", json={"owner": "johnnybasgallop", "repos": repos})
    print(response.json())
    
with DAG(
    dag_id='vuln_check',
    start_date=datetime(day=19, month=2, year=2026),
    schedule="*/5 * * * *",
    catchup=False
) as dag:
    task=PythonOperator(
        task_id="vuln_check",
        python_callable=get_deps,
        op_kwargs={"repo_names": repos}
    )