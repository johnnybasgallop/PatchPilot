from fastapi import FastAPI
from app.routes import github, vulnerabilities

app = FastAPI(title="PatchPilot")

app.include_router(github.router, prefix="/github", tags=["GitHub"])
app.include_router(vulnerabilities.router, prefix="/vulnerabilities", tags=["Vulnerabilities"])