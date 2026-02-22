import json
import os
import base64
from dotenv import load_dotenv
from fastapi import FastAPI, Response
from fastapi.responses import RedirectResponse
from httpx import AsyncClient
from typing import List
from pydantic import BaseModel

load_dotenv()

github_client_id = os.getenv("GITHUB_CLIENT_ID")
github_client_secret = os.getenv("GITHUB_CLIENT_SECRET")
access_token = os.getenv("TEST_ACCESS_TOKEN")

app = FastAPI()

@app.get("/")
async def hello():
    return Response("hello", status_code=200)


@app.get("/github-login")
async def github_login():
    return RedirectResponse(f"https://github.com/login/oauth/authorize?client_id={github_client_id}&scope=repo")


@app.get("/github-code")
async def github_code(code: str):
    params = {
        "client_id": github_client_id,
        "client_secret": github_client_secret,
        "code": code
    }
    headers = {"Accept": "application/json"}

    async with AsyncClient() as client:
        response = await client.post("https://github.com/login/oauth/access_token", params=params, headers=headers)
    response_json = response.json()
    access_token = response_json.get("access_token")
    print(access_token)

    async with AsyncClient() as client:
        headers.update({"Authorization": f"Bearer {access_token}"})
        user = await client.get("https://api.github.com/user",headers=headers)
    return user.json()


@app.get("/get-repos")
async def get_repos():
    dic = {}
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "visibility": "all",

    }
    async with AsyncClient() as client:
        response = await client.get(f"https://api.github.com/user/repos", headers=headers, params=params)
        repos = response.json()

        # paginate
        while "next" in response.links:
            response = await client.get(response.links["next"]["url"], headers=headers)
            repos.extend(response.json())

    for index, item in enumerate(repos):
        dic[item["name"]] = item

    return dic


class RepoRequest(BaseModel):
    owner: str
    repos: List

@app.post("/get-dep-files")
async def get_repo_tree(body: RepoRequest):
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {access_token}"
    }
    returned_repo_list = []
    print(f"bodies: {body}")
    for repo in body.repos:
        async with AsyncClient() as client:
            repo_response = await client.get(f"https://api.github.com/repos/{body.owner}/{repo}", headers=headers)
            default_branch = repo_response.json().get("default_branch", "main")
            response = await client.get(f"https://api.github.com/repos/{body.owner}/{repo}/git/trees/{default_branch}?recursive=1", headers=headers)
        res = response.json()
        tree = res.get("tree")
        
        if not tree:
            continue
        
        for item in tree:
            if item.get("path") == "requirements.txt":
                url = item.get("url")
                async with AsyncClient() as client:
                    response = await client.get(url=url, headers=headers)
                    
                res_json = response.json()
                content = base64.b64decode(res_json.get("content")).decode("utf-8")
                
                returned_repo_object = {
                    "name": repo,
                    "content": content
                }
                returned_repo_list.append(returned_repo_object)

    return returned_repo_list


class VulnerabilityRequest(BaseModel):
    package_list : List
    language : str
    
{
    "package_list": ["Flask==3.1.0", "google_auth_oauthlib==1.2.0", "gspread==6.2.0", "protobuf==6.30.2", "pyshorteners==1.0.1", "python-dotenv==1.1.0", "python-telegram-bot==22.0", "reverse_geocoder==1.5.1", "stripe==10.1.0"],
    "language": "Python"
}

@app.post("/get-vulnerabilities")
async def get_vulnerabilities(body: VulnerabilityRequest):
    ecosytem = "PyPI" if body.language.lower() == "python" else "npm"
    package_queries = []
    for package in body.package_list:
        name, version = package.split("==")
        package_queries.append({
            "version": version,
            "package": {
                "name": name,
                "ecosytem": ecosytem
            }
        })
        
    async with AsyncClient() as client:
        vuln_response = await client.post("https://api.osv.dev/v1/querybatch", json={'queries': package_queries})
        vuln_results_json = vuln_response.json().get('results')
    for package_name, result in zip(body.package_list, vuln_results_json):
        python_relevant_prefixes = ('GHSA-', 'PYSEC-', 'CVE-')
        javascript_relevant_prefixes = ('GHSA-', 'MAL-', 'CVE-')
        vulns = [vuln for vuln in result.get("vulns", []) if any(vuln['id'].startswith(p) for p in python_relevant_prefixes)]
        if vulns:
            print(f"{package_name}: has {len(vulns)}")