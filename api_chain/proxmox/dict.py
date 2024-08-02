import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve the tokens from environment variables
proxmox_HCM_api_token = os.getenv('PROXMOX_HCM_API_TOKEN')
node5_api_token = os.getenv('NODE_5_API_TOKEN')

# Define the Proxmox nodes with their base URLs and API tokens
proxmox_nodes = {
    "proxmoxHCM": {
        "base_url": "https://ns31418912.ip-54-38-37.eu:8006",
        "api_token": proxmox_HCM_api_token
    },
    "node5": {
        "base_url": "https://ns31212248.ip-51-178-74.eu:8006",
        "api_token": node5_api_token
    }
}
