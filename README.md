# GitHub Data Pipeline
This project automates the extraction of repository language data from GitHub organizations, processes it, and uploads the results to a designated GitHub repository. It's built with modular components for extraction, transformation, and uploading.

---

## main.py (Orchestrator) ⚙️

Serves as the main entry point, orchestrating the entire data pipeline: environment setup, ETL, and upload logic.

```python
# main.py
import os
import time
from etl.extractor import RepositoryData
from uploader.uploader import RepositoryUploader
from dotenv import load_dotenv

load_dotenv()

MY_GITHUB_USERNAME = 'FireFox-exe'
TARGET_REPO_NAME = 'company-repositories-languages'
USERS_TO_PROCESS = ['amzn', 'netflix', 'spotify']

if not os.path.exists('data'):
    os.makedirs('data')
    print(" [Main]: 'data/' directory created to store extracted CSV files.")
```

**Explanation**: Loads environment variables, defines config variables (GitHub user, repo, targets), and ensures the `data/` directory exists for file storage.

---

```python
# Uploader Initialization
uploader = None
try:
    uploader = RepositoryUploader(MY_GITHUB_USERNAME)
    uploader.create_repository(TARGET_REPO_NAME)
except ValueError as e:
    print(f" [Main]: FATAL ERROR during Uploader initialization: {e}")
    exit(1)
except Exception as e:
    print(f" [Main]: UNEXPECTED ERROR initializing Uploader or creating repository: {e}")
    exit(1)
```

**Explanation**: Creates a `RepositoryUploader` and attempts to create a GitHub repo. Fails fast if `TOKEN_GITHUB` is missing or API fails.

---

```python
# ETL Process
for user in USERS_TO_PROCESS:
    try:
        extractor = RepositoryData(user)
        languages_df = extractor.create_languages_df()
        local_file_path = f'data/languages_{user}.csv'

        if not languages_df.empty:
            languages_df.to_csv(local_file_path, index=False)
            if uploader:
                uploader.upload_file(TARGET_REPO_NAME, os.path.basename(local_file_path), local_file_path)
```

**Explanation**: Loops through each user/org, extracts data using `RepositoryData`, saves to CSV, and uploads if the file isn’t empty. Skips errors gracefully.

---

## etl/extractor.py 🔎✨

Handles GitHub API interaction and transformation to `pandas.DataFrame`.

```python
class RepositoryData:
    def __init__(self, owner):
        self.owner = owner
        self.api_base_url = 'https://api.github.com'
        self.access_token = os.getenv('TOKEN_GITHUB')
        if not self.access_token:
            raise ValueError("ERROR: 'TOKEN_GITHUB' not set.")
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-GitHub-Api-Version': '2022-11-28'
        }
```

**Explanation**: Initializes the GitHub data fetcher. Checks the token. Prepares headers. Critical to secure and authenticated GitHub access.

---

```python
    def list_all_repositories(self):
        if self._all_repos is not None:
            return self._all_repos

        repositories = []
        page = 1
        per_page = 100

        while True:
            url = f'{self.api_base_url}/users/{self.owner}/repos'
            response = requests.get(url, headers=self.headers, params={'page': page, 'per_page': per_page})
            response.raise_for_status()

            page_repos = response.json()
            if not page_repos:
                break

            repositories.extend(page_repos)
            page += 1
            time.sleep(0.5)
```

**Explanation**: Paginates through all user repos (up to 100 per call). Reusable in any GitHub repo extractor. Uses 0.5s delay to respect API.

---

```python
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403 and int(e.response.headers.get('X-RateLimit-Remaining', 1)) == 0:
                    reset_time = int(e.response.headers['X-RateLimit-Reset'])
                    sleep_for = max(0, reset_time - time.time()) + 1
                    time.sleep(sleep_for)
                    continue
```

**Explanation**: GitHub Rate Limit handler. Automatically sleeps and retries the current page if the quota is exceeded. Essential for large-scale fetches.

---

```python
    def create_languages_df(self):
        repos = self.list_all_repositories()
        names = [repo.get('name') for repo in repos if repo.get('name')]
        langs = [repo.get('language') for repo in repos]
        return pd.DataFrame({
            'repository_name': names,
            'language': langs
        })
```

**Explanation**: Converts raw JSON repo data into a `DataFrame` of name + language. Filters out missing names. Lightweight and reusable.

---

## uploader/uploader.py 📄🔗

Responsible for creating a GitHub repository and uploading files to it.

```python
class RepositoryUploader:
    def __init__(self, username):
        self.username = username
        self.api_base_url = 'https://api.github.com'
        self.access_token = os.getenv('TOKEN_GITHUB')
        if not self.access_token:
            raise ValueError("ERROR: 'TOKEN_GITHUB' not set.")
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-GitHub-Api-Version': '2022-11-28'
        }
```

**Explanation**: Sets up all credentials and headers for upload. Reusable base for GitHub-related actions.

---

```python
    def create_repository(self, repo_name):
        url = f'{self.api_base_url}/user/repos'
        data = {
            'name': repo_name,
            'description': 'Language data from automated pipeline.',
            'private': False
        }
        response = requests.post(url, json=data, headers=self.headers)
        if response.status_code == 201:
            return response.json()
        elif response.status_code == 422:
            print(f"Repository '{repo_name}' already exists.")
```

**Explanation**: Attempts to create a repo. If it already exists, continues gracefully. Returns useful metadata.

---

```python
    def upload_file(self, repo_name, file_name, file_path):
        with open(file_path, "rb") as file:
            file_content = file.read()
        encoded_file = base64.b64encode(file_content).decode("utf-8")

        url = f'{self.api_base_url}/repos/{self.username}/{repo_name}/contents/{file_name}'

        sha = None
        get_response = requests.get(url, headers=self.headers)
        if get_response.status_code == 200:
            sha = get_response.json().get('sha')

        data = {
            'message': f'Upload: {file_name}',
            'content': encoded_file
        }
        if sha:
            data['sha'] = sha

        response = requests.put(url, json=data, headers=self.headers)
```

**Explanation**: Uploads or updates a file depending on whether it already exists. Uses SHA to avoid duplication issues. Base64 is required by GitHub API.

---

**Reusability :**

* `list_all_repositories()`: GitHub pagination + caching
* `create_languages_df()`: Quick DataFrame from JSON
* `upload_file()`: Upload/update file with Base64 + SHA
* Token + error handling: robust, scalable, clear
* Rate limit handling: production-ready safety net
