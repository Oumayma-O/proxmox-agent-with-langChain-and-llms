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


