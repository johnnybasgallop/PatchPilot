def get_fixed_version(vuln_json: dict) -> str | None:
    for affected in vuln_json.get("affected", []):
        for range_info in affected.get("ranges", []):
            for event in range_info.get("events", []):
                if "fixed" in event:
                    return event["fixed"]
    return None