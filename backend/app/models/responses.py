from pydantic import BaseModel
from typing import List, Optional

class GithubUser(BaseModel):
    login: str
    id: int
    avatar_url: Optional[str] = None

class RepoSummary(BaseModel):
    name: str
    full_name: str
    private: bool
    default_branch: str

class DependencyFile(BaseModel):
    name: str
    content: str

class VulnerabilityDetail(BaseModel):
    id: str
    aliases: List[str] = []
    summary: Optional[str] = None
    details: Optional[str] = None
    severity: Optional[str] = None
    fixed_version: Optional[str] = None
    references: List[str] = []

class PackageVulnerabilityReport(BaseModel):
    package: str
    vulnerabilities: List[VulnerabilityDetail] = []