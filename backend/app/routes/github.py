import base64
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from fastapi.responses import RedirectResponse
from httpx import AsyncClient
from typing import List

from app.models.requests import GithubRepoRequest
from app.models.responses import DependencyFile
from app.config import Settings, get_settings

router = APIRouter()

@router.get("/login")
async def github_login(settings: Settings = Depends(get_settings)):
    return RedirectResponse(f"https://github.com/login/oauth/authorize?client_id={settings.github_client_id}&scope=repo")


@router.get("/callback")
async def github_code(code: str, settings: Settings = Depends(get_settings)):
    params = {
        "client_id": settings.github_client_id,
        "client_secret": settings.github_client_secret,
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


@router.get("/repos")
async def get_repos(settings: Settings = Depends(get_settings)):
    dic = {}
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {settings.test_access_token}"
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



@router.post("/dep-files", response_model=List[DependencyFile])
async def get_repo_tree(body: GithubRepoRequest, settings: Settings = Depends(get_settings)):
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {settings.test_access_token}"
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
            if "requirements.txt" in item.get("path"):
                url = item.get("url")
                async with AsyncClient() as client:
                    response = await client.get(url=url, headers=headers)
                    
                res_json = response.json()
                content = base64.b64decode(res_json.get("content")).decode("utf-8")
                returned_repo_list.append(DependencyFile(name=repo, content=content))

    return returned_repo_list
