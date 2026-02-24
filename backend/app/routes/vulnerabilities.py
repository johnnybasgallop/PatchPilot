import base64
import asyncio
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from fastapi.responses import RedirectResponse
from httpx import AsyncClient
from typing import List
from app.models.requests import VulnerabilityRequest
from app.models.responses import PackageVulnerabilityReport, VulnerabilityDetail
from app.utils.parsers import get_fixed_version
from app.config import Settings, get_settings

router = APIRouter()

# {
#     "package_list": ["Flask==3.1.0", "google_auth_oauthlib==1.2.0", "gspread==6.2.0", "protobuf==6.30.2", "pyshorteners==1.0.1", "python-dotenv==1.1.0", "python-telegram-bot==22.0", "reverse_geocoder==1.5.1", "stripe==10.1.0"],
#     "language": "Python"
# }

@router.post("/scan", response_model=List[PackageVulnerabilityReport])
async def get_vulnerabilities(body: VulnerabilityRequest):
    ecosystem = "PyPI" if body.language.lower() == "python" else "npm"
    prefixes = ('GHSA-', 'PYSEC-', 'CVE-') if body.language.lower() == "python" else ('GHSA-', 'MAL-', 'CVE-')

    package_queries = []
    for package in body.package_list:
        name, version = package.split("==")
        package_queries.append({
            "version": version,
            "package": {"name": name, "ecosystem": ecosystem},
        })

    async with AsyncClient() as client:
        batch_response = await client.post("https://api.osv.dev/v1/querybatch", json={"queries": package_queries})
        batch_results = batch_response.json().get("results", [])

        reports = []
        for package_name, result in zip(body.package_list, batch_results):
            relevant_vulns = [
                vuln for vuln in result.get("vulns", [])
                if any(vuln["id"].startswith(prefix) for prefix in prefixes)
            ]

            if not relevant_vulns:
                reports.append(PackageVulnerabilityReport(package=package_name))
                continue

            tasks = [client.get(f"https://api.osv.dev/v1/vulns/{vuln['id']}") for vuln in relevant_vulns]
            responses = await asyncio.gather(*tasks)

            vuln_details = []
            for r in responses:
                response_json = r.json()
                vuln_details.append(VulnerabilityDetail(
                    id=response_json.get("id"),
                    aliases=response_json.get("aliases", []),
                    summary=response_json.get("summary"),
                    details=response_json.get("details"),
                    severity=response_json.get("database_specific", {}).get("severity"),
                    fixed_version=get_fixed_version(response_json),
                    references=[ref.get("url") for ref in response_json.get("references", [])],
                ))

            reports.append(PackageVulnerabilityReport(
                package=package_name,
                vulnerabilities=vuln_details,
            ))

    return reports