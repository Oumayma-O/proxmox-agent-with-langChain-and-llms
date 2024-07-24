from typing import Dict, Any, Optional
import os

def _validate_headers(
        headers: Optional[Dict[str, Any]] = None,
        pve_token: Optional[str] = None,
) -> Dict[str, Any]:
    _pve_token = pve_token or os.getenv("PVE_TOKEN")
    auth: Dict[str, str] = {'Authorization': _pve_token}
    if headers:
        if 'Authorization' in headers:
            return headers
        return {**auth, **headers}
    return auth

def _validate_URL(
        base_url: str,
) -> str:
    _base_url = base_url or os.getenv("PROXMOX_BASE_URL")
    if not _base_url:
        raise ValueError("Base URL must be provided either as an argument or via the 'PROXMOX_BASE_URL' environment variable.")
    return _base_url

