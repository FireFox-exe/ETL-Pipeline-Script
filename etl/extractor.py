import os
import requests
import pandas as pd
import time
from dotenv import load_dotenv

load_dotenv() # Loads environment variables

class RepositoryData:
    def __init__(self, owner):
        self.owner = owner # Company Repository
        self.api_base_url = 'https://api.github.com'
        self.access_token = os.getenv('TOKEN_GITHUB')
        if not self.access_token:
            # Clear error message if token is not found
            raise ValueError(" ERROR: 'TOKEN_GITHUB' environment variable not set. Please define it before running (e.g., export TOKEN_GITHUB='YOUR_TOKEN_HERE').")
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        self._all_repos = None # Cache for optimization
        print(f"   [Extractor]: Data collector initialized for GitHub user: '{self.owner}'.")

    def list_all_repositories(self):
        """
        Fetches all repositories for a GitHub user,
        handling pagination dynamically and addressing rate limiting.
        Returns a flat list of repository dictionaries.
        Uses caching to avoid repeated requests.
        """
        if self._all_repos is not None:
            print(f"   [Extractor]: Returning repositories for '{self.owner}' from cache (to avoid repeated requests).") # Visual Effect
            return self._all_repos

        repositories = []
        page = 1
        per_page = 100 # Maximum allowed by GitHub API

        print(f"   [Extractor]: Starting API repository fetch for '{self.owner}' (cache empty, first fetch)...") # Visual Effect

        while True:
            params = {'page': page, 'per_page': per_page}
            url = f'{self.api_base_url}/users/{self.owner}/repos'
            print(f'     [Extractor]: Fetching page {page} of repositories...') # Visual Effect

            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status() # Raises an HTTPError for 4xx or 5xx responses

                if response.status_code == 200:
                    page_repos = response.json() # transform response to json()
                    if not page_repos:
                        print(f'     [Extractor]: Page {page} returned empty. End of pagination for {self.owner}.')
                        break
                    
                    repositories.extend(page_repos) # flat repositories(response.json)
                    print(f'     [Extractor]: Page {page} successfully downloaded. Total repositories for {self.owner}: {len(repositories)}') 
                    page += 1
                    time.sleep(0.5) # Small delay to be courteous to the API

            # if rate limit error
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403 and 'X-RateLimit-Remaining' in e.response.headers and int(e.response.headers['X-RateLimit-Remaining']) == 0:
                    reset_time = int(e.response.headers['X-RateLimit-Reset'])
                    sleep_for = max(0, reset_time - time.time()) + 1 # +1 second for safety
                    print(f'     [Extractor]: GitHub rate limit exceeded. Waiting for {sleep_for:.0f} seconds before retrying...')
                    time.sleep(sleep_for)
                    continue # Retries the same page after waiting
                else:
                    print(f'     [Extractor]: HTTP error fetching page {page} for {self.owner}: Status {e.response.status_code} - {e.response.text}')
                    print(f"       Error response details: {e.response.json()}")
                    break # Stops pagination on other errors
            except requests.exceptions.ConnectionError as e:
                print(f'     [Extractor]: Connection error accessing page {page} for {self.owner}: {e}. Check your internet connection.')
                break # Stops pagination on network error
            except Exception as e:
                print(f'     [Extractor]: An unexpected error occurred while fetching page {page}: {e}')
                break # Stops pagination on generic error
        
        self._all_repos = repositories # Stores the result in cache
        return self._all_repos
    
    def extract_repo_names(self, repos):
        print(f"   [Extractor]: Extracting repository names...") # Visual effect
        names = []
        for repo in repos:
            name = repo.get('name')
            if name:
                names.append(name)
            else:
                print(f"     [Extractor]: Repository found without 'name' key: {repo}. Skipping.")
        return names

    def extract_languages(self, repos):
        print(f"   [Extractor]: Extracting main languages from repositories...")  # Visual effect
        languages = []
        for repo in repos:
            lang = repo.get('language') # .get() to avoid KeyError
            languages.append(lang)
            if lang is None:
                print(f"     [Extractor]: Repository '{repo.get('name', 'N/A')}' did not specify a main language. Adding 'None'.")
        return languages

    def create_languages_df(self):
        """
        Fetches all repositories (using cache or API),
        extracts names and languages, and creates a DataFrame.
        """
        print(f"   [Extractor]: Creating languages DataFrame for '{self.owner}'...") # Company Repository
        repos = self.list_all_repositories() 
        
        if not repos:
            print(f"   [Extractor]: No repositories found for '{self.owner}'. DataFrame will be empty.")
            return pd.DataFrame({'repository_name': [], 'language': []})

        names = self.extract_repo_names(repos) 
        langs = self.extract_languages(repos) 

        df = pd.DataFrame({
            'repository_name': names,
            'language': langs
        })

        print(f"   [Extractor]: DataFrame for '{self.owner}' created with {len(df)} rows.") 
        return df