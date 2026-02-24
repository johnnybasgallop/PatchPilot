from pydantic import BaseModel
from typing import List
from enum import Enum

class Language(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"

class GithubRepoRequest(BaseModel):
    owner: str
    repos: List[str]
    
class VulnerabilityRequest(BaseModel):
    package_list : List[str]
    language : Language
    
