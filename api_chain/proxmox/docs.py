from typing import Dict, Any
import json

_proxmox_api_docs: Dict[str, Any] = {}

proxmox_api_docs = json.dumps(_proxmox_api_docs, indent=2)