import os
import requests
from requests.auth import HTTPBasicAuth
import getpass

# Step 1: Basic Authentication with Nginx
def authenticate_with_nginx(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("Authenticated with Nginx.")
            return True
        else:
            print(f"Failed to authenticate with Nginx: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request to Nginx failed: {e}")
        return False

# Step 2: Retrieve Vault Token
def get_vault_token():
    return getpass.getpass("Vault token: ").strip()

# Step 3: Access Vault Secret
def access_vault_secret(vault_token, url):
    headers = {
        'X-Vault-Token': vault_token
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            secret = response.json()
            print("Accessed Vault secret.")
            return secret['data']['data']['oumaima-token']
        else:
            print(f"Failed to access Vault secret: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request to Vault failed: {e}")
        return None

# Main logic
if __name__ == "__main__":
    # Get credentials from environment variables or prompt the user
    nginx_username = os.getenv('NGINX_USERNAME') or input("Nginx username: ")
    nginx_password = os.getenv('NGINX_PASSWORD') or getpass.getpass("Nginx password: ")
    vault_token = os.getenv('VAULT_TOKEN') or get_vault_token()

    # Save credentials and token in environment variables if not already set
    os.environ['NGINX_USERNAME'] = nginx_username
    os.environ['NGINX_PASSWORD'] = nginx_password
    os.environ['VAULT_TOKEN'] = vault_token

    # Form the URL with basic auth credentials
    base_url = f"http://{nginx_username}:{nginx_password}@46.105.247.55:8200"

    # Authenticate with Nginx
    if authenticate_with_nginx(f"{base_url}/v1/sys/health"):
        # Access Vault secret
        api_token = access_vault_secret(vault_token, f"{base_url}/v1/kv/data/users/accounts/api-tokens/proxmox?version=2")
        if api_token:
            print(f"API Token: {api_token}")
            # Save the retrieved API token in an environment variable
            os.environ['API_TOKEN'] = api_token
        else:
            print("Failed to retrieve API token.")
