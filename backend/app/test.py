import os
import requests
from typing import List
from dotenv import load_dotenv

load_dotenv()
base_url = os.getenv('BASE_API_URL')

def get_dependencies(repo_names: List):
    repo_response = requests.post(url=f"{base_url}/get-dep-files", json={"owner": "johnnybasgallop", "repos": repo_names})
    response_json = repo_response.json()
    for repository in response_json:
        unfiltered_dep_content = repository.get('content')
        filtered_dep_content = unfiltered_dep_content.split('\n')
        if filtered_dep_content[-1] == "":
            filtered_dep_content.pop()
        print(filtered_dep_content)
        

    
if __name__ == "__main__":
    repos = ['DMOIDBot', 'JTFX-Discord_Bot', 'TpTradingSubBot']
    get_dependencies(repo_names=repos)