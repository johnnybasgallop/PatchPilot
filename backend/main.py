import json
import os
import base64
from dotenv import load_dotenv
from fastapi import FastAPI, Response
from fastapi.responses import RedirectResponse
from httpx import AsyncClient

load_dotenv()

github_client_id = os.getenv('GITHUB_CLIENT_ID')
github_client_secret = os.getenv('GITHUB_CLIENT_SECRET')
access_token = os.getenv('TEST_ACCESS_TOKEN')

app = FastAPI()

@app.get('/')
async def hello():
    return Response('hello', status_code=200)


@app.get('/github-login')
async def github_login():
    return RedirectResponse(f'https://github.com/login/oauth/authorize?client_id={github_client_id}&scope=repo')


@app.get('/github-code')
async def github_code(code: str):
    params = {
        'client_id': github_client_id,
        'client_secret': github_client_secret,
        'code': code
    }
    headers = {'Accept': 'application/json'}

    async with AsyncClient() as client:
        response = await client.post('https://github.com/login/oauth/access_token', params=params, headers=headers)
    response_json = response.json()
    access_token = response_json.get('access_token')
    print(access_token)

    async with AsyncClient() as client:
        headers.update({'Authorization': f'Bearer {access_token}'})
        user = await client.get('https://api.github.com/user',headers=headers)
    return user.json()


@app.get('/get-repos')
async def get_repos():
    dic = {}
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        'visibility': 'all',

    }
    async with AsyncClient() as client:
        response = await client.get(f'https://api.github.com/user/repos', headers=headers, params=params)
        repos = response.json()

        # paginate
        while 'next' in response.links:
            response = await client.get(response.links['next']['url'], headers=headers)
            repos.extend(response.json())

    for index, item in enumerate(repos):
        dic[item['name']] = item

    return dic


@app.get('/repo-tree')
async def get_repo_tree(owner:str, repo:str, branch_name:str="main"):
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {access_token}'
    }
    
    async with AsyncClient() as client:
        print(owner, repo)
        response = await client.get(f'https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1', headers=headers)
    res = response.json()
    tree = res.get("tree")
    
    for item in tree:
        if item.get("path") == "requirements.txt":
            url = item.get("url")
            async with AsyncClient() as client:
                response = await client.get(url=url, headers=headers)
            res = response.json()
            content = base64.b64decode(res.get('content')).decode('utf-8')
            return content


# @app.ge