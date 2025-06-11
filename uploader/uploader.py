import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv() # Loads environment variables

class RepositoryUploader:
    def __init__(self, username):
        self.username = username
        self.api_base_url = 'https://api.github.com'
        self.access_token = os.getenv('TOKEN_GITHUB')
        if not self.access_token:
            # Clear error message if token is not found
            raise ValueError(" ERROR: 'TOKEN_GITHUB' environment variable not set. Please define it before running (e.g., export TOKEN_GITHUB='YOUR_TOKEN_HERE').")
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        print(f"   [Uploader]: Repository handler initialized for GitHub user: '{self.username}'.") # Visual Effect

    def create_repository(self, repo_name):
        """
        Attempts to create a new repository on GitHub.
        Provides detailed feedback on the operation's success or failure.
        """
        data = {
            'name': repo_name,
            'description': 'Repository language data for selected companies (generated via Python automation).',
            'private': False # Public repository
        }
        url = f'{self.api_base_url}/user/repos'
        
        print(f"   [Uploader]: Attempting to create repository '{repo_name}' for '{self.username}' on GitHub...")
        try:
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status() # Raises an HTTPError for 4xx or 5xx responses
            
            if response.status_code == 201:
                print(f"  [Uploader]: Repository '{repo_name}' successfully created! URL: {response.json().get('html_url')}")
                return response.json() # Returns the complete API response
            else:
                # In case a 2xx status other than 201 is returned (unlikely for creation)
                print(f"  [Uploader]: Unexpected response when creating repository '{repo_name}': Status {response.status_code}. Details: {response.text}")
                return None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 422 and "name already exists" in e.response.text:
                print(f"  [Uploader]: Repository '{repo_name}' already exists for '{self.username}'. No action needed, continuing.")
                return {'message': 'Repository already exists'} # Returns a message to indicate it already exists
            else:
                print(f"  [Uploader]: HTTP error creating repository '{repo_name}': Status {e.response.status_code} - {e.response.text}")
                print(f"     Error response details: {e.response.json()}") # Helps debug API errors
                return None
        except requests.exceptions.ConnectionError as e:
            print(f"  [Uploader]: Connection error when trying to create '{repo_name}': {e}. Check your internet connection.")
            return None
        except Exception as e:
            print(f"  [Uploader]: An unexpected error occurred when creating '{repo_name}': {e}") 
            return None

    def upload_file(self, repo_name, file_name, file_path):
        """
        Adds or updates a file in an existing GitHub repository.
        Includes detailed messages for each step of the process.
        """
        print(f"\n  [Uploader]: Preparing to upload file '{file_name}' to repository '{repo_name}'...") # Visual Effect
        
        if not os.path.exists(file_path):
            print(f"  [Uploader]: ERROR: Local file not found at '{file_path}'. Skipping upload of '{file_name}'.")
            return False

        try:
            with open(file_path, "rb") as file:
                file_content = file.read()
            # The .decode("utf-8") is crucial for Base64, as the API expects a string
            encoded_file = base64.b64encode(file_content).decode("utf-8") 
            print(f"    [Uploader]: File '{file_name}' successfully read and Base64 encoded.")
        except Exception as e:
            print(f"  [Uploader]: ERROR: Could not read or encode file '{file_path}': {e}. Skipping upload.")
            return False

        url = f'{self.api_base_url}/repos/{self.username}/{repo_name}/contents/{file_name}'
        
        # Logic to check file SHA (necessary for updates)
        sha = None
        try:
            print(f"    [Uploader]: Checking if file '{file_name}' already exists in the repository...")
            get_response = requests.get(url, headers=self.headers)
            if get_response.status_code == 200:
                sha = get_response.json().get('sha')
                print(f"    [Uploader]: File '{file_name}' already exists. It will be updated (SHA: {sha[:7]}...).") # Shows only a snippet of the SHA
            elif get_response.status_code == 404:
                print(f"    [Uploader]: File '{file_name}' not found. It will be created as a new file.")
            else:
                print(f"     [Uploader]: Warning: Could not verify status of file '{file_name}' (Status {get_response.status_code}). Attempting to create/update.")
        except requests.exceptions.RequestException as e:
            print(f"     [Uploader]: Warning: Error checking for existence of file '{file_name}': {e}. Proceeding with create/update attempt without SHA.")

        data = {
            'message': f'Automated upload via Python pipeline: {file_name}',
            'content': encoded_file
        }
        if sha:
            data['sha'] = sha # Adds the SHA to update the existing file

        print(f"     [Uploader]: Sending PUT request to GitHub for '{file_name}'...")
        try:
            response = requests.put(url, json=data, headers=self.headers)
            response.raise_for_status()

            if response.status_code in [200, 201]: # 200 for update, 201 for creation
                action = "created" if response.status_code == 201 else "updated"
                print(f"   [Uploader]: File '{file_name}' {action} successfully in repository '{repo_name}'. URL: {response.json().get('content', {}).get('html_url')}")
                return True
            else:
                print(f"   [Uploader]: Unexpected response when uploading '{file_name}': Status {response.status_code}. Details: {response.text}")
                return False
        except requests.exceptions.HTTPError as e:
            print(f"   [Uploader]: HTTP ERROR uploading file '{file_name}': Status {e.response.status_code} - {e.response.text}")
            print(f"     Error response details: {e.response.json()}")
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"   [Uploader]: Connection ERROR when trying to upload '{file_name}': {e}. Check your internet connection.")
            return False
        except Exception as e:
            print(f"   [Uploader]: An unexpected error occurred when uploading '{file_name}': {e}")
            return False